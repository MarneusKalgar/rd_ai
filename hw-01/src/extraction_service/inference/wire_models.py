"""Shared validation policy for known fields in evolving provider envelopes."""

from pydantic import ConfigDict

from extraction_service.runtime_types import StrictModel


class WireModel(StrictModel):
    """Strict known wire fields; evolving remote extras remain in raw HTTP evidence."""

    model_config = ConfigDict(extra="allow")
