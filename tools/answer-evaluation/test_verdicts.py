"""Independent evidence, coverage, quota and execution-negative controls."""

import json
from pathlib import Path
from typing import Any

import pytest
from judge import check_quota, check_result, controls
from verdicts import validate_verdict


def valid() -> dict[str, Any]:
    return {
        "id": "control-0",
        "correctness": "pass",
        "completeness": "pass",
        "abstention": "unknown",
        "propositions": [{"index": 0, "verdict": "pass", "rationale": "Preserves text and zeros"}],
        "claims": [
            {
                "claim_index": 0,
                "support": "pass",
                "evidence": [{"context_index": 0, "quote": "Keep identifiers as text"}],
                "rationale": "Exact supplied source supports the stated rule",
            }
        ],
        "summary_has_unsupported_additions": "pass",
        "rationale": "Source-backed rule",
    }


def test_valid_quote_and_complete_coverage() -> None:
    result = validate_verdict(json.dumps(valid()), controls()[0])

    assert result.correctness == "pass"


@pytest.mark.parametrize("defect", ["identity", "quote", "context", "coverage", "citation"])
def test_invalid_evidence_is_rejected(defect: str) -> None:
    value = valid()
    bundle = controls()[0]
    if defect == "identity":
        value["id"] = "other"
    elif defect == "quote":
        value["claims"][0]["evidence"][0]["quote"] = "invented quotation"
    elif defect == "context":
        value["claims"][0]["evidence"][0]["context_index"] = 1
    elif defect == "coverage":
        value["propositions"] = []
    else:
        bundle["answer"]["claims"][0]["citations"] = []

    with pytest.raises(ValueError):
        validate_verdict(json.dumps(value), bundle)


def test_no_context_cannot_claim_grounding() -> None:
    bundle = controls()[0]
    bundle["evidence"] = []
    value = valid()
    value["claims"][0]["evidence"] = []

    with pytest.raises(ValueError, match="requires exact evidence"):
        validate_verdict(json.dumps(value), bundle)


def quota() -> dict[str, Any]:
    return {
        "id": 1,
        "result": {
            "ordinaryUsageAllowed": True,
            "rateLimits": {
                "planType": "plus",
                "credits": {"hasCredits": False, "unlimited": False, "balance": "0"},
                "rateLimitReachedType": None,
                "primary": {"usedPercent": 25},
                "secondary": {"usedPercent": 40},
            },
        },
    }


def test_included_allowance_admitted(tmp_path: Path) -> None:
    path = tmp_path / "quota.jsonl"
    path.write_text(json.dumps(quota()))

    assert check_quota(path)["has_credits"] is False


@pytest.mark.parametrize("defect", ["credit", "exhausted", "unavailable", "missing"])
def test_paid_or_unknown_quota_stops(tmp_path: Path, defect: str) -> None:
    value = quota()
    if defect == "credit":
        value["result"]["rateLimits"]["credits"]["hasCredits"] = True
    elif defect == "exhausted":
        value["result"]["rateLimits"]["primary"]["usedPercent"] = 90
    elif defect == "unavailable":
        value["result"]["ordinaryUsageAllowed"] = False
    else:
        value = {}
    path = tmp_path / "quota.jsonl"
    path.write_text(json.dumps(value))

    with pytest.raises(ValueError):
        check_quota(path)


def execution(directory: Path) -> list[dict[str, Any]]:
    raw = json.dumps(valid())
    (directory / "exit-code.txt").write_text("0")
    (directory / "verdict.json").write_text(raw)
    return [
        {"type": "item.completed", "item": {"type": "agent_message", "text": raw}},
        {"type": "turn.completed", "usage": {"output_tokens": 100}},
    ]


def test_text_only_completed_turn(tmp_path: Path) -> None:
    events = execution(tmp_path)
    (tmp_path / "events.jsonl").write_text("\n".join(json.dumps(item) for item in events))

    result = check_result(tmp_path, controls()[0])

    assert result["authority"] == "provisional AI judgment"
    assert result["api_charge_usd"] is None


@pytest.mark.parametrize("defect", ["tool", "missing_turn", "changed_verdict", "exit", "tokens"])
def test_execution_failures_are_not_semantic_passes(tmp_path: Path, defect: str) -> None:
    events = execution(tmp_path)
    if defect == "tool":
        events.insert(0, {"type": "item.started", "item": {"type": "command_execution"}})
    elif defect == "missing_turn":
        events.pop()
    elif defect == "changed_verdict":
        (tmp_path / "verdict.json").write_text("{}")
    elif defect == "exit":
        (tmp_path / "exit-code.txt").write_text("137")
    else:
        events[-1]["usage"]["output_tokens"] = 12001
    (tmp_path / "events.jsonl").write_text("\n".join(json.dumps(item) for item in events))

    with pytest.raises(ValueError):
        check_result(tmp_path, controls()[0])
