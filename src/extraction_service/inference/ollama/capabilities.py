"""Verify the installed Ollama model and preserve its runtime identity."""

from extraction_service.configuration.models import ModelConfig
from extraction_service.inference.types import ModelIdentity
from extraction_service.record_types import ModelRuntime
from extraction_service.runtime_types import NonEmptyText, Sha256, StrictModel


class OllamaRuntime(StrictModel):
    """Identity read from the installed server and resolved model, without generation."""

    version: NonEmptyText
    model_name: NonEmptyText
    model_digest: Sha256
    capabilities: frozenset[str]

    def identity(self, config: ModelConfig, *, native: bool = False) -> ModelIdentity:
        """Require a matching installed text-completion model and preserve its digest."""

        if config.backend != "ollama" or config.model != self.model_name:
            raise ValueError("Installed Ollama model does not match configuration")

        if "completion" not in self.capabilities:
            raise ValueError("Installed Ollama model lacks text completion capability")

        return ModelIdentity(
            model_id=config.id,
            model_name=config.model,
            runtime=ModelRuntime.OLLAMA_NATIVE if native else ModelRuntime.OLLAMA_DOCKER,
            runtime_version=self.version,
            model_digest=self.model_digest,
        )
