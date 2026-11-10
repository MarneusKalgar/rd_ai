"""Optional LangChain boundaries; no framework types enter application records."""

import importlib
import math
import os
from typing import Any

from extraction_service.retrieval.composition import capture, render_request
from extraction_service.retrieval.vector_store import MAX_POINTS, checked_vector


def check_tracing_disabled() -> None:
    """Refuse ambient tracing configuration before loading the trial libraries."""

    for name in ("LANGSMITH_TRACING", "LANGCHAIN_TRACING", "LANGCHAIN_TRACING_V2"):
        if os.environ.get(name, "false").lower() not in ("false", "0", ""):
            raise ValueError("Tracing must remain disabled for I01")
    if os.environ.get("LANGSMITH_API_KEY") or os.environ.get("LANGCHAIN_API_KEY"):
        raise ValueError("Tracing credentials must not enter I01")


def query_filter(scope: str, snapshot: str) -> Any:
    """Build required flat-payload filters without exposing caller-controlled metadata."""

    if scope not in ("A", "B") or not snapshot:
        raise ValueError("Invalid vector query authority")
    models = importlib.import_module("qdrant_client.models")
    return models.Filter(
        must=[
            models.FieldCondition(key="scope", match=models.MatchAny(any=["shared", scope])),
            models.FieldCondition(key="snapshot", match=models.MatchValue(value=snapshot)),
            models.FieldCondition(key="eligible", match=models.MatchValue(value=True)),
        ]
    )


def decode_documents(documents: list[Any], collection: str) -> list[dict[str, Any]]:
    """Extract locators only; payload strings never become source authority."""

    if len(documents) > MAX_POINTS:
        raise ValueError("Oversized vector query result")
    points: list[dict[str, Any]] = []
    seen: set[int] = set()
    for document, score in documents:
        metadata = document.metadata
        identifier = metadata.get("_id")
        if (
            metadata.get("_collection_name") != collection
            or type(identifier) is not int
            or identifier in seen
            or type(score) not in (int, float)
            or not math.isfinite(score)
        ):
            raise ValueError("Invalid LangChain document mapping")
        seen.add(identifier)
        points.append({"id": identifier, "score": float(score)})
    return points


class LangChainQueries:
    """Borrow a Qdrant client; only precomputed-vector exact queries are available."""

    def __init__(self, client: Any) -> None:
        check_tracing_disabled()
        self.client = client

    def query(
        self, collection: str, vector: list[float], *, scope: str, snapshot: str
    ) -> list[dict[str, Any]]:
        """Query the existing collection with explicit filters and no encoder object."""

        checked = checked_vector(vector)
        filtered = query_filter(scope, snapshot)
        integration = importlib.import_module("langchain_qdrant")
        models = importlib.import_module("qdrant_client.models")
        store = integration.QdrantVectorStore(
            client=self.client,
            collection_name=collection,
            embedding=None,
            distance=models.Distance.COSINE,
            vector_name="",
            content_payload_key="page_content",
            metadata_payload_key="metadata",
            validate_embeddings=False,
            validate_collection_config=False,
        )
        documents = store.similarity_search_with_score_by_vector(
            checked, k=MAX_POINTS, filter=filtered, search_params=models.SearchParams(exact=True)
        )
        return decode_documents(documents, collection)


def langchain_compose(job: dict[str, Any]) -> dict[str, Any]:
    """Compose the same application functions through LangChain without retries or models."""

    check_tracing_disabled()
    runnables = importlib.import_module("langchain_core.runnables")
    render = runnables.RunnableLambda(render_request)
    finish = runnables.RunnableLambda(lambda request: capture(job, request))
    pipeline = render | finish
    result: dict[str, Any] = pipeline.invoke(job, config={"callbacks": []})
    return result
