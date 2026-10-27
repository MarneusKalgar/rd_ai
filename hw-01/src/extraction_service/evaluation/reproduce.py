"""Reproduce the published matrix without credentials, models or a private ledger."""

import argparse
import json
from decimal import Decimal
from pathlib import Path
from typing import Any

from extraction_service.application.persistence import reload_records
from extraction_service.archiving.archive import load_index, restore_archive, verify_archive
from extraction_service.archiving.bundles import verify_bundle
from extraction_service.archiving.files import confined, digest, read_json
from extraction_service.archiving.selection import verify_membership
from extraction_service.evaluation.budget_policy import EvaluationBudgetPolicy
from extraction_service.evaluation.reporting import evaluate_runs


def check_report_tables(report: str, rows: list[dict[str, Any]]) -> None:
    """Fail if the narrative's matrix tables disagree with regenerated metrics."""

    for row in rows:
        model = "G" if row["model"] == "local" else "F"
        sampling = "B" if row["sampling"] == "baseline-16384" else "E"
        key = f"{model} {row['prompt']} {sampling}"
        quality = row["quality"]
        operational = row["operational"]
        overall = quality["overall"]
        headers = quality["headers"]
        lines = quality["lines"]
        expected = (
            f"| {key} | {overall['correct']}/{overall['total']} | "
            f"{overall['accuracy'] * 100:.2f}% | {quality['exact_documents']} | "
            f"{headers['correct']}/{headers['total']} | {lines['correct']}/{lines['total']} | "
            f"{overall['present_correct']} | {overall['null_correct']} | "
            f"{quality['extra_lines']} / {quality['missing_lines']} |"
        )

        if expected not in report:
            raise ValueError(f"Report quality table differs: {key}")

        prefix = f"| {key} | {operational['first_valid']}/{operational['final_valid']} |"
        matches = [line for line in report.splitlines() if line.startswith(prefix)]

        if len(matches) != 1:
            raise ValueError(f"Report operational row is missing or ambiguous: {key}")

        columns = [value.strip() for value in matches[0].strip("|").split("|")]
        expected_latency = (
            f"{operational['latency_p50_ms'] / 1000:.3f} / "
            f"{operational['latency_p95_ms'] / 1000:.3f}"
        )

        if (
            len(columns) != 6
            or columns[2] != expected_latency
            or columns[3] != f"{row['processing_seconds']:.3f}"
            or Decimal(columns[4].removeprefix("$")) != Decimal(operational["total_api_cost_usd"])
            or Decimal(columns[5].removeprefix("$"))
            != Decimal(operational["api_cost_per_1000_attempted_inputs_usd"])
        ):
            raise ValueError(f"Report operational table differs: {key}")

        usage = row["usage"]
        token_row = (
            f"| {key} | {usage['input_tokens']['known_sum']} | "
            f"{usage['output_tokens']['known_sum']} |"
        )

        if token_row not in report:
            raise ValueError(f"Report usage table differs: {key}")

    for field in rows[0]["quality"]["per_field"]:
        label = field.replace("lineItems/*/", "line.")
        values = []

        for row in rows:
            score = row["quality"]["per_field"][field]
            values.append(f"{score['correct']}/{score['total']}")

        if "| " + label + " | " + " | ".join(values) + " |" not in report:
            raise ValueError(f"Report per-field table differs: {field}")


