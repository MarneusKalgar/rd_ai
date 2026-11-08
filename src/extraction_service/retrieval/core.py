"""Bounded reference snapshots and eligible-partition BM25 retrieval."""

import hashlib
import json
import math
import re
from collections import Counter
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

MAX_SOURCE_BYTES = 65536
MAX_CONTEXT_BYTES = 12288
MAX_ARTIFACT_BYTES = 32 * 1024 * 1024


def digest(data: bytes) -> str:
    """Identify exact original bytes."""

    return hashlib.sha256(data).hexdigest()


def canonical(value: object) -> bytes:
    """Serialize a portable deterministic artifact."""

    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()


def read_confined(root: Path, relative: str, limit: int) -> bytes:
    """Read bounded regular files without path escape or symlink traversal."""

    path = Path(relative)
    if path.is_absolute() or ".." in path.parts:
        raise ValueError("Invalid reference path")
    current = root
    for part in path.parts:
        current = current / part
        if current.is_symlink():
            raise ValueError("Symlink reference forbidden")
    if not current.is_file():
        raise ValueError("Reference must be a regular file")
    with current.open("rb") as stream:
        data = stream.read(limit + 1)
    if len(data) > limit:
        raise ValueError("Artifact size limit exceeded")
    return data


class StrictModel(BaseModel):
    """Reject unknown or coerced protocol fields."""

    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)


class Reference(StrictModel):
    """Trusted catalog metadata; text cannot modify authority."""

    id: str
    revision: str
    path: str
    sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    topic: str
    scope: Literal["shared", "A", "B"]
    authority: Literal["schema-derived", "synthetic"]
    provenance: str
    status: Literal["active", "deleted", "revoked"] = "active"
    effective_from: int = Field(ge=0)
    effective_until: int | None = None
    exclusive_key: str

    @model_validator(mode="after")
    def check_interval(self) -> Reference:
        """Reject impossible effective intervals."""

        if self.effective_until is not None and self.effective_until <= self.effective_from:
            raise ValueError("Invalid effective interval")
        return self


class Catalog(StrictModel):
    """One immutable fixture snapshot."""

    version: Literal[1]
    references: list[Reference] = Field(min_length=1, max_length=64)

    @model_validator(mode="after")
    def check_ids(self) -> Catalog:
        """Prevent ambiguous duplicate chunk identities."""

        keys = [(item.id, item.revision) for item in self.references]
        if len(set(keys)) != len(keys):
            raise ValueError("Duplicate reference identity")
        return self


class Chunk(StrictModel):
    """One complete rule with original UTF-8 byte coordinates."""

    reference: Reference
    text: str
    start: Literal[0] = 0
    end: int


class Snapshot(StrictModel):
    """Manifest-bound source material, not an authorization cache."""

    catalog_sha256: str
    chunks: list[Chunk]
    chunker: Literal["whole-rule-v1"] = "whole-rule-v1"


def build_snapshot(root: Path, catalog_path: str) -> Snapshot:
    """Validate every source and construct an immutable rule index."""

    raw = read_confined(root, catalog_path, MAX_ARTIFACT_BYTES)
    catalog = Catalog.model_validate_json(raw)
    chunks: list[Chunk] = []
    total = 0
    for reference in catalog.references:
        if not reference.path.startswith("data/references/"):
            raise ValueError("Source outside explicit reference collection")
        data = read_confined(root, reference.path, MAX_SOURCE_BYTES)
        if digest(data) != reference.sha256:
            raise ValueError("Reference hash mismatch")
        total += len(data)
        if total > 4 * 1024 * 1024:
            raise ValueError("Reference collection size limit exceeded")
        chunks.append(Chunk(reference=reference, text=data.decode("utf-8"), end=len(data)))
    return Snapshot(catalog_sha256=digest(raw), chunks=chunks)


def tokens(text: str) -> list[str]:
    """Unicode alphanumeric terms, case-folded, without stemming."""

    return re.findall(r"[^\W_]+", text.casefold(), flags=re.UNICODE)


