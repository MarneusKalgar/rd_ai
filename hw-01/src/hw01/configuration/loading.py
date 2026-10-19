"""Load safe experiment YAML without silently overwriting duplicate keys."""

from pathlib import Path
from typing import Any

import yaml
from yaml.nodes import MappingNode

from hw01.artifacts import read_text
from hw01.configuration.models import ExperimentConfig


class ConfigurationError(ValueError):
    """Experiment configuration cannot be loaded."""


class UniqueKeyLoader(yaml.SafeLoader):
    """Safe YAML construction that refuses duplicate or unhashable keys."""

    def construct_mapping(self, node: MappingNode, deep: bool = False) -> dict[Any, Any]:
        self.flatten_mapping(node)
        result: dict[Any, Any] = {}

        for key_node, value_node in node.value:
            key = self.construct_object(key_node, deep=deep)

            try:
                duplicate = key in result
            except TypeError as error:
                raise ConfigurationError("YAML mapping keys must be scalar values") from error

            if duplicate:
                raise ConfigurationError("Duplicate YAML mapping key")

            result[key] = self.construct_object(value_node, deep=deep)

        return result


def load_experiment(path: Path) -> ExperimentConfig:
    """Load YAML then validate its complete operational shape without coercion.

    Raises:
        ConfigurationError: YAML syntax or mapping keys are invalid.
        ArtifactError: The file cannot be read.
        pydantic.ValidationError: Values violate experiment constraints.
    """

    raw_configuration = read_text(path)

    try:
        parsed = yaml.load(raw_configuration, Loader=UniqueKeyLoader)
    except yaml.YAMLError as error:
        raise ConfigurationError("Invalid experiment YAML") from error

    return ExperimentConfig.model_validate(parsed)