def reproduce_report(project: Path, policy_file: str, report_file: str) -> dict[str, Any]:
    """Verify restored provenance and match the published saved-data computation.

    The public policy is bound to original manifests and changes only evaluation
    grouping across the historical administrative cap raise. No spending ledger
    is opened or created. Archived Python drivers are never executed.
    """

    policy = EvaluationBudgetPolicy.model_validate_json(confined(project, policy_file).read_bytes())
    index = load_index(confined(project, f"archive-index/{policy.source_archive_sha256}.json"))

    if index.archive_sha256 != policy.source_archive_sha256:
        raise ValueError("Public policy archive differs from its index")

    manifest = verify_archive(project, index)
    restored = confined(project, f"results/restored/{index.archive_sha256}")

    if not restored.exists():
        restore_archive(project, index)

    for member in manifest.files:
        if digest(confined(restored, member.path)) != member.sha256:
            raise ValueError("Restored payload differs from the checked archive")

    public = restored / "submission"

    for source_bundle in manifest.bundles:
        verify_bundle(confined(public, source_bundle.name))

    bundle = confined(public, policy.evidence_bundle)
    membership = read_json(bundle / "membership.json")
    runs, count = verify_membership(public, membership)
    expected = read_json(bundle / "evaluation.json")
    evaluated = evaluate_runs(
        project,
        sorted(runs),
        source_dir=public.relative_to(project).as_posix(),
        sampling_aliases_file="config/matrix-sampling-aliases.json",
        budget_policy_file=policy_file,
    )
    public_policy_hash = evaluated.pop("public_budget_policy_sha256")

    if evaluated != expected:
        raise ValueError("Regenerated evaluation differs from the published evaluation")

    variants = evaluated["variants"]
    identities = {
        (v["identity"]["model_id"], v["identity"]["prompt_id"], v["identity"]["sampling"]["id"])
        for v in variants
    }
    required = {
        (model, prompt, sampling)
        for model in ("local", "provider-flash")
        for prompt in ("v1", "v2")
        for sampling in ("baseline-16384", "exploratory-16384")
    }

    if count != 240 or len(membership["entries"]) != 240 or identities != required:
        raise ValueError("Published matrix population is incomplete or unexpected")

    summary = json.loads((bundle / "summary.json").read_bytes())
    by_identity = {(r["model"], r["prompt"], r["sampling"]): r for r in summary}

    if len(summary) != 8 or set(by_identity) != required:
        raise ValueError("Published summary population differs")

    for variant in variants:
        identity = variant["identity"]
        key = (identity["model_id"], identity["prompt_id"], identity["sampling"]["id"])
        row = by_identity[key]
        quality = {key: value for key, value in variant["quality"].items() if key != "cases"}
        records = []

        for run_id in variant["run_ids"]:
            records.extend(reload_records(public / run_id)[1])

        if (
            len(records) != 30
            or len({r.input_id for r in records}) != 30
            or variant["quality"]["gold_cases"] != 10
            or quality != row["quality"]
            or variant["operational"] != row["operational"]
            or sum(r.duration_ms for r in records) / 1000 != row["processing_seconds"]
        ):
            raise ValueError("Published summary differs from regenerated metrics")

        attempts = [a for r in records for a in r.attempts]
        usage = {
            "input_tokens": [a.input_tokens for a in attempts],
            "output_tokens": [a.output_tokens for a in attempts],
        }

        for name, values in usage.items():
            measured = {
                "known_sum": sum(value for value in values if value is not None),
                "unknown_attempts": sum(value is None for value in values),
            }

            if measured != row["usage"][name]:
                raise ValueError("Published usage differs from saved attempts")

    check_report_tables(confined(project, report_file).read_text(), summary)
    return {
        "version": "report-reproduction-v1",
        "archive_sha256": index.archive_sha256,
        "public_budget_policy_sha256": public_policy_hash,
        "observations": count,
        "variants": len(variants),
        "bundles": len(manifest.bundles),
        "payload_files": len(manifest.files),
        "evaluation_and_report_tables_match": True,
        "private_ledger_required": False,
        "inference_performed": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-dir", type=Path, default=Path.cwd())
    parser.add_argument("--budget-policy", default="config/evaluation-budget-policy.json")
    parser.add_argument("--report", default="REPORT.md")
    args = parser.parse_args()

    try:
        result = reproduce_report(args.project_dir, args.budget_policy, args.report)
        output = args.project_dir / "results/reproductions" / result["archive_sha256"]
        output.mkdir(parents=True, exist_ok=True)
        (output / "verification.json").write_text(json.dumps(result, indent=2) + "\n")
        print(json.dumps(result, indent=2))
        return 0
    except (OSError, ValueError, KeyError, TypeError) as error:
        print(json.dumps({"reproduction_error": type(error).__name__}))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
