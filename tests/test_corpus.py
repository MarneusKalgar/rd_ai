import hashlib
import json
from pathlib import Path
from typing import Any, Final

import pytest
from conftest import PROJECT_DIR

from extraction_service.corpus.loading import CorpusError, load_corpus

GOLD_PAIR_APPROVAL_METHOD: Final[str] = "explicit_conversation_approval_of_candidate_pairs"
NEUTRAL_INPUT_APPROVAL_METHOD: Final[str] = "explicit_conversation_approval_of_neutral_inputs"


@pytest.fixture
def corpus_manifests(project_copy: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    corpus = json.loads((project_copy / "data/corpus-manifest.json").read_text())
    gold = json.loads((project_copy / "data/manifest.json").read_text())

    return corpus, gold


def write_manifests(project: Path, corpus: dict[str, Any], gold: dict[str, Any]) -> None:
    """Rehash test manifests so semantic failures are not masked by hash errors."""

    gold_bytes = json.dumps(gold).encode("utf-8")
    (project / "data/manifest.json").write_bytes(gold_bytes)
    corpus["goldManifestSha256"] = hashlib.sha256(gold_bytes).hexdigest()
    (project / "data/corpus-manifest.json").write_text(json.dumps(corpus))


def test_complete_corpus_preserves_order_groups_and_separate_labels() -> None:
    manifest = json.loads((PROJECT_DIR / "data/corpus-manifest.json").read_text())
    expected_ids = [case["inputId"] for case in manifest["cases"]]

    corpus = load_corpus(PROJECT_DIR)

    actual_ids = [item.input_id for item in corpus.inputs]

    assert actual_ids == expected_ids
    assert len(corpus.inputs) == 30
    assert len(corpus.gold) == corpus.annotation_count == 10
    assert len({item.source_group for item in corpus.inputs}) == 30
    assert len({item.layout_group for item in corpus.inputs}) == 25
    assert sum(item.is_gold for item in corpus.inputs) == 10

    for item, case in zip(corpus.inputs, manifest["cases"], strict=True):
        expected_text = (PROJECT_DIR / "data" / case["inputFile"]).read_bytes().decode("utf-8")

        assert item.text == expected_text
        assert item.source_group == case["sourceGroup"]
        assert item.layout_group == case["layoutGroup"]
        assert item.input_sha256 == case["inputSha256"]
        assert item.language == case["language"]
        assert item.is_gold == (item.input_id in corpus.gold)
        assert not hasattr(item, "gold")
        assert not hasattr(item, "annotations")


@pytest.mark.parametrize("area", ["unlabeled_input", "gold", "annotation", "gold_manifest"])
def test_any_changed_artifact_fails_its_hash(project_copy: Path, area: str) -> None:
    corpus = json.loads((project_copy / "data/corpus-manifest.json").read_text())
    gold = json.loads((project_copy / "data/manifest.json").read_text())
    unlabeled = next(case for case in corpus["cases"] if case["labelStatus"] == "not_gold")
    paths = {
        "unlabeled_input": unlabeled["inputFile"],
        "gold": gold["cases"][0]["goldFile"],
        "annotation": gold["cases"][0]["annotationFile"],
        "gold_manifest": "manifest.json",
    }
    path = project_copy / "data" / paths[area]
    path.write_bytes(path.read_bytes() + b"\n")

    with pytest.raises(CorpusError, match="hash mismatch"):
        load_corpus(project_copy)


@pytest.mark.parametrize("field", ["inputId", "inputFile"])
def test_duplicate_inputs_do_not_hide_missing_cases(project_copy: Path, field: str) -> None:
    corpus = json.loads((project_copy / "data/corpus-manifest.json").read_text())
    gold = json.loads((project_copy / "data/manifest.json").read_text())
    corpus["cases"][1][field] = corpus["cases"][0][field]
    write_manifests(project_copy, corpus, gold)

    with pytest.raises(CorpusError, match="must be unique"):
        load_corpus(project_copy)


@pytest.mark.parametrize("field", ["sourceGroup", "layoutGroup", "language", "inputSha256"])
def test_corpus_gold_cross_references_are_checked_after_manifest_hashes_pass(
    project_copy: Path, field: str
) -> None:
    corpus = json.loads((project_copy / "data/corpus-manifest.json").read_text())
    gold = json.loads((project_copy / "data/manifest.json").read_text())
    gold["cases"][0][field] = "0" * 64 if field == "inputSha256" else "different"
    write_manifests(project_copy, corpus, gold)

    with pytest.raises(CorpusError, match="metadata mismatch"):
        load_corpus(project_copy)


@pytest.mark.parametrize("change", ["approval", "membership", "gold_duplicate", "gold_invalid"])
def test_semantically_invalid_corpus_is_rejected_with_matching_hashes(
    project_copy: Path, change: str
) -> None:
    corpus = json.loads((project_copy / "data/corpus-manifest.json").read_text())
    gold = json.loads((project_copy / "data/manifest.json").read_text())

    if change == "approval":
        corpus["cases"][0]["privacyReviewStatus"] = "unreviewed"
        expected = "privacyReviewStatus"
    elif change == "membership":
        gold["cases"][0]["inputId"] = "missing-input"
        expected = "membership differs"
    elif change == "gold_duplicate":
        gold["cases"][1] = gold["cases"][0].copy()
        expected = "must be unique"
    else:
        case = gold["cases"][0]
        gold_path = project_copy / "data" / case["goldFile"]
        gold_path.write_text("{}")
        case["goldSha256"] = hashlib.sha256(b"{}").hexdigest()

        for item in corpus["cases"]:
            if item["inputId"] == case["inputId"]:
                item["goldSha256"] = case["goldSha256"]

        expected = "Gold violates the extraction contract"

    write_manifests(project_copy, corpus, gold)

    with pytest.raises(CorpusError, match=expected):
        load_corpus(project_copy)


def test_manifest_paths_cannot_escape_the_data_directory(project_copy: Path) -> None:
    corpus = json.loads((project_copy / "data/corpus-manifest.json").read_text())
    gold = json.loads((project_copy / "data/manifest.json").read_text())
    unlabeled = next(case for case in corpus["cases"] if case["labelStatus"] == "not_gold")
    unlabeled["inputFile"] = "../private/customer.xlsx"
    write_manifests(project_copy, corpus, gold)

    with pytest.raises(CorpusError, match="within its owning directory"):
        load_corpus(project_copy)


def test_missing_input_is_a_setup_failure(project_copy: Path) -> None:
    corpus = json.loads((project_copy / "data/corpus-manifest.json").read_text())
    path = project_copy / "data" / corpus["cases"][-1]["inputFile"]
    path.unlink()

    with pytest.raises(CorpusError, match="Cannot read approved artifact"):
        load_corpus(project_copy)


def test_gold_approval_must_approve_candidate_pairs(
    project_copy: Path, corpus_manifests: tuple[dict[str, Any], dict[str, Any]]
) -> None:
    corpus, gold = corpus_manifests
    gold["approval"]["method"] = NEUTRAL_INPUT_APPROVAL_METHOD
    write_manifests(project_copy, corpus, gold)

    with pytest.raises(CorpusError, match="Gold approval must approve candidate pairs"):
        load_corpus(project_copy)


@pytest.mark.parametrize("area", ["inputs", "gold"])
def test_incomplete_manifests_cannot_pass_frozen_counts(
    project_copy: Path,
    corpus_manifests: tuple[dict[str, Any], dict[str, Any]],
    area: str,
) -> None:
    corpus, gold = corpus_manifests

    if area == "inputs":
        for case in corpus["cases"]:
            if case["labelStatus"] == "not_gold":
                corpus["cases"].remove(case)
                break
    else:
        removed = gold["cases"].pop()

        for case in corpus["cases"]:
            if case["inputId"] == removed["inputId"]:
                case["labelStatus"] = "not_gold"
                del case["goldFile"]
                del case["goldSha256"]
                break

    write_manifests(project_copy, corpus, gold)

    with pytest.raises(CorpusError, match="Frozen v1 requires 30 inputs and 10 gold cases"):
        load_corpus(project_copy)


@pytest.mark.parametrize("method", [GOLD_PAIR_APPROVAL_METHOD, NEUTRAL_INPUT_APPROVAL_METHOD])
def test_both_corpus_approval_methods_are_required(
    project_copy: Path,
    corpus_manifests: tuple[dict[str, Any], dict[str, Any]],
    method: str,
) -> None:
    corpus, gold = corpus_manifests
    retained_approvals: list[dict[str, Any]] = []

    for approval in corpus["approvals"]:
        if approval["method"] != method:
            retained_approvals.append(approval)

    corpus["approvals"] = retained_approvals
    write_manifests(project_copy, corpus, gold)

    with pytest.raises(CorpusError, match="both gold-pair and neutral-input approvals"):
        load_corpus(project_copy)


def test_corpus_and_gold_grouping_rules_must_agree(
    project_copy: Path, corpus_manifests: tuple[dict[str, Any], dict[str, Any]]
) -> None:
    corpus, gold = corpus_manifests
    gold["groupingRule"] = "A different evaluation split rule"
    write_manifests(project_copy, corpus, gold)

    with pytest.raises(CorpusError, match="Corpus and gold grouping rules differ"):
        load_corpus(project_copy)


@pytest.mark.parametrize(
    "target,schema_hash,expected_error",
    [
        ("gold_manifest", "0" * 64, "Gold approval does not name the current schema hash"),
        ("gold_manifest", None, "Gold approval does not name the current schema hash"),
        ("corpus_gold", "0" * 64, "Corpus gold-pair approval must name the approved schema hash"),
        ("corpus_gold", None, "Corpus gold-pair approval must name the approved schema hash"),
        ("corpus_neutral", "0" * 64, "Corpus approval names a different schema hash"),
    ],
)
def test_approvals_name_the_approved_schema(
    project_copy: Path,
    corpus_manifests: tuple[dict[str, Any], dict[str, Any]],
    target: str,
    schema_hash: str | None,
    expected_error: str,
) -> None:
    corpus, gold = corpus_manifests
    approvals_by_method = {approval["method"]: approval for approval in corpus["approvals"]}
    targets = {
        "gold_manifest": gold["approval"],
        "corpus_gold": approvals_by_method[GOLD_PAIR_APPROVAL_METHOD],
        "corpus_neutral": approvals_by_method[NEUTRAL_INPUT_APPROVAL_METHOD],
    }
    targets[target]["schemaSha256"] = schema_hash
    write_manifests(project_copy, corpus, gold)

    with pytest.raises(CorpusError, match=expected_error):
        load_corpus(project_copy)


def test_annotation_identity_is_checked_after_its_hash_passes(
    project_copy: Path, corpus_manifests: tuple[dict[str, Any], dict[str, Any]]
) -> None:
    corpus, gold = corpus_manifests
    case = gold["cases"][0]
    path = project_copy / "data" / case["annotationFile"]
    annotation = json.loads(path.read_text())
    annotation["inputId"] = "another-input"
    annotation_bytes = json.dumps(annotation).encode("utf-8")
    path.write_bytes(annotation_bytes)
    case["annotationSha256"] = hashlib.sha256(annotation_bytes).hexdigest()
    write_manifests(project_copy, corpus, gold)

    with pytest.raises(CorpusError, match="Annotation input identity differs"):
        load_corpus(project_copy)


def test_gold_line_count_matches_the_actual_ordered_lines(
    project_copy: Path, corpus_manifests: tuple[dict[str, Any], dict[str, Any]]
) -> None:
    corpus, gold = corpus_manifests
    gold_case = gold["cases"][0]
    gold_case["lineCount"] += 1

    for case in corpus["cases"]:
        if case["inputId"] == gold_case["inputId"]:
            case["lineCount"] = gold_case["lineCount"]

    write_manifests(project_copy, corpus, gold)

    with pytest.raises(CorpusError, match="Gold line count differs from manifest"):
        load_corpus(project_copy)


def test_gold_files_cannot_be_loaded_as_unlabeled_input_text(
    project_copy: Path, corpus_manifests: tuple[dict[str, Any], dict[str, Any]]
) -> None:
    corpus, gold = corpus_manifests
    gold_file = gold["cases"][0]["goldFile"]
    gold_bytes = (project_copy / "data" / gold_file).read_bytes()

    for case in corpus["cases"]:
        if case["labelStatus"] == "not_gold":
            case["inputFile"] = gold_file
            case["inputSha256"] = hashlib.sha256(gold_bytes).hexdigest()
            break

    write_manifests(project_copy, corpus, gold)

    with pytest.raises(CorpusError, match="Artifact must belong to the inputs directory"):
        load_corpus(project_copy)
