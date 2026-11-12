"""Replay actual S07 responses through matched direct and LangChain composition."""

import importlib
import json
import time
from functools import partial
from pathlib import Path
from typing import Any

from prepare import EVIDENCE, OUTPUT, load_population, write_once

from extraction_service.answering.contract import AnswerJob, validate_answer
from extraction_service.answering.protocol import load_profile
from extraction_service.inference.types import GenerationRequest, ModelResponse
from extraction_service.retrieval.core import canonical, digest
from extraction_service.retrieval.integration import check_tracing_disabled


def compose(
    job: AnswerJob, instructions: str, sampling: Any, timeout: float
) -> GenerationRequest | None:
    """Reuse the actual request contract; deterministic skips make no replay call."""

    if job.skip_reason is not None:
        return None
    return job.request(instructions, sampling, timeout)


def finish(
    request: GenerationRequest | None, job: AnswerJob, row: dict[str, Any]
) -> dict[str, Any]:
    """Return the saved response intact, including the retained upstream error."""

    if request is None:
        return {"skip": job.skip_reason, "replay_calls": 0}
    response = ModelResponse.model_validate_json(json.dumps(row["response"]))
    if request.model_dump(mode="json") != row["_request"]:
        raise ValueError("Replay request differs from original physical request")
    result: dict[str, Any] = {
        "request": request.model_dump(mode="json"),
        "response": response.model_dump(mode="json"),
        "replay_calls": 1,
        "outcome": row["outcome"],
    }
    if row["outcome"] == "structurally_valid":
        if response.raw_response is None:
            raise ValueError("Valid response lacks text")
        result["answer"] = validate_answer(response.raw_response, job).model_dump(mode="json")
    return result


def replay(root: Path, evidence: Path) -> dict[str, Any]:
    """Measure composition/validation parity without network or generator clients."""

    check_tracing_disabled()
    runnable = importlib.import_module("langchain_core.runnables").RunnableLambda
    jobs, outcomes, source = load_population(root, evidence)
    profile = load_profile(root)
    instructions = (root / profile.prompt).read_text()
    rows = []
    for job in jobs:
        row = outcomes[job.key]
        timeout = row.get("_request", {}).get("timeout_seconds", profile.request_seconds)
        started = time.perf_counter()
        direct = finish(compose(job, instructions, profile.sampling, timeout), job, row)
        direct_seconds = time.perf_counter() - started
        render = runnable(
            partial(compose, instructions=instructions, sampling=profile.sampling, timeout=timeout)
        )
        capture = runnable(partial(finish, job=job, row=row))
        started = time.perf_counter()
        framework = (render | capture).invoke(job, config={"callbacks": []})
        framework_seconds = time.perf_counter() - started
        if canonical(direct) != canonical(framework):
            raise ValueError(f"Replay parity differs: {job.key}")
        rows.append(
            {
                "key": job.key,
                "parity": True,
                "replay_calls": direct["replay_calls"],
                "outcome": row["outcome"],
                "result_sha256": digest(canonical(direct)),
                "direct_seconds": direct_seconds,
                "langchain_seconds": framework_seconds,
            }
        )
    return {
        "id": "P03-S08-actual-response-replay-v1",
        "jobs": len(rows),
        "responses_replayed_per_path": sum(row["replay_calls"] for row in rows),
        "parity": all(row["parity"] for row in rows),
        "rows": rows,
        "source_receipts": source["receipts"],
        "new_model_calls": 0,
        "interpretation": ("actual saved responses; integration parity, no new accuracy evidence"),
    }


if __name__ == "__main__":
    result = replay(Path.cwd(), EVIDENCE)
    # Timings vary between reproductions; each execution retains its own file.
    path = OUTPUT / f"actual-response-replay-{time.time_ns()}.json"
    write_once(path, json.dumps(result, indent=2).encode() + b"\n")
    print(json.dumps({key: value for key, value in result.items() if key != "rows"}, indent=2))
