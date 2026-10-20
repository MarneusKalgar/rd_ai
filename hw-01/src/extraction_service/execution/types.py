"""Input and dependency identities without gold labels or application resources."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Self

from pydantic import AnyHttpUrl, model_validator

from extraction_service.configuration.models import SamplingConfig
from extraction_service.inference.types import ModelAdapter, ModelIdentity
from extraction_service.record_types import ExecutionStage, ModelRuntime
from extraction_service.runtime_types import Identifier, NonEmptyText, Sha256, StrictModel

if TYPE_CHECKING:
    from extraction_service.execution.pricing import VerifiedPricing
    from extraction_service.inference.errors import FailureEvidence
    from extraction_service.records import AttemptResult


class DependencyIdentity(StrictModel):
    """Canonical dependency key shared across prompt, sampling and model-ID aliases."""

    runtime: ModelRuntime
    endpoint: AnyHttpUrl
    model_name: Identifier
    serving_provider: NonEmptyText | None = None
    runtime_version: NonEmptyText | None = None
    model_digest: Sha256 | None = None

    @model_validator(mode="after")
    def check_endpoint(self) -> Self:
        """Keep credentials and unrelated URL components out of saved identities."""

        if self.endpoint.username or self.endpoint.password:
            raise ValueError("Dependency URLs cannot contain credentials")

        if self.endpoint.query or self.endpoint.fragment:
            raise ValueError("Dependency URLs cannot contain queries or fragments")

        if self.runtime == ModelRuntime.OPENROUTER and self.serving_provider is None:
            raise ValueError("Paid dependency identity requires the verified serving route")

        if self.runtime != ModelRuntime.OPENROUTER:
            if self.runtime_version is None or self.model_digest is None:
                raise ValueError("Local dependency identity requires installed version and digest")

        return self

    @classmethod
    def from_model(cls, endpoint: str, identity: ModelIdentity) -> Self:
        return cls(
            runtime=identity.runtime,
            endpoint=AnyHttpUrl(endpoint.rstrip("/") + "/"),
            model_name=identity.model_name,
            serving_provider=identity.serving_provider,
            runtime_version=identity.runtime_version,
            model_digest=identity.model_digest,
        )


@dataclass(frozen=True)
class ExecutionTarget:
    """An adapter borrowed from application setup, with its configured endpoint."""

    adapter: ModelAdapter
    endpoint: str

    @property
    def dependency(self) -> DependencyIdentity:
        return DependencyIdentity.from_model(self.endpoint, self.adapter.identity)


class ExtractionJob(StrictModel):
    """One selected input/prompt/sampling task; no labels or annotations are accepted."""

    run_id: Identifier
    input_id: Identifier
    input_sha256: Sha256
    source_text: NonEmptyText
    experiment_sha256: Sha256
    prompt_id: Identifier
    prompt_sha256: Sha256
    instructions: NonEmptyText
    sampling: SamplingConfig
    stage: ExecutionStage = ExecutionStage.MATRIX


@dataclass(frozen=True)
class ScheduledExtraction:
    """Application-selected work; listing candidates alone never schedules inference."""

    job: ExtractionJob
    target: ExecutionTarget
    pricing: VerifiedPricing | None = None


@dataclass
class InputExecution:
    """Invocation-local progress shared by orchestration and result construction."""

    scheduled: ScheduledExtraction
    started: float
    deadline: float
    attempts: list[AttemptResult] = field(default_factory=list)
    reason: str | None = None
    last_failure: FailureEvidence | None = None
    budget_stopped: bool = False
