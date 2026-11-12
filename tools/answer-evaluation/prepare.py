"""Prepare source-bound S08 human review without changing frozen S07 records."""

import json
from pathlib import Path
from typing import Any

from extraction_service.answering.contract import AnswerJob, validate_answer
from extraction_service.answering.protocol import verified_jobs
from extraction_service.inference.types import GenerationRequest
from extraction_service.retrieval.core import canonical, digest

CALIBRATION = ("Q01", "Q07", "Q13", "Q22", "Q25", "Q29", "Q35", "Q38")
AUDIT = ("Q12", "Q24", "Q32", "Q40")
REPORT = "docs/reports/P03-rag-answers-summary.json"
EVIDENCE = Path("/evidence")
OUTPUT = Path("/review-output")


def combine(journals: list[list[dict[str, Any]]]) -> dict[str, dict[str, Any]]:
    """Fill only unsent slots; reject replacements of actual observations."""

    combined: dict[str, dict[str, Any]] = {}
    for events in journals:
        if not events or events[-1].get("event") != "complete":
            raise ValueError("Incomplete journal")
        seen: set[str] = set()
        for row in events:
            if row.get("event") != "outcome":
                continue
            key = row["key"]
            if key in seen or (key in combined and combined[key]["outcome"] != "not_attempted"):
                raise ValueError("Duplicate or replaced observation")
            seen.add(key)
            combined[key] = row
    if any(row["outcome"] == "not_attempted" for row in combined.values()):
        raise ValueError("Unattempted job remains")
    return combined


def write_once(path: Path, value: bytes) -> None:
    """Allow identical reproduction without overwriting human edits."""

    if path.exists():
        if path.read_bytes() != value:
            raise ValueError(f"Refusing to replace {path.name}")
        return
    with path.open("xb") as output:
        output.write(value)


def load_population(
    root: Path, evidence: Path
) -> tuple[list[AnswerJob], dict[str, dict[str, Any]], dict[str, Any]]:
    """Reconstruct the fixed population before any evaluation or replay."""

    profile, jobs, manifest = verified_jobs(root)
    summary = json.loads((root / REPORT).read_bytes())
    if manifest != summary["parent_manifest_sha256"]:
        raise ValueError("Manifest differs from operational receipt")
    journals = []
    for name, expected in summary["receipts"].items():
        raw = (evidence / name).read_bytes()
        if digest(raw) != expected:
            raise ValueError(f"Journal hash differs: {name}")
        journals.append([json.loads(line) for line in raw.splitlines()])
    outcomes = combine(journals)
    expected_jobs = {job.key: job for job in jobs}
    if set(outcomes) != set(expected_jobs) or len(jobs) != 120:
        raise ValueError("Full job membership differs")
    physical = [
        event for events in journals for event in events if event.get("event") == "physical_result"
    ]
    physical_keys = [row["key"] for row in physical]
    if len(physical_keys) != len(set(physical_keys)) or len(physical_keys) != 108:
        raise ValueError("Physical population differs")
    physical_by_key = {row["key"]: row for row in physical}
    requests = [
        event for events in journals for event in events if event.get("event") == "reserved"
    ]
    request_by_key = {row["key"]: row["request"] for row in requests}
    if len(requests) != 108 or set(request_by_key) != set(physical_by_key):
        raise ValueError("Reserved request population differs")
    instructions = (root / profile.prompt).read_text()
    for job in jobs:
        row = outcomes[job.key]
        if row["job"] != job.model_dump(mode="json"):
            raise ValueError("Saved job differs from frozen job")
        if job.key in request_by_key:
            request = GenerationRequest.model_validate_json(json.dumps(request_by_key[job.key]))
            if request != job.request(instructions, profile.sampling, request.timeout_seconds):
                raise ValueError("Physical request differs from frozen instructions/settings")
            if not 0 < request.timeout_seconds <= profile.request_seconds:
                raise ValueError("Physical request timeout differs")
            row["_request"] = request_by_key[job.key]
        if row["outcome"] == "structurally_valid":
            response = physical_by_key[job.key]["response"]
            if row["response"] != response:
                raise ValueError("Physical and outcome response differ")
            answer = validate_answer(response["raw_response"], job)
            if answer.model_dump(mode="json") != row["answer"]:
                raise ValueError("Parsed answer differs")
        elif job.skip_reason is not None:
            if row["outcome"] != "deterministic_non_answer" or row["physical_calls"] != 0:
                raise ValueError("Skip differs")
        elif row["outcome"] != "response_failure" or job.key != "Q07/bm25":
            raise ValueError("Unexpected failure")
    return jobs, outcomes, summary


