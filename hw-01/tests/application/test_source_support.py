"""Source views preserve content and abstain before uncertain row exclusion."""

import json

import pytest

from extraction_service.application.persistence import reload_records
from extraction_service.configuration.loading import load_experiment
from extraction_service.extraction.validation import JsonObject
from extraction_service.source_support.cells import read_records, text_digest
from extraction_service.source_support.evidence import assess_order_evidence
from extraction_service.source_support.views import build_source_view, validate_source_view

from .conftest import ControlledService

SOURCE = (
    "ORDER!B4 Ügyfél neve: Test buyer\n"
    "ORDER!A21 Termék kódja: X | B21 Megnevezés: Package 20 kg | "
    "C21 Rendelt mennyiség: 2 | D21 Mértékegység: KG\n"
    "ORDER!A22 Termék kódja: Y | B22 Megnevezés: Catalog only | "
    "C22 Rendelt mennyiség: [blank] | D22 Mértékegység: KG\n"
)


def test_cell_records_preserve_grouping_literals_order_and_original_bytes() -> None:
    source = SOURCE.replace("\n", "\r\n") + "Unparsed | text with [blank] and 0"
    records = read_records(source)
    view = build_source_view(source, "cell-records-v1")

    assert "".join(record.original for record in records) == source
    assert len(view.source_map) == 4
    assert all(row["retained"] for row in view.source_map)
    assert "ORDER!C22 | Rendelt mennyiség | [blank]" in view.rendered_text
    assert "ORDER!B21 | Megnevezés | Package 20 kg" in view.rendered_text
    assert "Unparsed | text with [blank] and 0" in view.rendered_text
    assert view.selection is None
    assert (
        validate_source_view(
            json.loads(json.dumps(view.evidence())), "cell-records-v1", text_digest(source)
        )
        == view.rendered_text
    )


def test_sheet_inheritance_and_shared_header_coordinates_are_not_reassigned() -> None:
    records = read_records(
        "ORDER!A21 Code: X | OTHER!B7 Text: Other | C21 Quantity: 2 | D9 Unit: KG\n"
    )
    assert [cell.reference for cell in records[0].cells] == [
        "ORDER!A21",
        "OTHER!B7",
        "ORDER!C21",
        "ORDER!D9",
    ]


def test_order_selection_excludes_only_known_blank_catalog_rows_and_keeps_headers() -> None:
    view = build_source_view(SOURCE, "ordered-rows-v1")

    assert view.selection is not None and view.selection["applied"]
    assert view.selection["excluded_lines"] == (3,)
    assert "Test buyer" in view.rendered_text and "Package 20 kg" in view.rendered_text
    assert "Catalog only" not in view.rendered_text
    assert view.original_text == SOURCE
    assert len(view.source_map) == 3
    assert (
        validate_source_view(
            json.loads(json.dumps(view.evidence())), "ordered-rows-v1", text_digest(SOURCE)
        )
        == view.rendered_text
    )


@pytest.mark.parametrize("quantity", ["0", "-2", "2,5", "[missing]"])
def test_uncertain_quantities_abstain_without_removing_any_rows(quantity: str) -> None:
    source = SOURCE.replace("C21 Rendelt mennyiség: 2", f"C21 Rendelt mennyiség: {quantity}")
    view = build_source_view(source, "ordered-rows-v1")

    assert view.selection is not None and not view.selection["applied"]
    assert all(row["retained"] for row in view.source_map)
    assert "Catalog only" in view.rendered_text


def test_explicit_selection_with_blank_quantity_is_not_silently_removed() -> None:
    source = SOURCE.replace("D22 Mértékegység: KG", "D22 Mértékegység: KG | E22 Selected: yes")
    view = build_source_view(source, "ordered-rows-v1")

    assert view.selection is not None and not view.selection["applied"]
    assert view.selection["reason"] == "additional_item_evidence"
    assert "Catalog only" in view.rendered_text and "Selected | yes" in view.rendered_text


