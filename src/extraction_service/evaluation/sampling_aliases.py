"""Explicit ID-only aliases for offline grouping; generation records stay unchanged."""

from typing import Literal, Self

from pydantic import Field, model_validator

from extraction_service.configuration.models import SamplingConfig
from extraction_service.runtime_types import StrictModel


class SamplingAlias(StrictModel):
    """One source-to-target naming change with identical generation controls."""

    source: SamplingConfig
    target: SamplingConfig

    @model_validator(mode="after")
    def check_controls(self) -> Self:
        if self.source.id == self.target.id:
            raise ValueError("Sampling alias requires different IDs")

        if self.source.model_dump(exclude={"id"}) != self.target.model_dump(exclude={"id"}):
            raise ValueError("Sampling alias cannot change generation controls")

        return self


class SamplingAliases(StrictModel):
    """Unambiguous offline mappings without chaining or conflicting target settings."""

    version: Literal["sampling-aliases-v1"] = "sampling-aliases-v1"
    aliases: list[SamplingAlias] = Field(min_length=1)

    @model_validator(mode="after")
    def check_mapping(self) -> Self:
        sources = [alias.source.id for alias in self.aliases]
        targets = {alias.target.id for alias in self.aliases}

        if len(sources) != len(set(sources)) or set(sources) & targets:
            raise ValueError("Sampling aliases require unique sources and no chains")

        definitions: dict[str, SamplingConfig] = {}
        for alias in self.aliases:
            previous = definitions.get(alias.target.id)
            if previous is not None and previous != alias.target:
                raise ValueError("Sampling target ID has conflicting controls")
            definitions[alias.target.id] = alias.target

        return self

    def canonical(self, sampling: SamplingConfig) -> SamplingConfig:
        """Validate source values before substituting a grouping-only target ID."""

        for alias in self.aliases:
            if sampling.id == alias.source.id:
                if sampling != alias.source:
                    raise ValueError("Saved sampling differs from the declared alias source")

                return alias.target.model_copy(deep=True)

            if sampling.id == alias.target.id and sampling != alias.target:
                raise ValueError("Saved sampling differs from the declared alias target")

        return sampling
