"""Manifest metadata models; these do not define purchase-order output fields."""

from typing import Literal, Self

from pydantic import ConfigDict, model_validator
from pydantic.alias_generators import to_camel

from extraction_service.runtime_types import (
    Identifier,
    NonEmptyText,
    PositiveInt,
    Sha256,
    StrictModel,
)


class ManifestModel(StrictModel):
    """Accept the existing manifest's camelCase keys without renaming its files."""

    model_config = ConfigDict(alias_generator=to_camel)


class Approval(ManifestModel):
    """Recorded human approval, distinct from agent annotation authorship."""

    reviewer: Literal["user"]
    date: NonEmptyText
    method: Literal[
        "explicit_conversation_approval_of_candidate_pairs",
        "explicit_conversation_approval_of_neutral_inputs",
    ]
    statement: NonEmptyText
    scope: NonEmptyText
    schema_sha256: Sha256 | None = None


class CorpusCase(ManifestModel):
    """One approved logical input, optionally linked to an approved gold object."""

    input_id: Identifier
    input_file: NonEmptyText
    input_sha256: Sha256
    source_group: Identifier
    layout_group: Identifier
    language: Identifier
    line_count: PositiveInt
    privacy_review_status: Literal["human_approved"]
    label_status: Literal["human_approved", "not_gold"]
    gold_file: NonEmptyText | None = None
    gold_sha256: Sha256 | None = None

    @model_validator(mode="after")
    def check_gold_membership(self) -> Self:
        """Do not turn approved text or a partial link into an approved label."""

        has_gold = self.gold_file is not None and self.gold_sha256 is not None
        has_any_gold = self.gold_file is not None or self.gold_sha256 is not None

        if self.label_status == "human_approved" and not has_gold:
            raise ValueError("Approved labels require a complete gold link")

        if self.label_status == "not_gold" and has_any_gold:
            raise ValueError("Unlabeled inputs cannot carry gold links")

        return self


class GoldCase(ManifestModel):
    """Approved label and its current annotation hash, retaining historical metadata."""

    input_id: Identifier
    input_file: NonEmptyText
    gold_file: NonEmptyText
    annotation_file: NonEmptyText
    source_group: Identifier
    layout_group: Identifier
    language: Identifier
    line_count: PositiveInt
    review_status: Literal["human_approved"]
    input_sha256: Sha256
    gold_sha256: Sha256
    annotation_sha256: Sha256
    original_annotation_sha256: Sha256


class AnnotationDocumentation(ManifestModel):
    """Agent-written explanations do not add another human labeling pass."""

    author: Literal["agent"]
    date: NonEmptyText
    scope: NonEmptyText


class CorpusManifest(ManifestModel):
    """The frozen corpus-v1 manifest."""

    version: Literal["corpus-v1"]
    gold_manifest: Literal["manifest.json"]
    gold_manifest_sha256: Sha256
    approvals: list[Approval]
    grouping_rule: NonEmptyText
    cases: list[CorpusCase]


class GoldManifest(ManifestModel):
    """The frozen gold-v1 manifest and annotation documentation revision."""

    version: Literal["gold-v1"]
    schema_sha256: Sha256
    approval: Approval
    grouping_rule: NonEmptyText
    cases: list[GoldCase]
    annotation_revision: Literal[2]
    annotation_documentation: AnnotationDocumentation
