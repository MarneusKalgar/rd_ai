"""Strict experiment definitions, independent of provider availability."""

from typing import Annotated, Final, Literal, Self

from pydantic import Field, model_validator

from hw01.runtime_types import Identifier, NonEmptyText, PositiveFloat, PositiveInt, StrictModel

MAX_TRANSPORT_RETRIES: Final[int] = 5
ASSIGNMENT_API_CAP_USD: Final[float] = 5.0


class ModelConfig(StrictModel):
    """Requested model identity; capabilities must be verified by later adapters."""

    id: Identifier
    backend: Literal["openrouter", "ollama"]
    model: Identifier
    serving_provider: NonEmptyText | None = None

    @model_validator(mode="after")
    def check_provider(self) -> Self:
        """Keep serving-provider routing specific to provider requests."""

        if self.backend == "ollama" and self.serving_provider is not None:
            raise ValueError("Ollama models cannot specify a serving provider")

        return self


class PromptConfig(StrictModel):
    """A versioned prompt file owned by the HW project."""

    id: Identifier
    file: NonEmptyText


class SamplingConfig(StrictModel):
    """Requested common sampling values, not a claim of model support."""

    id: Identifier
    temperature: Annotated[float, Field(ge=0, le=2)]
    top_p: Annotated[float, Field(gt=0, le=1)]
    max_output_tokens: PositiveInt


class ExecutionConfig(StrictModel):
    """Runtime bounds; their enforcement belongs to the future coordinator."""

    request_timeout_seconds: PositiveFloat
    input_timeout_seconds: PositiveFloat
    transport_retries: Annotated[int, Field(ge=0, le=MAX_TRANSPORT_RETRIES)]
    api_budget_usd: Annotated[float, Field(gt=0, lt=ASSIGNMENT_API_CAP_USD)]

    @model_validator(mode="after")
    def check_deadline(self) -> Self:
        """Ensure a single request can fit within the input deadline."""

        if self.input_timeout_seconds < self.request_timeout_seconds:
            raise ValueError("Input timeout cannot be shorter than request timeout")

        return self


class ExperimentSelection(StrictModel):
    """References selecting one configured model, prompt and sampling variant."""

    model_id: Identifier
    prompt_id: Identifier
    sampling_id: Identifier


class ExperimentConfig(StrictModel):
    """Experiment definitions with unique IDs and checked default references."""

    version: Literal["experiment-v1"]
    models: Annotated[list[ModelConfig], Field(min_length=1)]
    prompts: Annotated[list[PromptConfig], Field(min_length=1)]
    sampling: Annotated[list[SamplingConfig], Field(min_length=1)]
    execution: ExecutionConfig
    selection: ExperimentSelection

    @model_validator(mode="after")
    def check_references(self) -> Self:
        """Reject duplicate IDs and references absent from the corresponding list."""

        groups = {
            "model": [model.id for model in self.models],
            "prompt": [prompt.id for prompt in self.prompts],
            "sampling": [sampling.id for sampling in self.sampling],
        }
        selected = {
            "model": self.selection.model_id,
            "prompt": self.selection.prompt_id,
            "sampling": self.selection.sampling_id,
        }

        for kind, identifiers in groups.items():
            if len(identifiers) != len(set(identifiers)):
                raise ValueError(f"Duplicate {kind} IDs")

            if selected[kind] not in identifiers:
                raise ValueError(f"Selected {kind} ID is not configured")

        return self
