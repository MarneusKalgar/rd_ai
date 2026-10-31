"""Failure shared by manifest and corpus artifact verification."""


class CorpusError(ValueError):
    """The corpus cannot be used as the approved benchmark."""
