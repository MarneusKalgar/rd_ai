"""Shared operational types; PO fields remain defined only by JSON Schema."""

from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, StringConstraints

type Identifier = Annotated[str, StringConstraints(pattern=r"^[A-Za-z0-9][A-Za-z0-9_.:/-]*$")]
type NonEmptyText = Annotated[str, StringConstraints(min_length=1, pattern=r"\S")]
type Sha256 = Annotated[str, StringConstraints(pattern=r"^[a-f0-9]{64}$")]
type NonNegativeFloat = Annotated[float, Field(ge=0, allow_inf_nan=False)]
type NonNegativeInt = Annotated[int, Field(ge=0)]
type PositiveFloat = Annotated[float, Field(gt=0, allow_inf_nan=False)]
type PositiveInt = Annotated[int, Field(gt=0)]


class StrictModel(BaseModel):
    """Reject coercion, unknown fields and non-finite operational numbers."""

    model_config = ConfigDict(
        strict=True,
        extra="forbid",
        frozen=True,
        allow_inf_nan=False,
        hide_input_in_errors=True,
        revalidate_instances="always",
    )
