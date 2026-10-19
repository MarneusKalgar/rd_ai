import hashlib
import json
from pathlib import Path
from typing import Any

import pytest
from conftest import PROJECT_DIR

from hw01.corpus.loading import CorpusError, load_corpus


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


def test_manifest_paths_cannot_escape_the_public_input_directory(project_copy: Path) -> None:
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