def bm25(query: str, documents: list[str]) -> list[float]:
    """Score using eligible documents only and positive smoothed IDF."""

    counts = [Counter(tokens(text)) for text in documents]
    lengths = [sum(count.values()) for count in counts]
    average = sum(lengths) / len(lengths) if lengths else 0.0
    scores = [0.0] * len(documents)
    if not average:
        return scores
    for term in sorted(set(tokens(query))):
        frequency = sum(term in count for count in counts)
        idf = math.log(1 + (len(counts) - frequency + 0.5) / (frequency + 0.5))
        for index, count in enumerate(counts):
            tf = count[term]
            denominator = tf + 1.2 * (1 - 0.75 + 0.75 * lengths[index] / average)
            scores[index] += idf * tf * 2.2 / denominator
    return scores


class Hit(StrictModel):
    """Quoted evidence; similarity is not entailment."""

    source_id: str
    revision: str
    sha256: str
    start: int
    end: int
    quote: str
    score: float


class Evidence(StrictModel):
    """Separate operational response, never a PO output."""

    snapshot: str
    status: Literal["evidence_found", "insufficient_evidence", "conflicting_evidence"]
    hits: list[Hit]


def retrieve(
    root: Path,
    catalog_path: str,
    snapshot: Snapshot,
    *,
    query: str,
    scope: str,
    effective_time: int,
    method: Literal["exact", "bm25"],
    topic: str | None = None,
) -> Evidence:
    """Revalidate current source authority before ranking or quoting.

    Scope is supplied by trusted application context, not inferred from query text.
    Replaying history requires an explicitly selected historical catalog.
    """

    if scope not in ("A", "B") or effective_time < 0:
        raise ValueError("Invalid trusted context")
    if method not in ("exact", "bm25"):
        raise ValueError("Invalid retrieval method")
    if len(query.encode()) > 4096:
        raise ValueError("Query size limit exceeded")
    current = build_snapshot(root, catalog_path)
    if current != snapshot:
        raise ValueError("Stale or modified snapshot")
    eligible = [
        chunk
        for chunk in current.chunks
        if chunk.reference.scope in ("shared", scope)
        and chunk.reference.status == "active"
        and chunk.reference.effective_from <= effective_time
        and (
            chunk.reference.effective_until is None
            or effective_time < chunk.reference.effective_until
        )
    ]
    if method == "exact":
        ranked = [(chunk, 1.0) for chunk in eligible if topic and chunk.reference.topic == topic]
    else:
        scores = bm25(query, [chunk.text for chunk in eligible])
        ranked = [
            (chunk, score) for chunk, score in zip(eligible, scores, strict=True) if score > 0
        ]
    ranked.sort(key=lambda item: (-item[1], item[0].reference.id, item[0].reference.revision))
    keys = Counter(chunk.reference.exclusive_key for chunk in eligible)
    conflict = any(keys[chunk.reference.exclusive_key] > 1 for chunk, _ in ranked)
    hits: list[Hit] = []
    seen: set[str] = set()
    for chunk, score in ranked:
        if chunk.reference.sha256 in seen:
            continue
        seen.add(chunk.reference.sha256)
        hits.append(
            Hit(
                source_id=chunk.reference.id,
                revision=chunk.reference.revision,
                sha256=chunk.reference.sha256,
                start=0,
                end=chunk.end,
                quote=chunk.text,
                score=score,
            )
        )
        if len(hits) == 3:
            break
    if sum(len(hit.quote.encode()) for hit in hits) > MAX_CONTEXT_BYTES:
        raise ValueError("Context size limit exceeded")
    status: Literal["evidence_found", "insufficient_evidence", "conflicting_evidence"]
    status = (
        "conflicting_evidence"
        if conflict
        else "evidence_found"
        if hits
        else "insufficient_evidence"
    )
    return Evidence(snapshot=digest(canonical(snapshot.model_dump())), status=status, hits=hits)


def validate_evidence(
    root: Path,
    catalog_path: str,
    snapshot: Snapshot,
    evidence: Evidence,
    *,
    query: str,
    scope: str,
    effective_time: int,
    method: Literal["exact", "bm25"],
    topic: str | None = None,
) -> None:
    """Reject forged quotes, identities, eligibility or ranking in saved responses."""

    expected = retrieve(
        root,
        catalog_path,
        snapshot,
        query=query,
        scope=scope,
        effective_time=effective_time,
        method=method,
        topic=topic,
    )
    if evidence != expected:
        raise ValueError("Evidence integrity mismatch")