@pytest.mark.parametrize(
    "note",
    ["Free-text order instruction\n", "ORDER!H4 Special instructions: Order the marked rows\n"],
)
def test_unrecognized_order_instructions_preserve_the_full_source(note: str) -> None:
    view = build_source_view(SOURCE + note, "ordered-rows-v1")

    assert view.selection is not None and not view.selection["applied"]
    assert "Catalog only" in view.rendered_text


@pytest.mark.parametrize("defect", ["body", "original", "mapping", "selection", "identity"])
def test_source_view_rejects_tampering_even_with_updated_body_checksum(defect: str) -> None:
    evidence = json.loads(json.dumps(build_source_view(SOURCE, "cell-records-v1").evidence()))
    if defect == "body":
        evidence["rendered_text"] = evidence["rendered_text"].replace("Catalog only", "Changed")
        evidence["rendered_sha256"] = text_digest(evidence["rendered_text"])
    elif defect == "original":
        evidence["original_text"] += "changed"
    elif defect == "mapping":
        evidence["source_map"].pop()
    elif defect == "selection":
        evidence["selection"] = {"applied": True}
    else:
        evidence["identity"]["profile"] = "ordered-rows-v1"

    with pytest.raises(ValueError, match="Source view"):
        validate_source_view(evidence, "cell-records-v1", text_digest(SOURCE))


def test_completeness_and_quantity_candidates_detect_distinct_failures() -> None:
    correct: JsonObject = {
        "lineItems": [{"buyerProductName": "Package 20 kg", "buyerProductQuantity": "2"}]
    }
    supported = assess_order_evidence(SOURCE, correct)
    wrong_quantity: JsonObject = {
        "lineItems": [{"buyerProductName": "Package 20 kg", "buyerProductQuantity": "20"}]
    }
    missing: JsonObject = {
        "lineItems": [{"buyerProductName": "Catalog only", "buyerProductQuantity": None}]
    }

    assert supported["completeness"] == "supported"
    assert supported["quantity_findings"][0]["status"] == "supported"
    assert (
        assess_order_evidence(SOURCE, wrong_quantity)["quantity_findings"][0]["status"]
        == "contradicted"
    )
    assert assess_order_evidence(SOURCE, missing)["missing_source_rows"] == ["ORDER!21"]
    assert assess_order_evidence(SOURCE, None)["completeness"] == "unknown"
    assert assess_order_evidence("Unsupported source", correct)["completeness"] == "unknown"


def test_duplicate_names_keep_completeness_unknown() -> None:
    source = SOURCE.replace("Catalog only", "Package 20 kg")
    output: JsonObject = {
        "lineItems": [{"buyerProductName": "Package 20 kg", "buyerProductQuantity": "2"}]
    }

    result = assess_order_evidence(source, output)

    assert result["completeness"] == "unknown"
    assert result["quantity_findings"][0]["status"] == "unknown"


def test_unmatched_description_cannot_prove_an_ordered_row_is_missing() -> None:
    output: JsonObject = {
        "lineItems": [{"buyerProductName": "Paraphrased package", "buyerProductQuantity": "2"}]
    }

    result = assess_order_evidence(SOURCE, output)

    assert result["completeness"] == "unknown"
    assert result["missing_source_rows"] == []


def test_repeated_ordered_products_stay_separate() -> None:
    source = SOURCE.replace("Catalog only", "Package 20 kg").replace("[blank]", "3")
    view = build_source_view(source, "ordered-rows-v1")

    assert view.selection is not None and view.selection["applied"]
    assert view.selection["excluded_lines"] == ()
    assert view.rendered_text.count("| Megnevezés | Package 20 kg") == 2


def test_selection_keeps_shared_unit_when_only_blank_catalog_row_references_it() -> None:
    source = (
        "ORDER!C6 Order datum: 2026-08-31\n"
        "ORDER!E13 Artikelcode: X | C13 Omschrijving: Catalog | "
        "F13 Aantal: [blank] | F12 Eenheid: Dozen\n"
        "ORDER!E14 Artikelcode: Y | C14 Omschrijving: Ordered | F14 Aantal: 2\n"
    )
    view = build_source_view(source, "ordered-rows-v1")

    assert view.selection is not None and view.selection["applied"]
    assert "| Omschrijving | Catalog" not in view.rendered_text
    assert "ORDER!F12 | Eenheid | Dozen" in view.rendered_text
    assert view.source_map[1]["shared_context_references_preserved"] == ["ORDER!F12"]


