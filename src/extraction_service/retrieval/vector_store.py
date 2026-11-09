"""Bounded direct Qdrant REST integration; application retains source authority."""

import math
import time
from typing import Any

import httpx

DIMENSIONS = 384
MAX_POINTS = 64


def checked_vector(value: object) -> list[float]:
    """Reject missing, nonfinite, zero or incorrectly dimensioned vectors."""

    if not isinstance(value, list) or len(value) != DIMENSIONS:
        raise ValueError("Vector dimension mismatch")
    result: list[float] = []
    for item in value:
        if isinstance(item, bool) or not isinstance(item, (int, float)) or not math.isfinite(item):
            raise ValueError("Vector values must be finite numbers")
        result.append(float(item))
    if sum(item * item for item in result) <= 0:
        raise ValueError("Zero vector is invalid")
    return result


def cosine(left: list[float], right: list[float]) -> float:
    """Independent exact cosine oracle, without database or encoder imports."""

    a = checked_vector(left)
    b = checked_vector(right)
    numerator = sum(x * y for x, y in zip(a, b, strict=True))
    denominator = math.sqrt(sum(x * x for x in a) * sum(y * y for y in b))
    return numerator / denominator


class QdrantStore:
    """Borrow one HTTP client; enforce request ceilings and mandatory scope filters.

    Application setup owns client cleanup. This adapter never reads source text,
    expected answers, model files or accounting state.
    """

    def __init__(
        self, client: httpx.Client, *, call_limit: int = 400, deadline_seconds: float = 900
    ) -> None:
        self.client = client
        self.call_limit = call_limit
        self.deadline = time.monotonic() + deadline_seconds
        self.calls = 0

    def request(self, method: str, path: str, body: object = None) -> Any:
        """One physical REST request, without retries or fallback."""

        remaining = self.deadline - time.monotonic()
        if self.calls >= self.call_limit or remaining <= 0:
            raise ValueError("Vector-store invocation limit exceeded")
        self.calls += 1
        response = self.client.request(method, path, json=body, timeout=min(5, remaining))
        response.raise_for_status()
        value = response.json()
        if not isinstance(value, dict) or value.get("status") != "ok":
            raise ValueError("Invalid Qdrant response")
        return value.get("result")

    def create(self, collection: str) -> None:
        """Create a new exact-search collection; existing names must fail."""

        self.request(
            "PUT",
            f"collections/{collection}",
            {
                "vectors": {"size": DIMENSIONS, "distance": "Cosine"},
                "hnsw_config": {"m": 0},
                "optimizers_config": {"indexing_threshold": 0},
            },
        )

    def upsert(self, collection: str, points: list[dict[str, Any]]) -> None:
        """Insert bounded vectors with metadata, never trusting it as source truth."""

        if not points or len(points) > MAX_POINTS:
            raise ValueError("Point batch limit exceeded")
        for point in points:
            checked_vector(point.get("vector"))
        self.request("PUT", f"collections/{collection}/points?wait=true", {"points": points})

    def query(
        self, collection: str, vector: list[float], *, scope: str, snapshot: str
    ) -> list[dict[str, Any]]:
        """Search only the authorized current snapshot, without payload-text output.

        Fetch the bounded eligible population to make exact-search tie ordering
        reproducible in the application. This is not an ANN performance exercise.
        """

        if scope not in ("A", "B") or not snapshot:
            raise ValueError("Invalid vector query authority")
        result = self.request(
            "POST",
            f"collections/{collection}/points/query",
            {
                "query": checked_vector(vector),
                "params": {"exact": True},
                "limit": MAX_POINTS,
                "with_payload": False,
                "with_vector": False,
                "filter": {
                    "must": [
                        {"key": "scope", "match": {"any": ["shared", scope]}},
                        {"key": "snapshot", "match": {"value": snapshot}},
                        {"key": "eligible", "match": {"value": True}},
                    ]
                },
            },
        )
        if not isinstance(result, dict) or not isinstance(result.get("points"), list):
            raise ValueError("Invalid Qdrant query result")
        points: list[dict[str, Any]] = result["points"]
        if len(points) > MAX_POINTS:
            raise ValueError("Oversized vector query result")
        identifiers: set[int] = set()
        for point in points:
            identifier = point.get("id")
            score = point.get("score")
            if (
                type(identifier) is not int
                or identifier in identifiers
                or not isinstance(score, (int, float))
                or not math.isfinite(score)
            ):
                raise ValueError("Invalid or duplicate vector result")
            identifiers.add(identifier)
        return points

    def delete_points(self, collection: str, identifiers: list[int]) -> None:
        """Delete selected point IDs and wait for acknowledged completion."""

        if not identifiers or len(identifiers) > MAX_POINTS:
            raise ValueError("Deletion batch limit exceeded")
        self.request(
            "POST", f"collections/{collection}/points/delete?wait=true", {"points": identifiers}
        )
