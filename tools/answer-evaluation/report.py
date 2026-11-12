"""Complete-population deterministic accounting and provisional paired reporting."""

import json
from collections import Counter
from datetime import datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

from prepare import EVIDENCE, OUTPUT, load_population

from extraction_service.execution.budget.ledger import BudgetSnapshot
from extraction_service.retrieval.core import digest


def report(root: Path) -> dict[str, Any]:
    """Reconcile saved calls with a read-only ledger, retaining all non-answer outcomes."""

    jobs, outcomes, source = load_population(root, EVIDENCE)
    ledger_path = root / "results/budget-ledger.json"
    ledger_bytes = ledger_path.read_bytes()
    ledger = BudgetSnapshot.model_validate_json(ledger_bytes)
    reservations = {entry.id: entry for entry in ledger.reservations}
    selected: set[str] = set()
    arms: dict[str, Any] = {}
    for job in jobs:
        arm = arms.setdefault(
            job.arm.value,
            {"jobs": 0, "physical_calls": 0, "outcomes": Counter(), "known_cost_usd": "0"},
        )
        arm["jobs"] += 1
        row = outcomes[job.key]
        arm["outcomes"][row["outcome"]] += 1
        arm["physical_calls"] += row["physical_calls"]
        if row["physical_calls"]:
            identity = row["reservation_id"]
            if identity in selected:
                raise ValueError("Repeated billed observation")
            selected.add(identity)
            reservation = reservations[identity]
            billed = row["response"]["cost_usd"]
            if billed is None or reservation.billed_usd != Decimal(str(billed)):
                raise ValueError("Ledger charge differs from response")
            arm["known_cost_usd"] = str(Decimal(arm["known_cost_usd"]) + reservation.billed_usd)
    total_cost = sum((Decimal(arm["known_cost_usd"]) for arm in arms.values()), Decimal(0))
    if len(selected) != 108 or total_cost != Decimal(source["total_e03_cost_usd"]):
        raise ValueError("Complete physical accounting differs")
    prior = [entry for entry in ledger.reservations if entry.id not in selected]
    unknown_holds = sum(
        (entry.reserved_usd for entry in prior if entry.billed_usd is None), Decimal(0)
    )
    if len(prior) != 215 or unknown_holds != Decimal(source["prior_unknown_holds_usd"]):
        raise ValueError("Prior reservations/unknown holds differ")
    if ledger.accounted_usd != Decimal(source["cumulative_accounted_usd"]):
        raise ValueError("Cumulative ledger differs")
    if ledger_path.read_bytes() != ledger_bytes:
        raise ValueError("Ledger changed during read-only reconstruction")
    metrics: dict[str, Any] = {}
    cases = {
        case["id"]: case
        for case in json.loads((root / "config/evaluation/P03-cases-v1.json").read_bytes())["cases"]
    }
    for name in ("bm25", "vector"):
        selected_jobs = [job for job in jobs if job.arm.value == name]
        positives = [job for job in selected_jobs if cases[job.case_id]["relevant"]]
        recall, precision, reciprocal = [], [], []
        for job in positives:
            relevant = set(cases[job.case_id]["relevant"])
            revision_specific = any("@" in item for item in relevant)
            retrieved = [
                item.source_id + (f"@{item.revision}" if revision_specific else "")
                for item in job.context
            ]
            hits = len(set(retrieved) & relevant)
            recall.append(hits / len(relevant))
            precision.append(hits / 3)
            ranks = [index + 1 for index, item in enumerate(retrieved) if item in relevant]
            reciprocal.append(1 / min(ranks) if ranks else 0)
        metrics[name] = {
            "cases": len(selected_jobs),
            "positive_relevance_cases": len(positives),
            "macro_recall_at_3": sum(recall) / len(recall),
            "macro_precision_at_3": sum(precision) / len(precision),
            "mrr": sum(reciprocal) / len(reciprocal),
            "authority": "authored technical relevance, not human accuracy",
        }
    grade_path = OUTPUT / "judge-v1/provisional-summary-R01.json"
    if not grade_path.exists():
        grade_path = OUTPUT / "judge-v1/provisional-summary.json"
    grades = json.loads(grade_path.read_bytes())["rows"] if grade_path.exists() else []
    if grade_path.exists() and grade_path.name == "provisional-summary-R01.json":
        from judge_continue import checked_result, verify

        manifest = verify(root)
        for entry, grade in zip(manifest["jobs"], grades, strict=True):
            if grade["id"] != entry["id"]:
                raise ValueError("Provisional summary job identity differs")
            if grade["status"] == "valid_provisional":
                directory = OUTPUT / "judge-v1" / entry["directory"]
                actual = checked_result(
                    directory, json.loads((directory / "bundle.json").read_bytes())
                )
                if grade["verdict"] != actual["verdict"] or grade["usage"] != actual["usage"]:
                    raise ValueError("Provisional summary differs from raw CLI result")
    grades_by_id = {item["id"]: item for item in grades}
    usage: Counter[str] = Counter()
    threads: set[str] = set()
    timing: dict[str, list[datetime]] = {"original": [], "R01": []}
    valid_grades = 0
    if grades:
        manifest = json.loads((OUTPUT / "judge-v1/manifest.json").read_bytes())
        for entry, grade in zip(manifest["jobs"], grades, strict=True):
            if grade["status"] != "valid_provisional":
                continue
            valid_grades += 1
            for key, value in grade["usage"].items():
                if type(value) is int:
                    usage[key] += value
            directory = OUTPUT / "judge-v1" / entry["directory"]
            events = [
                json.loads(line) for line in (directory / "events.jsonl").read_text().splitlines()
            ]
            identifiers = [
                event["thread_id"] for event in events if event.get("type") == "thread.started"
            ]
            if len(identifiers) != 1 or identifiers[0] in threads:
                raise ValueError("Judge thread identity missing or reused")
            threads.add(identifiers[0])
            phase = "original" if entry["directory"] == "000" else "R01"
            for filename in ("started.txt", "finished.txt"):
                timing[phase].append(
                    datetime.fromisoformat((directory / filename).read_text().strip())
                )
    paired = []
    provisional: dict[str, Any] = {}
    for job in jobs:
        grade = grades_by_id.get(digest(job.key.encode())[:16])
        stats = provisional.setdefault(
            job.arm.value,
            {
                "jobs": 0,
                "valid_ai_grades": 0,
                "complete_correct_rubric_passes": 0,
                "reviewed_human_anchors": 0,
                "explicit_claims": 0,
                "supported_explicit_claims": 0,
                "authority": "uncalibrated AI judgment; no semantic adoption conclusion",
            },
        )
        stats["jobs"] += 1
        if grade and grade["status"] == "valid_provisional":
            verdict = grade["verdict"]
            stats["valid_ai_grades"] += 1
            stats["complete_correct_rubric_passes"] += (
                verdict["correctness"] == "pass" and verdict["completeness"] == "pass"
            )
            stats["explicit_claims"] += len(verdict["claims"])
            stats["supported_explicit_claims"] += sum(
                claim["support"] == "pass" for claim in verdict["claims"]
            )
        paired.append(
            {
                "key": job.key,
                "group": cases[job.case_id]["group"],
                "operational_outcome": outcomes[job.key]["outcome"],
                "answer_status": (outcomes[job.key].get("answer") or {}).get("status", "absent"),
                "semantic_review": grade or {"status": "unreviewed"},
            }
        )
    human_overall = None
    if (OUTPUT / "human-overall-review.json").exists():
        from overall_reviews import finalize

        human_overall = finalize(OUTPUT)
        if json.loads((OUTPUT / "human-overall-review.json").read_bytes()) != human_overall:
            raise ValueError("Finalized human overall review differs from source labels")
        human_overall = {key: value for key, value in human_overall.items() if key != "rows"}
    from improvement import improvement

    return {
        "id": "P03-S08-v1",
        "jobs": len(jobs),
        "arms": arms,
        "retrieval": metrics,
        "source_receipts": source["receipts"],
        "ledger_sha256": digest(ledger_bytes),
        "prior_unknown_holds_usd": str(unknown_holds),
        "e03_known_cost_usd": str(total_cost),
        "paired_outcomes": paired,
        "provisional_semantic_counts": provisional,
        "improvement_metrics": improvement(paired, cases),
        "judge_execution": {
            "valid_provisional_records_including_controls": valid_grades,
            "distinct_thread_ids": len(threads),
            "reported_usage": dict(usage),
            "phase_spans_seconds": {
                key: (max(values) - min(values)).total_seconds()
                for key, values in timing.items()
                if values
            },
            "usage_note": "reported fields; cached/reasoning fields may be subsets, not additive",
            "api_ledger_writes": 0,
            "cli_internal_physical_requests": "unavailable",
        },
        "human_calibration": "incomplete",
        "human_overall_review": human_overall,
        "semantic_adoption": "unresolved",
        "new_generator_calls": 0,
    }


if __name__ == "__main__":
    result = report(Path.cwd())
    (OUTPUT / "evaluation-report.json").write_text(json.dumps(result, indent=2) + "\n")
    public = Path("/public-output")
    if public.is_dir():
        compact = {key: value for key, value in result.items() if key != "paired_outcomes"}
        compact["provisional_summary_sha256"] = digest(
            (OUTPUT / "judge-v1/provisional-summary-R01.json").read_bytes()
        )
        (public / "P03-evaluation-summary.json").write_text(json.dumps(compact, indent=2) + "\n")
    print(
        json.dumps(
            {key: value for key, value in result.items() if key != "paired_outcomes"}, indent=2
        )
    )
