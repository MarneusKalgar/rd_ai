"""Read approved inputs, gold labels and current annotation artifacts."""

from pathlib import Path

from extraction_service.artifacts import artifact_path, read_checked
from extraction_service.corpus.constants import (
    ANNOTATION_INPUT_ID_FIELD,
    ANNOTATIONS_DIRECTORY,
    GOLD_DIRECTORY,
    INPUTS_DIRECTORY,
    ORDER_LINES_FIELD,
)
from extraction_service.corpus.errors import CorpusError
from extraction_service.corpus.manifests import check_case_link
from extraction_service.corpus.models import CorpusCase, GoldCase
from extraction_service.extraction import ExtractionContract
from extraction_service.extraction.json_parsing import parse_json
from extraction_service.extraction.validation import JsonObject


def _data_path(data_dir: Path, relative_path: str, area: str) -> Path:
    path = artifact_path(data_dir, relative_path)
    area_dir = (data_dir / area).resolve()

    if not path.is_relative_to(area_dir):
        raise CorpusError(f"Artifact must belong to the {area} directory")

    return path


def read_input(data_dir: Path, case: CorpusCase) -> str:
    """Read one neutral input with checked bytes and a nonempty text guard."""

    path = _data_path(data_dir, case.input_file, INPUTS_DIRECTORY)
    text = read_checked(path, case.input_sha256)

    if not text.strip():
        raise CorpusError(f"Input is empty: {case.input_id}")

    return text


def check_annotation(data_dir: Path, case: GoldCase) -> None:
    """Check current annotation bytes and identity without interpreting labels."""

    path = _data_path(data_dir, case.annotation_file, ANNOTATIONS_DIRECTORY)
    # originalAnnotationSha256 documents history; only annotationSha256
    # describes the current bytes shipped with this corpus.
    text = read_checked(path, case.annotation_sha256)
    annotation = parse_json(text)

    if (
        not isinstance(annotation, dict)
        or annotation.get(ANNOTATION_INPUT_ID_FIELD) != case.input_id
    ):
        raise CorpusError(f"Annotation input identity differs: {case.input_id}")


def read_gold(data_dir: Path, case: GoldCase, contract: ExtractionContract) -> JsonObject:
    """Validate an approved gold PO, its ordered-line count and annotation."""

    path = _data_path(data_dir, case.gold_file, GOLD_DIRECTORY)
    raw_gold = read_checked(path, case.gold_sha256)
    outcome = contract.validate_json(raw_gold)

    if not outcome.is_valid or outcome.value is None:
        raise CorpusError(f"Gold violates the extraction contract: {case.input_id}")

    lines = outcome.value[ORDER_LINES_FIELD]

    if not isinstance(lines, list) or len(lines) != case.line_count:
        raise CorpusError(f"Gold line count differs from manifest: {case.input_id}")

    check_annotation(data_dir, case)

    return outcome.value


def read_case_gold(
    data_dir: Path,
    case: CorpusCase,
    gold_case: GoldCase | None,
    contract: ExtractionContract,
) -> JsonObject | None:
    """Load a linked approved label while keeping unlabeled cases unlabeled."""

    if gold_case is None:
        return None

    check_case_link(case, gold_case)

    return read_gold(data_dir, gold_case, contract)
