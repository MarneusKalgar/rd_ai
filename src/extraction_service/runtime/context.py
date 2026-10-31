"""Complete setup requests; byte inventory is distinct from verified token capacity."""

from collections.abc import Generator
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from extraction_service.artifacts import read_text
from extraction_service.configuration.models import ExperimentConfig
from extraction_service.corpus.loading import load_corpus
from extraction_service.execution.evidence import render_correction
from extraction_service.inference.messages import request_messages
from extraction_service.inference.types import GenerationRequest
from extraction_service.record_types import AttemptKind


@dataclass(frozen=True)
class PreparedRequest:
    input_id: str
    input_sha256: str
    prompt_id: str
    kind: AttemptKind
    request: GenerationRequest

    def message_utf8_bytes(self) -> int:
        """Measure full message bytes for diagnostic inventory and sample selection."""

        messages = request_messages(self.request)

        return sum(len(message["content"].encode("utf-8")) for message in messages)

    def inventory(self) -> dict[str, Any]:
        """Count full message bytes, including schema and any correction evidence."""

        return {
            "input_id": self.input_id,
            "input_sha256": self.input_sha256,
            "prompt_id": self.prompt_id,
            "sampling_id": self.request.sampling.id,
            "kind": self.kind.value,
            "message_utf8_bytes": self.message_utf8_bytes(),
            "output_allowance_tokens": self.request.sampling.max_output_tokens,
        }


def prepared_requests(
    project_dir: Path, experiment: ExperimentConfig
) -> Generator[PreparedRequest]:
    """Include all inputs/variants and an explicit invalid-object correction case.

    The correction fixture is intentionally invalid (`{}`), and its complete
    validation issues use production rendering. It is not a worst-case bound for
    future model responses; those need admission with their actual evidence.
    Gold values never enter any diagnostic request.
    """

    corpus = load_corpus(project_dir)
    invalid = corpus.contract.validate_json("{}")

    for prompt in experiment.prompts:
        instructions = read_text(project_dir / prompt.file)
        corrected_instructions = render_correction(instructions, "{}", invalid.issues)

        for sampling in experiment.sampling:
            for source in corpus.inputs:
                for kind in (AttemptKind.EXTRACTION, AttemptKind.CORRECTION):
                    request = GenerationRequest.from_contract(
                        instructions=(
                            instructions
                            if kind == AttemptKind.EXTRACTION
                            else corrected_instructions
                        ),
                        source_text=source.text,
                        contract=corpus.contract,
                        sampling=sampling,
                        timeout_seconds=experiment.execution.request_timeout_seconds,
                    )

                    yield PreparedRequest(
                        input_id=source.input_id,
                        input_sha256=source.input_sha256,
                        prompt_id=prompt.id,
                        kind=kind,
                        request=request,
                    )


def context_inventory(project_dir: Path, experiment: ExperimentConfig) -> dict[str, Any]:
    """Inventory complete messages without treating bytes as a model-token bound."""

    requests = []
    largest: dict[str, Any] | None = None

    for prepared in prepared_requests(project_dir, experiment):
        item = prepared.inventory()
        requests.append(item)

        if largest is None or item["message_utf8_bytes"] > largest["message_utf8_bytes"]:
            largest = item

    return {
        "token_capacity_verified": False,
        "largest_by_bytes": largest,
        "requests": requests,
        "correction_fixture": "invalid response {} with all authoritative validator issues",
        "future_corrections_require_actual_request_admission": True,
    }
