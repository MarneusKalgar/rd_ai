"""Score only assembled whole POs; retain failed stages and count both requests in operations."""

from pathlib import Path
from typing import Any

from extraction_service.application.persistence import reload_records
from extraction_service.corpus.loading import load_corpus
from extraction_service.evaluation.metrics import operational_metrics
from extraction_service.evaluation.scoring import combine_scores, score_extraction
from extraction_service.staged.contracts import SplitStage
from extraction_service.staged.storage import verify_split


def evaluate_split(project: Path, directory: Path, base_dir: Path) -> dict[str, Any]:
    """Read gold only for offline scoring; failed assembly earns no field matches."""

    header, cases, stages = verify_split(directory, base_dir)
    _, originals = reload_records(base_dir)
    corpus = load_corpus(project)
    if {case.input_id for case in cases} != set(corpus.gold):
        raise ValueError("Split evaluation requires exact current gold membership")
    source_hashes = {source.input_id: source.input_sha256 for source in corpus.inputs}
    if any(record.input_sha256 != source_hashes[record.input_id] for record in originals):
        raise ValueError("Split input differs from the current approved corpus")
    scores = [
        score_extraction(corpus.gold[c.input_id], c.extraction, corpus.contract) for c in cases
    ]
    fields = {name for score in scores for name in score.fields}
    quality = {
        "gold_cases": len(cases),
        "schema_valid": sum(score.schema_valid for score in scores),
        "exact_documents": sum(score.exact for score in scores),
        "extra_lines": sum(score.extra_lines for score in scores),
        "missing_lines": sum(score.missing_lines for score in scores),
        "per_field": {
            field: combine_scores([s.fields[field] for s in scores]).model_dump()
            for field in sorted(fields)
        },
        "cases": [
            {"input_id": case.input_id, "score": score.model_dump()}
            for case, score in zip(cases, scores, strict=True)
        ],
    }
    for name, population in (
        ("overall", [s.overall for s in scores]),
        ("headers", [s.headers for s in scores]),
        ("lines", [s.lines for s in scores]),
    ):
        combined = combine_scores(population)
        quality[name] = {**combined.model_dump(), "accuracy": combined.accuracy}
    return {
        "version": "header-lines-split-evaluation-v1",
        "run_id": header["run_id"],
        "base_run_id": header["base_run_id"],
        "policy": header["policy"],
        "quality": quality,
        "stage_operations": {
            stage.value: operational_metrics(stages[stage]) for stage in SplitStage
        },
        "stage_processing_seconds": {
            stage.value: sum(r.duration_ms for r in stages[stage]) / 1000 for stage in SplitStage
        },
        "processing_seconds": sum(case.duration_ms for case in cases) / 1000,
        "phase_wall_seconds": header["phase_wall_seconds"],
        "physical_requests": sum(len(r.attempts) for records in stages.values() for r in records),
        "new_primary_stage_jobs": 2 * len(cases),
        "assembled_documents": len(cases),
        "api_cost_usd": "0",
        "whole_po_certified": False,
        "note": (
            "Accuracy uses final whole POs; a failed stage gives a failed PO, while partial "
            "stage evidence stays visible. Gold10 is development data."
        ),
    }
