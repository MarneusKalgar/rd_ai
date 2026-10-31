"""Process exit semantics shared by offline checks and selected extraction runs."""

from enum import IntEnum


class ExitStatus(IntEnum):
    SUCCESS = 0
    EXTRACTION_FAILURE = 1
    SETUP_FAILURE = 2
    INCOMPLETE = 3
    INTERRUPTED = 130