def prepare(root: Path, evidence: Path, output: Path) -> dict[str, Any]:
    """Verify sources, reconstruct membership and publish ungraded review packets."""

    jobs, outcomes, summary = load_population(root, evidence)
    manifest = summary["parent_manifest_sha256"]
    rubric = json.loads((root / "config/evaluation/P03-E03-rubric-v1.json").read_bytes())
    bundles = []
    for job in jobs:
        row = outcomes[job.key]
        opaque_id = digest(job.key.encode())[:16]
        bundles.append(
            {
                "id": opaque_id,
                "question": job.question,
                "expected_propositions": rubric["cases"][job.case_id],
                "evidence": [item.model_dump(mode="json") for item in job.context],
                "answer": row.get("answer"),
                "operational_outcome": row["outcome"],
                "evidence_available": bool(job.context),
            }
        )
    output.mkdir(parents=True, exist_ok=True)
    template: dict[str, Any] = {
        "authority": "pending human review",
        "reviewer": None,
        "decisions": [],
    }
    mapping = {}
    for phase, cases in (("calibration", CALIBRATION), ("audit", AUDIT)):
        lines = [
            f"# S08 {phase} review",
            "",
            "All verdicts are pending. Verify expected propositions against the sources.",
            "For each answer record correctness, completeness, unsupported claims,",
            "citation support, abstention/conflict behavior and evidence/rationale.",
            "Application skips and provider failures are not model abstentions.",
            "",
        ]
        for job, bundle in zip(jobs, bundles, strict=True):
            if job.case_id not in cases:
                continue
            mapping[bundle["id"]] = {"key": job.key, "phase": phase}
            lines.extend(
                [
                    f"## {bundle['id']}",
                    "",
                    "```json",
                    json.dumps(bundle, indent=2, ensure_ascii=False),
                    "```",
                    "",
                ]
            )
            template["decisions"].append(
                {
                    "id": bundle["id"],
                    "phase": phase,
                    "correctness": None,
                    "completeness": None,
                    "claim_support": None,
                    "abstention_or_conflict": None,
                    "evidence_and_rationale": None,
                    "expected_propositions_approved": None,
                }
            )
        write_once(output / f"{phase}-review.md", "\n".join(lines).encode())
    profile = {
        "id": "P03-S08-v1",
        "generation_manifest": manifest,
        "receipts": summary["receipts"],
        "judge": "gpt-6.1-sol",
        "human_review": "pending",
        "semantic_adoption": "unresolved",
        "calibration_cases": CALIBRATION,
        "audit_cases": AUDIT,
        "selection": "Two calibration and one audit question per frozen group;"
        " includes provider failure, nonsense, conflict, scope B, deletion and history.",
        "bundle_sha256": digest(canonical(bundles)),
        "jobs": len(bundles),
        "judge_calls": 0,
        "human_reviewed": 0,
    }
    for name, value in (
        ("profile.json", profile),
        ("bundles.json", bundles),
        ("review-template.json", template),
        ("private-mapping.json", mapping),
    ):
        write_once(output / name, json.dumps(value, indent=2, ensure_ascii=False).encode() + b"\n")
    return profile


if __name__ == "__main__":
    print(json.dumps(prepare(Path.cwd(), EVIDENCE, OUTPUT), indent=2))
