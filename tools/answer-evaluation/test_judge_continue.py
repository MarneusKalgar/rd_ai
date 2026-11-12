"""The recovery recognizes exactly one startup notice, never a real tool/error."""

import json
from pathlib import Path
from typing import Any

import pytest
from judge import controls
from judge_continue import checked_result
from test_verdicts import execution

NOTICE = (
    "Under-development features enabled: skip_host_skill_discovery. "
    "Under-development features are incomplete and may behave unpredictably. "
    "To suppress this warning, set `suppress_unstable_features_warning = true` "
    "in /fixture/config.toml."
)


@pytest.mark.parametrize("kind", ["startup", "after_turn", "other_error", "tool", "duplicate"])
def test_only_specific_preturn_notice_is_allowed(tmp_path: Path, kind: str) -> None:
    events = execution(tmp_path)
    notice: dict[str, Any] = {
        "type": "item.completed",
        "item": {"type": "error", "message": NOTICE},
    }
    if kind == "other_error":
        notice["item"]["message"] = "Real execution failed"
    elif kind == "tool":
        notice["item"]["type"] = "command_execution"
    if kind == "after_turn":
        events.insert(0, {"type": "turn.started"})
        events.insert(1, notice)
    else:
        events.insert(0, notice)
        if kind == "duplicate":
            events.insert(0, notice)
    (tmp_path / "events.jsonl").write_text("\n".join(json.dumps(item) for item in events))

    if kind == "startup":
        result = checked_result(tmp_path, controls()[0])
        assert len(result["startup_notices"]) == 1
        assert result["verdict"]["correctness"] == "pass"
    else:
        with pytest.raises(ValueError):
            checked_result(tmp_path, controls()[0])
