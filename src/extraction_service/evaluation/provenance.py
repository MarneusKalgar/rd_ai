"""A purpose-bound P02 protocol; no gold answers, generation or accounting setup."""

import json
from collections import Counter
from pathlib import Path
from typing import Any, Literal

from pydantic import Field

from extraction_service.application.persistence import item_key, reload_records
from extraction_service.archiving.archive import load_index
from extraction_service.archiving.bundles import verify_bundle
from extraction_service.archiving.files import canonical, confined, digest, read_json
from extraction_service.corpus.files import read_input
from extraction_service.corpus.manifests import load_manifests
from extraction_service.evaluation.protocol import Binding, Selection
from extraction_service.runtime_types import Identifier, StrictModel
from extraction_service.source_support import cells, field_labels, field_roles, provenance

MAX_RESULT_BYTES = 128 * 1024 * 1024


class ProvenanceProtocol(StrictModel):
    """Keep P02 independent of P01's fixed two-sided comparison constraints."""

    version: Literal["provenance-protocol-v1"]
    experiment_id: Literal["P02-E01"]
    source_revision: str
    authority: str
    archive: Binding
    corpus: Binding
    exposure: Binding
    rubric: Binding
    schema_binding: Binding = Field(alias="schema")
    controls: Binding
    plan: Binding
    selection: Selection
    input_ids: list[Identifier]
    fields: list[str]
    model_calls: Literal[0]
    generated_tokens: Literal[0]
    new_spend_usd: Literal["0"]
    output: str


def load_provenance_protocol(project: Path, filename: str) -> ProvenanceProtocol:
    """Verify metadata and explicit populations without reading approved gold objects."""

    protocol = ProvenanceProtocol.model_validate(read_json(confined(project, filename)))
    for binding in (
        protocol.archive,
        protocol.corpus,
        protocol.exposure,
        protocol.rubric,
        protocol.schema_binding,
        protocol.controls,
        protocol.plan,
    ):
        binding.verify(project)
    manifests = load_manifests(project / "data")
    ids = [case.input_id for case in manifests.corpus.cases]
    members = [name for run in protocol.selection.runs.values() for name in run.records]
    if (
        len(protocol.input_ids) != 30
        or len(set(protocol.input_ids)) != 30
        or set(protocol.input_ids) != set(ids)
        or len(members) != 30
        or set(members) != set(ids)
        or protocol.fields != list(provenance.FIELDS)
        or not protocol.output.startswith("results/submission/")
        or protocol.schema_binding.sha256 != manifests.gold.schema_sha256
    ):
        raise ValueError("P02 population, fields or contract differs")
    confined(project, protocol.output)
    return protocol


def assess_provenance(project: Path, filename: str, source: str) -> dict[str, Any]:
    """Verify archived records, then report all selected outcomes without inference."""

    protocol = load_provenance_protocol(project, filename)
    index = load_index(confined(project, protocol.archive.path))
    archived = {bundle.name: bundle for bundle in index.bundles}
    cases = {case.input_id: case for case in load_manifests(project / "data").corpus.cases}
    results = {}
    counts: Counter[str] = Counter()
    serialized = 0
    for run, expected in protocol.selection.runs.items():
        directory = confined(project, f"{source}/{run}")
        if (
            verify_bundle(directory) != archived.get(run)
            or digest(directory / "manifest.json") != expected.manifest_sha256
        ):
            raise ValueError("Run differs from pinned evidence")
        manifest, records = reload_records(directory)
        if manifest.experiment.execution.model_dump() != expected.original_execution:
            raise ValueError("Original execution differs")
        if len(records) != len(expected.records) or {r.input_id for r in records} != set(
            expected.records
        ):
            raise ValueError("Record population differs")
        for record in records:
            key = item_key(record.input_id, record.model_id, record.prompt_id, record.sampling_id)
            if manifest.record_sha256[key] != expected.records[record.input_id]:
                raise ValueError("Record hash differs")
            text = read_input(project / "data", cases[record.input_id])
            assessment = provenance.assess_fields(text, record.extraction)
            counts[assessment["status"]] += 1
            for finding in assessment["fields"]:
                counts["fields"] += 1
                counts[f"location:{finding['location']['status']}"] += 1
                counts[f"support:{finding['support_status']}"] += 1
                counts[f"linkage:{finding['linkage']}"] += 1
                counts["occurrence_references"] += len(finding["location"]["references"])
                counts["context_references"] += len(finding["context"])
            result = {
                "input_id": record.input_id,
                "run_id": run,
                "record_sha256": expected.records[record.input_id],
                "source_sha256": cases[record.input_id].input_sha256,
                "original_status": record.status.value,
                "assessment": assessment,
            }
            serialized += len(canonical(result))
            if serialized > MAX_RESULT_BYTES:
                raise ValueError("Provenance output resource limit exceeded")
            results[record.input_id] = result
    files = (
        Path(__file__),
        Path(provenance.__file__),
        Path(field_roles.__file__),
        Path(cells.__file__),
        Path(field_labels.__file__),
    )
    report = {
        "version": "provenance-report-v1",
        "protocol_sha256": digest(confined(project, filename)),
        "implementation": {path.name: digest(path) for path in files},
        "model_calls": 0,
        "generated_tokens": 0,
        "new_spend_usd": "0",
        "semantic_accuracy": None,
        "human_reviewed_anchors": 0,
        "counts": dict(sorted(counts.items())),
        "records": [results[name] for name in protocol.input_ids],
    }
    normalized: dict[str, Any] = json.loads(canonical(report))
    return normalized
