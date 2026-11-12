"""Check that reconstruction cannot replace or discard actual observations."""

from pathlib import Path
from typing import Any

import pytest
from prepare import combine, prepare, write_once


def journal(key: str, outcome: str) -> list[dict[str, Any]]:
    return [{"event": "outcome", "key": key, "outcome": outcome}, {"event": "complete"}]


def test_only_unsent_can_be_filled() -> None:
    result = combine([journal("Q/a", "not_attempted"), journal("Q/a", "valid")])

    assert result["Q/a"]["outcome"] == "valid"


def test_completed_observation_cannot_be_replaced() -> None:
    with pytest.raises(ValueError, match="replaced"):
        combine([journal("Q/a", "valid"), journal("Q/a", "valid")])


def test_unsent_and_incomplete_are_rejected() -> None:
    with pytest.raises(ValueError, match="Unattempted"):
        combine([journal("Q/a", "not_attempted")])
    with pytest.raises(ValueError, match="Incomplete"):
        combine([journal("Q/a", "valid")[:-1]])


def test_review_edits_are_preserved(tmp_path: Any) -> None:
    path = tmp_path / "review.json"
    write_once(path, b"pending")
    write_once(path, b"pending")
    path.write_bytes(b"human decision")

    with pytest.raises(ValueError, match="Refusing"):
        write_once(path, b"pending")
    assert path.read_bytes() == b"human decision"


def test_real_frozen_population_produces_pending_review(tmp_path: Path) -> None:
    result = prepare(Path.cwd(), Path("/evidence"), tmp_path)

    assert result["jobs"] == 120
    assert result["judge_calls"] == 0
    assert result["human_reviewed"] == 0
    assert result["semantic_adoption"] == "unresolved"
    assert len(result["calibration_cases"]) == 8
    assert len(result["audit_cases"]) == 4
    assert set(result["calibration_cases"]).isdisjoint(result["audit_cases"])
    assert (tmp_path / "calibration-review.md").is_file()
    assert (tmp_path / "audit-review.md").is_file()


def test_tampered_journal_is_rejected(tmp_path: Path) -> None:
    (tmp_path / "pilot.jsonl").write_bytes(b"modified journal")

    with pytest.raises(ValueError, match="Journal hash differs: pilot.jsonl"):
        prepare(Path.cwd(), tmp_path, tmp_path / "output")
    assert not (tmp_path / "output").exists()
