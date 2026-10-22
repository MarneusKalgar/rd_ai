"""Read-only aggregation of checked terminal run records under the frozen corpus."""

import hashlib
import json
from pathlib import Path
from typing import Any

from extraction_service.application.persistence import RunState, reload_records
from extraction_service.application.selection import RunOptions
from extraction_service.corpus.loading import load_corpus
from extraction_service.evaluation.metrics import operational_metrics
from extraction_service.evaluation.scoring import FieldScore, combine_scores, score_extraction
from extraction_service.records import RunRecord


def _counts(score: FieldScore) -> dict[str, Any]:
    return {
        **score.model_dump(),
        "accuracy": score.accuracy,
        "present_accuracy": None
        if not score.present_total
        else score.present_correct / score.present_total,
        "null_accuracy": None if not score.null_total else score.null_correct / score.null_total,
    }


def _variant(record: RunRecord, execution: dict[str, Any], setup: dict[str, Any]) -> dict[str, Any]:
    dependency = None if record.dependency is None else record.dependency.model_dump(mode="json")
    loaded = setup.get("loaded", {})
    context = {
        "context_length": setup.get("context_length", loaded.get("context_length")),
        "context_enforcement": setup.get("context_enforcement", "counted"),
        "tokenizer_sha256": setup.get("tokenizer_sha256"),
        "processor": setup.get("processor"),
        "pricing_stop": setup.get("pricing_stop"),
    }

    return {
        "stage": record.stage.value,
        "model_id": record.model_id,
        "model_name": record.model_name,
        "runtime": record.runtime.value,
        "dependency": dependency,
        "prompt_id": record.prompt_id,
        "prompt_sha256": record.prompt_sha256,
        "sampling": record.sampling.model_dump(),
        "schema_sha256": record.schema_sha256,
        "execution": execution,
        "context": context,
    }


def evaluate_runs(project_dir: Path, run_ids: list[str]) -> dict[str, Any]:
    """Evaluate saved terminal runs without inference or rewriting original evidence.

    Reject overlapping observations, current-corpus mismatches and unfinished
    checkpoint-only runs. Complete and stopped runs with terminal records are
    both supported; untouched labeled inputs receive zero field matches.
    """

    if not run_ids or len(run_ids) != len(set(run_ids)):
        raise ValueError("Evaluation requires unique run IDs")

    corpus = load_corpus(project_dir)
    sources = {source.input_id: source for source in corpus.inputs}
    grouped: dict[str, list[RunRecord]] = {}
    identities: dict[str, dict[str, Any]] = {}
    runs = []

    for run_id in run_ids:
        RunOptions(run_id=run_id)
        directory = project_dir / "results/runs" / run_id
        manifest, records = reload_records(directory)

        if manifest.state not in (RunState.COMPLETE, RunState.INCOMPLETE):
            raise ValueError("Evaluation requires terminal records for every selected job")

        runs.append(
            {
                "run_id": run_id,
                "state": manifest.state.value,
                "manifest_sha256": hashlib.sha256(
                    (directory / "manifest.json").read_bytes()
                ).hexdigest(),
                "experiment_sha256": sorted({record.experiment_sha256 for record in records}),
            }
        )

        for record in records:
            source = sources.get(record.input_id)

            if source is None or source.input_sha256 != record.input_sha256:
                raise ValueError("Evaluation input differs from the approved corpus")

            if record.schema_sha256 != corpus.contract.identity.sha256:
                raise ValueError("Evaluation schema differs from the approved corpus")

            descriptor = _variant(
                record,
                manifest.experiment.execution.model_dump(),
                manifest.setup.get(record.model_id, {}),
            )
            key = hashlib.sha256(json.dumps(descriptor, sort_keys=True).encode()).hexdigest()
            bucket = grouped.setdefault(key, [])

            if any(previous.input_id == record.input_id for previous in bucket):
                raise ValueError(
                    "Duplicate input observation for one variant; separate repetitions"
                )

            bucket.append(record)
            identities[key] = descriptor

    variants = []

    for key, records in grouped.items():
        cases = []
        scores = []
        fields: dict[str, list[FieldScore]] = {}

        for record in records:
            expected = corpus.gold.get(record.input_id)

            if expected is None:
                continue

            score = score_extraction(expected, record.extraction, corpus.contract)
            scores.append(score)

            for name, field in score.fields.items():
                fields.setdefault(name, []).append(field)

            cases.append(
                {
                    "input_id": record.input_id,
                    "status": record.status.value,
                    "score": score.model_dump(),
                }
            )

        observed = {record.input_id for record in records}
        variants.append(
            {
                "variant_id": key,
                "identity": identities[key],
                "run_ids": sorted({record.run_id for record in records}),
                "input_ids": [record.input_id for record in records],
                "operational": operational_metrics(records),
                "reported_models": sorted(
                    {
                        attempt.response.reported_model
                        for record in records
                        for attempt in record.attempts
                        if attempt.response is not None
                    }
                ),
                "quality": {
                    "gold_cases": len(scores),
                    "approved_gold_cases": len(corpus.gold),
                    "missing_gold_inputs": sorted(set(corpus.gold) - observed),
                    "exact_documents": sum(score.exact for score in scores),
                    "exact_document_rate": None
                    if not scores
                    else sum(score.exact for score in scores) / len(scores),
                    "overall": _counts(combine_scores([score.overall for score in scores])),
                    "headers": _counts(combine_scores([score.headers for score in scores])),
                    "lines": _counts(combine_scores([score.lines for score in scores])),
                    "per_field": {
                        name: _counts(combine_scores(values)) for name, values in fields.items()
                    },
                    "missing_lines": sum(score.missing_lines for score in scores),
                    "extra_lines": sum(score.extra_lines for score in scores),
                    "cases": cases,
                },
            }
        )

    return {
        "version": "evaluation-v1",
        "corpus": corpus.version,
        "runs": runs,
        "variants": variants,
        "scoring": "exact-contract-values-positional-lines-extra-rows-penalized-no-normalization",
        "selection_disclosure": (
            "Gold cases used for screening/tuning are development data, not a held-out test."
        ),
    }