def test_conflicting_shared_unit_abstains_instead_of_borrowing_a_value() -> None:
    source = (
        "ORDER!E13 Artikelcode: X | C13 Omschrijving: Catalog | "
        "F13 Aantal: [blank] | F12 Eenheid: Dozen\n"
        "ORDER!E14 Artikelcode: Y | C14 Omschrijving: Ordered | "
        "F14 Aantal: 2 | F12 Eenheid: Bottles\n"
    )
    view = build_source_view(source, "ordered-rows-v1")

    assert view.selection is not None and not view.selection["applied"]
    assert view.selection["reason"] == "conflicting_shared_cell"
    assert "| Omschrijving | Catalog" in view.rendered_text


def test_saved_source_assessment_needs_no_gold_and_makes_no_calls(
    service: ControlledService, gold: dict[str, object]
) -> None:
    service.responses = [json.dumps(gold)]
    result = service.invoke("run", "--run-id", "source-assess", "--input", "B02-S003-PO01")
    assert result.returncode == 0
    directory = service.project / "results/runs/source-assess"
    before = {path: path.read_bytes() for path in directory.rglob("*") if path.is_file()}
    for name in ("gold", "annotations"):
        for path in (service.project / "data" / name).rglob("*.json"):
            path.unlink()
    count = len(service.requests)

    assessed = service.invoke("assess-source", "source-assess", "--source", "runs")

    assert assessed.returncode == 0, assessed.stdout + assessed.stderr
    report = json.loads(assessed.stdout)
    assert report["gold_answers_read"] is False
    assert report["runs"][0]["records"][0]["evidence"]["completeness"] == "unknown"
    assert len(service.requests) == count
    assert before == {path: path.read_bytes() for path in directory.rglob("*") if path.is_file()}


def test_real_cli_records_transformed_source_and_keeps_raw_variant_separate(
    service: ControlledService, gold: dict[str, object]
) -> None:
    config = load_experiment(service.project / "config/experiments.yaml")
    (service.project / "config/view.json").write_text(
        config.model_copy(update={"source_view": "cell-records-v1"}).model_dump_json()
    )
    service.responses = [json.dumps(gold), json.dumps(gold)]
    original = service.invoke("run", "--run-id", "view-reference", "--input", "B02-S003-PO01")
    viewed = service.invoke(
        "run", "--config", "config/view.json", "--run-id", "view-cells", "--input", "B02-S003-PO01"
    )
    assert original.returncode == viewed.returncode == 0
    manifest, records = reload_records(service.project / "results/runs/view-cells")
    evidence = manifest.setup["source_views"]["B02-S003-PO01"]
    assert evidence["original_sha256"] == records[0].input_sha256
    assert evidence["rendered_sha256"] != records[0].input_sha256
    chats = [
        payload
        for path, payload, _ in service.requests
        if path == "/api/chat" and payload and not payload.get("_debug_render_only")
    ]
    assert chats[-1]["messages"][1]["content"] == evidence["rendered_text"]
    evaluated = service.invoke("evaluate", "view-reference", "view-cells")
    assert evaluated.returncode == 0
    assert len(json.loads(evaluated.stdout)["variants"]) == 2


def test_hybrid_keeps_recognized_selection_body_but_has_separate_identity() -> None:
    selected = build_source_view(SOURCE, "ordered-rows-v1")
    hybrid = build_source_view(SOURCE, "ordered-rows-raw-fallback-v1")

    assert hybrid.selection is not None and hybrid.selection["applied"]
    assert hybrid.rendered_text == selected.rendered_text
    assert hybrid.source_map == selected.source_map
    assert hybrid.selection == selected.selection
    assert hybrid.evidence()["identity"] != selected.evidence()["identity"]


