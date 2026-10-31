"""Controlled, credential-free setup failures safe for the command boundary."""


class SetupError(ValueError):
    """Expected setup failure with an actionable message written by this application."""
