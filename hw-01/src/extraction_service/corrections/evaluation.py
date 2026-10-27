"""Offline retained-output quality and explicit replay/correction timing populations."""

from collections import Counter
from pathlib import Path
from typing import Any

from extraction_service.application.persistence import reload_records
from extraction_service.corpus.loading import load_corpus
from extraction_service.corrections.storage import verify_corrections
from extraction_service.evaluation.scoring import ExtractionScore, combine_scores, score_extraction


def _quality(scores: list[ExtractionScore], input_ids: list[str]) -> dict[str, Any]:
    combined = combine_scores([score.overall for score in scores])
    counts = combined.model_dump()
    return {
        "gold_cases": len(scores),
        "schema_valid": sum(score.schema_valid for score in scores),
        "exact_documents": sum(score.exact for score in scores),
        "extra_lines": sum(score.extra_lines for score in scores),
        "missing_lines": sum(score.missing_lines for score in scores),
        "overall": {**counts, "accuracy": combined.accuracy},
        "cases": [
            {"input_id": input_id, "score": score.model_dump()}
            for input_id, score in zip(input_ids, scores, strict=True)
        ],
    }


def evaluate_corrections(project: Path, directory: Path, base_dir: Path) -> dict[str, Any]:
    """Read gold only here; acceptance and generation never use evaluator judgments."""

    header, cases = verify_corrections(directory, base_dir)
    _, records = reload_records(base_dir)
    corpus = load_corpus(project)
    if {record.input_id for record in records} != set(corpus.gold):
        raise ValueError("Correction evaluation requires exact current gold membership")
    sources = {source.input_id: source for source in corpus.inputs}
    baseline_scores = []
    retained_scores = []
    identifiers: Counter[str] = Counter()
    for record, case in zip(records, cases, strict=True):
        if record.input_sha256 != sources[record.input_id].input_sha256:
            raise ValueError("Correction evaluation input differs from current corpus")
        expected = corpus.gold[record.input_id]
        baseline_scores.append(score_extraction(expected, case.prior, corpus.contract))
        retained_scores.append(score_extraction(expected, case.retained, corpus.contract))
        for finding in case.after.get("findings", []):
            if finding["output_path"].endswith("/buyerProductIdentifier"):
                identifiers[finding["status"]] += 1
    attempts = [case.attempt for case in cases if case.attempt is not None]
    baseline_seconds = sum(record.duration_ms for record in records) / 1000
    correction_seconds = sum(case.duration_ms for case in cases) / 1000
    return {
        "version": "buyer-id-correction-evaluation-v1",
        "run_id": header["run_id"],
        "base_run_id": header["base_run_id"],
        "policy": header["policy"],
        "new_primaries": 0,
        "reused_primary_requests": sum(len(record.attempts) for record in records),
        "new_physical_requests": len(attempts),
        "decisions": dict(Counter(case.decision.value for case in cases)),
        "baseline": _quality(baseline_scores, [record.input_id for record in records]),
        "retained_pipeline": _quality(retained_scores, [record.input_id for record in records]),
        "identifier_findings_after": dict(identifiers),
        "baseline_processing_seconds": baseline_seconds,
        "new_correction_processing_seconds": correction_seconds,
        "reconstructed_processing_seconds": baseline_seconds + correction_seconds,
        "correction_phase_wall_seconds": header["phase_wall_seconds"],
        "live_end_to_end_measured": False,
        "api_cost_usd": "0",
        "whole_po_certified": False,
        "disclosure": (
            "Saved primaries plus actual new correction requests; source-only policy chooses "
            "retained whole objects. Gold10 is development data; retained for review is not "
            "automatic PO acceptance."
        ),
    }