def test_hybrid_unknown_layout_preserves_raw_bytes_including_line_endings() -> None:
    source = "ORDER!A1 Unknown label: café\r\n\r\nUnparsed | [blank] | 0"
    hybrid = build_source_view(source, "ordered-rows-raw-fallback-v1")

    assert hybrid.selection is not None and not hybrid.selection["applied"]
    assert hybrid.rendered_text.encode() == source.encode()
    assert hybrid.evidence()["rendered_sha256"] == text_digest(source)
    assert all(row["retained"] for row in hybrid.source_map)
    reloaded = validate_source_view(
        json.loads(json.dumps(hybrid.evidence())),
        "ordered-rows-raw-fallback-v1",
        text_digest(source),
    )
    assert reloaded == source


@pytest.mark.parametrize("quantity", ["0", "-2", "2,5", "[missing]"])
def test_hybrid_uncertain_quantity_retains_exact_raw_source(quantity: str) -> None:
    source = SOURCE.replace("C21 Rendelt mennyiség: 2", f"C21 Rendelt mennyiség: {quantity}")
    hybrid = build_source_view(source, "ordered-rows-raw-fallback-v1")

    assert hybrid.selection is not None and not hybrid.selection["applied"]
    assert hybrid.rendered_text == source
    assert all(row["retained"] for row in hybrid.source_map)


def test_hybrid_explicit_order_mark_with_blank_quantity_preserves_raw_evidence() -> None:
    source = SOURCE.replace("D22 Mértékegység: KG", "D22 Mértékegység: KG | E22 Selected: yes")
    hybrid = build_source_view(source, "ordered-rows-raw-fallback-v1")

    assert hybrid.selection is not None and not hybrid.selection["applied"]
    assert hybrid.rendered_text == source
    assert "C22 Rendelt mennyiség: [blank]" in hybrid.rendered_text


def test_hybrid_rejects_reformatted_fallback_even_with_updated_checksum() -> None:
    source = "Unsupported raw source\r\n"
    evidence = json.loads(
        json.dumps(build_source_view(source, "ordered-rows-raw-fallback-v1").evidence())
    )
    evidence["rendered_text"] = "Unsupported raw source\n"
    evidence["rendered_sha256"] = text_digest(evidence["rendered_text"])

    with pytest.raises(ValueError, match="declared source transformation"):
        validate_source_view(evidence, "ordered-rows-raw-fallback-v1", text_digest(source))


def test_hybrid_cli_sends_raw_fallback_and_remains_separate_from_raw_variant(
    service: ControlledService, gold: dict[str, object]
) -> None:
    config = load_experiment(service.project / "config/experiments.yaml")
    (service.project / "config/hybrid.json").write_text(
        config.model_copy(update={"source_view": "ordered-rows-raw-fallback-v1"}).model_dump_json()
    )
    service.responses = [json.dumps(gold), json.dumps(gold)]
    raw = service.invoke("run", "--run-id", "hybrid-raw", "--input", "B02-S003-PO01")
    hybrid = service.invoke(
        "run",
        "--config",
        "config/hybrid.json",
        "--run-id",
        "hybrid-view",
        "--input",
        "B02-S003-PO01",
    )

    assert raw.returncode == hybrid.returncode == 0
    manifest, records = reload_records(service.project / "results/runs/hybrid-view")
    evidence = manifest.setup["source_views"]["B02-S003-PO01"]
    assert not evidence["selection"]["applied"]
    assert evidence["original_sha256"] == evidence["rendered_sha256"] == records[0].input_sha256
    chats = [
        payload
        for path, payload, _ in service.requests
        if path == "/api/chat" and payload and not payload.get("_debug_render_only")
    ]
    assert chats[-1]["messages"][1]["content"] == evidence["original_text"]
    assert chats[-1]["messages"] == chats[-2]["messages"]
    evaluated = service.invoke("evaluate", "hybrid-raw", "hybrid-view")
    assert evaluated.returncode == 0
    assert len(json.loads(evaluated.stdout)["variants"]) == 2
