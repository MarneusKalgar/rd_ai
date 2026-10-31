"""Frozen corpus layout, approval protocol and cross-manifest identity fields."""

from typing import Final, Literal

CORPUS_MANIFEST_FILENAME: Final[str] = "corpus-manifest.json"
GOLD_MANIFEST_FILENAME: Final[str] = "manifest.json"
CORPUS_V1_INPUT_COUNT: Final[int] = 30
GOLD_V1_CASE_COUNT: Final[int] = 10

INPUTS_DIRECTORY: Final[str] = "inputs"
GOLD_DIRECTORY: Final[str] = "gold"
ANNOTATIONS_DIRECTORY: Final[str] = "annotations"
ORDER_LINES_FIELD: Final[str] = "lineItems"
ANNOTATION_INPUT_ID_FIELD: Final[str] = "inputId"

HUMAN_APPROVED: Final[Literal["human_approved"]] = "human_approved"
GOLD_PAIR_APPROVAL: Final[str] = "explicit_conversation_approval_of_candidate_pairs"
NEUTRAL_INPUT_APPROVAL: Final[str] = "explicit_conversation_approval_of_neutral_inputs"
REQUIRED_APPROVAL_METHODS: Final[frozenset[str]] = frozenset(
    (GOLD_PAIR_APPROVAL, NEUTRAL_INPUT_APPROVAL)
)

CASE_IDENTITY_FIELDS: Final[tuple[str, ...]] = (
    "input_id",
    "input_file",
    "input_sha256",
    "source_group",
    "layout_group",
    "language",
    "line_count",
    "gold_file",
    "gold_sha256",
)
