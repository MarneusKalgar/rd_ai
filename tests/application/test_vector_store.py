"""Independent vector arithmetic and mandatory-filter boundary checks."""

import json

import httpx
import pytest

from extraction_service.retrieval.vector_store import QdrantStore, checked_vector, cosine


def test_independent_cosine() -> None:
    left = [1.0, 0.0] + [0.0] * 382
    right = [0.0, 1.0] + [0.0] * 382

    assert cosine(left, left) == 1
    assert cosine(left, right) == 0
    assert cosine(left, [-value for value in left]) == -1


@pytest.mark.parametrize(
    "value",
    [[], [0.0] * 384, [float("nan")] * 384, [float("inf")] * 384, [True] * 384, ["1"] * 384],
)
def test_invalid_vectors(value: object) -> None:
    with pytest.raises(ValueError, match="Vector|vector"):
        checked_vector(value)


def test_scope_filters_are_in_physical_query() -> None:
    requests: list[httpx.Request] = []

    def handle(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return httpx.Response(200, json={"status": "ok", "result": {"points": []}})

    with httpx.Client(base_url="http://store/", transport=httpx.MockTransport(handle)) as client:
        store = QdrantStore(client)
        result = store.query("fixture", [1.0] + [0.0] * 383, scope="A", snapshot="current")
        with pytest.raises(ValueError, match="authority"):
            store.query("fixture", [1.0] + [0.0] * 383, scope="", snapshot="current")

    assert result == []
    assert len(requests) == 1
    body = json.loads(requests[0].content)
    assert body["filter"]["must"] == [
        {"key": "scope", "match": {"any": ["shared", "A"]}},
        {"key": "snapshot", "match": {"value": "current"}},
        {"key": "eligible", "match": {"value": True}},
    ]
    assert body["params"] == {"exact": True}
    assert body["with_payload"] is False


def test_transport_failure_is_not_retried() -> None:
    calls = 0

    def handle(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        return httpx.Response(503)

    with httpx.Client(base_url="http://store/", transport=httpx.MockTransport(handle)) as client:
        store = QdrantStore(client)
        with pytest.raises(httpx.HTTPStatusError):
            store.query("fixture", [1.0] + [0.0] * 383, scope="A", snapshot="current")

    assert calls == 1
