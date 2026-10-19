"""Recognized wire values; raw finish-reason fields remain open to unknown strings."""

from typing import Final

STOP_FINISH_REASON: Final[str] = "stop"
LENGTH_FINISH_REASON: Final[str] = "length"
ERROR_FINISH_REASON: Final[str] = "error"
CONTENT_FILTER_FINISH_REASON: Final[str] = "content_filter"
