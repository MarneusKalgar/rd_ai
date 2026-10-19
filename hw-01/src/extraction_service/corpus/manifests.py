"""Read and cross-check frozen manifests before loading corpus artifacts."""

from dataclasses import dataclass
from pathlib import Path

from extraction_service.artifacts import artifact_path, read_checked, read_text
from extraction_service.corpus.constants import (
    CASE_IDENTITY_FIELDS,
    CORPUS_MANIFEST_FILENAME,
    CORPUS_V1_INPUT_COUNT,
    GOLD_PAIR_APPROVAL,
    GOLD_V1_CASE_COUNT,
    HUMAN_APPROVED,
    REQUIRED_APPROVAL_METHODS,
)
from extraction_service.corpus.errors import CorpusError
from extraction_service.corpus.models import CorpusCase, CorpusManifest, GoldCase, GoldManifest
from extraction_service.extraction.json_parsing import parse_json


@dataclass(frozen=True)
class ApprovedManifests:
    """Related corpus/gold metadata after consistency and approval checks."""

    corpus: CorpusManifest
    gold: GoldManifest
    gold_by_id: dict[str, GoldCase]


def _check_counts_and_uniqueness(corpus: CorpusManifest, gold: GoldManifest) -> None:
    if len(corpus.cases) != CORPUS_V1_INPUT_COUNT or len(gold.cases) != GOLD_V1_CASE_COUNT:
        raise CorpusError("Frozen v1 requires 30 inputs and 10 gold cases")

    input_ids = [case.input_id for case in corpus.cases]
    input_files = [case.input_file for case in corpus.cases]
    gold_ids = [case.input_id for case in gold.cases]
    gold_files = [case.gold_file for case in gold.cases]
    annotation_files = [case.annotation_file for case in gold.cases]

    if len(set(input_ids)) != len(input_ids) or len(set(input_files)) != len(input_files):
        raise CorpusError("Corpus input IDs and files must be unique")

    if len(set(gold_ids)) != len(gold_ids) or len(set(gold_files)) != len(gold_files):
        raise CorpusError("Gold input IDs and files must be unique")

    if len(set(annotation_files)) != len(annotation_files):
        raise CorpusError("Annotation files must be unique")


def _check_membership(corpus: CorpusManifest, gold_by_id: dict[str, GoldCase]) -> None:
    approved_ids: set[str] = set()

    for case in corpus.cases:
        if case.label_status == HUMAN_APPROVED:
            approved_ids.add(case.input_id)

    if approved_ids != set(gold_by_id):
        raise CorpusError("Corpus gold membership differs from the gold manifest")


def _check_approvals(corpus: CorpusManifest, gold: GoldManifest) -> None:
    if corpus.grouping_rule != gold.grouping_rule:
        raise CorpusError("Corpus and gold grouping rules differ")

    if gold.approval.schema_sha256 != gold.schema_sha256:
        raise CorpusError("Gold approval does not name the current schema hash")

    methods = {approval.method for approval in corpus.approvals}

    if methods != REQUIRED_APPROVAL_METHODS:
        raise CorpusError("Corpus requires both gold-pair and neutral-input approvals")

    for approval in corpus.approvals:
        if approval.method == GOLD_PAIR_APPROVAL and approval.schema_sha256 != gold.schema_sha256:
            raise CorpusError("Corpus gold-pair approval must name the approved schema hash")

        if approval.schema_sha256 is not None and approval.schema_sha256 != gold.schema_sha256:
            raise CorpusError("Corpus approval names a different schema hash")


def load_manifests(data_dir: Path) -> ApprovedManifests:
    """Verify the manifest hash chain, identity sets and recorded approvals."""

    corpus_text = read_text(data_dir / CORPUS_MANIFEST_FILENAME)
    corpus = CorpusManifest.model_validate(parse_json(corpus_text))
    gold_path = artifact_path(data_dir, corpus.gold_manifest)
    gold_text = read_checked(gold_path, corpus.gold_manifest_sha256)
    gold = GoldManifest.model_validate(parse_json(gold_text))

    _check_counts_and_uniqueness(corpus, gold)
    gold_by_id = {case.input_id: case for case in gold.cases}
    _check_membership(corpus, gold_by_id)
    _check_approvals(corpus, gold)

    return ApprovedManifests(corpus=corpus, gold=gold, gold_by_id=gold_by_id)


def check_case_link(case: CorpusCase, gold_case: GoldCase) -> None:
    """Compare the identity and provenance fields shared by the two manifests."""

    for field_name in CASE_IDENTITY_FIELDS:
        if getattr(case, field_name) != getattr(gold_case, field_name):
            raise CorpusError(f"Corpus/gold metadata mismatch: {case.input_id}, {field_name}")
