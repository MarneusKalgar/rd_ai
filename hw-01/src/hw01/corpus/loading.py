"""Coordinate complete corpus verification before any model request is possible."""

import json
from dataclasses import dataclass
from pathlib import Path

from pydantic import ValidationError

from hw01.artifacts import ArtifactError
from hw01.corpus.errors import CorpusError as CorpusError
from hw01.corpus.files import read_case_gold, read_input
from hw01.corpus.manifests import load_manifests
from hw01.corpus.models import CorpusCase, GoldCase
from hw01.extraction import ExtractionContract
from hw01.extraction.constants import SCHEMA_FILENAME
from hw01.extraction.json_parsing import AmbiguousJsonError
from hw01.extraction.validation import JsonObject


@dataclass(frozen=True)
class CorpusInput:
    """Model-facing neutral text and provenance, without gold or annotation text."""

    input_id: str
    text: str
    input_sha256: str
    source_group: str
    layout_group: str
    language: str
    is_gold: bool


@dataclass(frozen=True)
class LoadedCorpus:
    """Verified inputs and separately held evaluation objects under one contract."""

    inputs: tuple[CorpusInput, ...]
    gold: dict[str, JsonObject]
    contract: ExtractionContract
    annotation_count: int
    version: str


def load_corpus(project_dir: Path) -> LoadedCorpus:
    """Verify manifests, load neutral inputs and validate every linked gold PO.

    Returns:
        Ordered model-facing inputs, separate gold values and one reusable contract.

    Raises:
        CorpusError: Manifest metadata, links, artifacts or gold validation fail.
        ContractLoadError: The approved extraction schema cannot be loaded.
    """

    data_dir = project_dir / "data"

    try:
        manifests = load_manifests(data_dir)
        contract = ExtractionContract.load(
            project_dir / "schemas" / SCHEMA_FILENAME,
            expected_sha256=manifests.gold.schema_sha256,
        )
        inputs, gold_values = _load_cases(
            data_dir, manifests.corpus.cases, manifests.gold_by_id, contract
        )
    except (ArtifactError, ValidationError, AmbiguousJsonError, json.JSONDecodeError) as error:
        raise CorpusError(str(error)) from error

    return LoadedCorpus(
        inputs=inputs,
        gold=gold_values,
        contract=contract,
        annotation_count=len(gold_values),
        version=manifests.corpus.version,
    )


def _load_cases(
    data_dir: Path,
    cases: list[CorpusCase],
    gold_by_id: dict[str, GoldCase],
    contract: ExtractionContract,
) -> tuple[tuple[CorpusInput, ...], dict[str, JsonObject]]:
    inputs: list[CorpusInput] = []
    gold_values: dict[str, JsonObject] = {}

    for case in cases:
        text = read_input(data_dir, case)
        gold_case = gold_by_id.get(case.input_id)
        gold_value = read_case_gold(data_dir, case, gold_case, contract)

        if gold_value is not None:
            gold_values[case.input_id] = gold_value

        inputs.append(
            CorpusInput(
                input_id=case.input_id,
                text=text,
                input_sha256=case.input_sha256,
                source_group=case.source_group,
                layout_group=case.layout_group,
                language=case.language,
                is_gold=gold_case is not None,
            )
        )

    return tuple(inputs), gold_values
