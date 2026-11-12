"""R01: preserve the stopped judge phase; recognize one exact pre-turn CLI notice."""

import argparse
import json
import re
import shlex
import tempfile
from pathlib import Path
from typing import Any

import judge
from prepare import write_once

from extraction_service.retrieval.core import digest

NOTICE = re.compile(
    r"Under-development features enabled: skip_host_skill_discovery\. "
    r"Under-development features are incomplete and may behave unpredictably\. "
    r"To suppress this warning, set `suppress_unstable_features_warning = true` in "
    r"[^\n]+/config\.toml\."
)
ADDENDUM = judge.RUNNER / "continuation-R01.json"


def checked_result(directory: Path, bundle: dict[str, Any]) -> dict[str, Any]:
    """Ignore only a known client notice before turn start; all tool/error checks remain."""

    events = [json.loads(line) for line in (directory / "events.jsonl").read_text().splitlines()]
    cleaned = []
    notices: list[str] = []
    started = False
    for event in events:
        if event.get("type") == "turn.started":
            started = True
        item = event.get("item", {})
        if (
            not started
            and event.get("type") == "item.completed"
            and item.get("type") == "error"
            and NOTICE.fullmatch(item.get("message", ""))
        ):
            if notices:
                raise ValueError("Repeated startup notice")
            notices.append(item["message"])
        else:
            cleaned.append(event)
    with tempfile.TemporaryDirectory() as temporary:
        target = Path(temporary)
        for name in ("exit-code.txt", "verdict.json"):
            (target / name).write_bytes((directory / name).read_bytes())
        (target / "events.jsonl").write_text("\n".join(json.dumps(item) for item in cleaned))
        result = judge.check_result(target, bundle)
    return dict(
        result,
        startup_notices=notices,
        raw_events_sha256=digest((directory / "events.jsonl").read_bytes()),
    )


def verify(root: Path) -> dict[str, Any]:
    manifest = judge.read_manifest(root)
    addendum = json.loads(ADDENDUM.read_bytes())
    if addendum["original_manifest_sha256"] != digest(
        (judge.RUNNER / "manifest.json").read_bytes()
    ):
        raise ValueError("Original judge manifest changed")
    if addendum["controller_sha256"] != digest(Path(__file__).read_bytes()):
        raise ValueError("R01 controller changed")
    if addendum["script_sha256"] != digest((judge.RUNNER / "continue-R01.sh").read_bytes()):
        raise ValueError("R01 orchestration changed")
    if addendum["first_events_sha256"] != digest((judge.RUNNER / "000/events.jsonl").read_bytes()):
        raise ValueError("Preserved first observation changed")
    return manifest


def freeze(root: Path, host_root: str) -> None:
    """Bind the parser addendum and derive orchestration from the frozen original."""

    judge.read_manifest(root)
    first = judge.RUNNER / "000"
    checked_result(first, json.loads((first / "bundle.json").read_bytes()))
    source = (root / "tools/answer-evaluation/run-judge.sh").read_text()
    start = 'task_root="$(cd "$(dirname "$0")/../.." && pwd)"'
    stop = (
        '    echo "Existing attempt $task_job; stop without automatic retry or resume." >&2\n'
        "    exit 3"
    )
    if source.count(start) != 1 or source.count(stop) != 1:
        raise ValueError("Original orchestration shape differs")
    script = source.replace(start, f"task_root={shlex.quote(host_root)}").replace(
        stop, '    make -C "$task_root" answer-judge-r01-check JOB="$task_job"\n    continue'
    )
    script = (
        script.replace("answer-judge-admit", "answer-judge-r01-admit")
        .replace("answer-judge-check", "answer-judge-r01-check")
        .replace("answer-judge-summary", "answer-judge-r01-summary")
    )
    write_once(judge.RUNNER / "continue-R01.sh", script.encode())
    addendum = {
        "id": "P03-S08-R01",
        "original_manifest_sha256": digest((judge.RUNNER / "manifest.json").read_bytes()),
        "controller_sha256": digest(Path(__file__).read_bytes()),
        "first_events_sha256": digest((first / "events.jsonl").read_bytes()),
        "script_sha256": digest(script.encode()),
        "reason": (
            "Recognize the exact pre-turn CLI feature warning; retain all genuine errors/tools."
        ),
        "first_observation": "reused unchanged; no inference repeated",
        "scope": (
            "remaining 108 jobs; one attempt per job, unchanged model/prompt/schema/quota gates"
        ),
    }
    write_once(ADDENDUM, json.dumps(addendum, indent=2).encode() + b"\n")
    print(json.dumps(addendum, indent=2))


def admit(root: Path, name: str) -> None:
    manifest = verify(root)
    names = [item["directory"] for item in manifest["jobs"]]
    if name not in names:
        raise ValueError("Unknown R01 job")
    index = names.index(name)
    directory = judge.RUNNER / name
    if (directory / "started.txt").exists():
        raise ValueError("R01 attempt already started")
    judge.check_quota(directory / "quota.jsonl")
    for previous in names[:index]:
        prior = judge.RUNNER / previous
        checked_result(prior, json.loads((prior / "bundle.json").read_bytes()))
    for filename, expected in (
        ("bundle.json", manifest["jobs"][index]["request_sha256"]),
        ("instructions.txt", manifest["prompt_sha256"]),
        ("schema.json", manifest["schema_sha256"]),
    ):
        if digest((directory / filename).read_bytes()) != expected:
            raise ValueError("R01 frozen request changed")
    print(json.dumps({"job": name, "admitted": True, "authority": "provisional"}))


def summarize(root: Path) -> None:
    manifest = verify(root)
    rows = []
    for entry in manifest["jobs"]:
        directory = judge.RUNNER / entry["directory"]
        if not (directory / "started.txt").exists():
            rows.append({"id": entry["id"], "status": "not_attempted"})
            continue
        try:
            result = checked_result(directory, json.loads((directory / "bundle.json").read_bytes()))
            rows.append(dict(result, status="valid_provisional"))
        except (ValueError, KeyError, OSError) as error:
            rows.append({"id": entry["id"], "status": "invalid_or_incomplete", "error": str(error)})
    result = {
        "profile": manifest["profile"],
        "addendum": "P03-S08-R01",
        "rows": rows,
        "human_calibration": "incomplete",
        "semantic_adoption": "unresolved",
    }
    (judge.RUNNER / "provisional-summary-R01.json").write_text(json.dumps(result, indent=2) + "\n")
    print(
        json.dumps(
            {
                "jobs": len(rows),
                "valid_provisional": sum(item["status"] == "valid_provisional" for item in rows),
            }
        )
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=("freeze", "admit", "check", "summary"))
    parser.add_argument("--job")
    parser.add_argument("--host-root")
    args = parser.parse_args()
    if args.action == "freeze":
        freeze(Path.cwd(), args.host_root)
    elif args.action == "admit":
        admit(Path.cwd(), args.job)
    elif args.action == "check":
        verify(Path.cwd())
        directory = judge.RUNNER / args.job
        print(
            json.dumps(
                checked_result(directory, json.loads((directory / "bundle.json").read_bytes()))
            )
        )
    else:
        summarize(Path.cwd())
