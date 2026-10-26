"""Role facts cannot promote catalog rows or turn uncertain membership into a filter."""

import json

import pytest

from extraction_service.application.persistence import reload_records
from extraction_service.configuration.loading import load_experiment
from extraction_service.source_support.cells import text_digest
from extraction_service.source_support.field_roles import render_field_role_cues
from extraction_service.source_support.views import build_source_view, validate_source_view

from .conftest import ControlledService

SOURCE = (
    "ORDER!B4 Ügyfél neve: Test buyer\n"
    "ORDER!B15 Delivery date: 2026-09-30\n"
    "ORDER!A21 Termék kódja: ORD-123 | B21 Megnevezés: Ordered product | "
    "C21 Rendelt mennyiség: 2 | D21 Mértékegység: KG\n"
    "ORDER!A22 Termék kódja: CAT-456 | B22 Megnevezés: Catalog product | "
    "C22 Rendelt mennyiség: [blank] | D22 Mértékegység: KG\n"
)


def test_confirmed_scope_omits_catalog_facts_and_preserves_hybrid_body() -> None:
    hybrid = build_source_view(SOURCE, "ordered-rows-raw-fallback-v1")
    scoped = build_source_view(SOURCE, "ordered-rows-scoped-roles-v1")

    assert scoped.field_roles is not None and scoped.field_roles["cue_applied"]
    assert scoped.rendered_text == hybrid.rendered_text + scoped.field_roles["cue_text"]
    assert scoped.field_roles["scope"]["product_cells"] == ["ORDER!B21"]
    assert len(scoped.field_roles["source"]["rows"]) == 1
    assert "CAT-456" not in json.dumps(scoped.field_roles)
    assert "Catalog product" not in json.dumps(scoped.field_roles)
    assert scoped.original_text == SOURCE and "Catalog product" in scoped.original_text
    assert scoped.source_map == hybrid.source_map


def test_catalog_buyer_codes_are_true_facts_without_confirmed_order_membership() -> None:
    source = (
        "ORDER!A10 Article code: X | B10 Description: Ordered | C10 Quantity: 2 | "
        "D10 Buyer product code: 0001 | E10 Delivery date: 2026-09-22\n"
        "ORDER!A11 Article code: Y | B11 Description: Catalog | C11 Quantity: [blank] | "
        "D11 Buyer product code: 0002\n"
    )
    unscoped, _ = render_field_role_cues(source)
    scoped = build_source_view(source, "ordered-rows-scoped-roles-v1")

    assert unscoped is not None and "0002" in unscoped
    assert scoped.field_roles is not None and not scoped.field_roles["cue_applied"]
    assert scoped.field_roles["scope"]["reason"] == "unknown_order_membership"
    assert scoped.rendered_text == source
    assert "0001" in scoped.rendered_text and "2026-09-22" in scoped.rendered_text


def test_catalog_role_labels_do_not_expand_existing_selection_rules() -> None:
    source = SOURCE.replace(
        "D22 Mértékegység: KG", "D22 Mértékegység: KG | E22 Buyer product code: BUY-CATALOG"
    )
    scoped = build_source_view(source, "ordered-rows-scoped-roles-v1")

    assert scoped.selection is not None and not scoped.selection["applied"]
    assert scoped.field_roles is not None and not scoped.field_roles["cue_applied"]
    assert scoped.rendered_text == source


def test_marked_order_with_unknown_quantity_is_retained_without_cues() -> None:
    source = SOURCE.replace("D22 Mértékegység: KG", "D22 Mértékegység: KG | E22 Selected: yes")
    scoped = build_source_view(source, "ordered-rows-scoped-roles-v1")

    assert scoped.field_roles is not None and not scoped.field_roles["cue_applied"]
    assert scoped.rendered_text == source
    assert "C22 Rendelt mennyiség: [blank]" in scoped.rendered_text
    assert all(item["retained"] for item in scoped.source_map)


def test_ambiguous_products_keep_both_ordered_rows_without_role_cues() -> None:
    source = SOURCE.replace("Catalog product", "Ordered product").replace("[blank]", "3")
    hybrid = build_source_view(source, "ordered-rows-raw-fallback-v1")
    scoped = build_source_view(source, "ordered-rows-scoped-roles-v1")

    assert scoped.selection is not None and scoped.selection["applied"]
    assert scoped.field_roles is not None and not scoped.field_roles["cue_applied"]
    assert scoped.field_roles["scope"]["reason"] == "ambiguous_scoped_products"
    assert scoped.rendered_text == hybrid.rendered_text
    assert scoped.rendered_text.count("| Megnevezés | Ordered product") == 2


def test_ambiguous_source_coordinates_cannot_authorize_a_scope() -> None:
    source = SOURCE.replace("22", "21")
    scoped = build_source_view(source, "ordered-rows-scoped-roles-v1")

    assert scoped.selection is not None and not scoped.selection["applied"]
    assert scoped.field_roles is not None and not scoped.field_roles["cue_applied"]
    assert scoped.rendered_text == source


def test_scope_certificate_tampering_is_rejected() -> None:
    evidence = json.loads(
        json.dumps(build_source_view(SOURCE, "ordered-rows-scoped-roles-v1").evidence())
    )
    evidence["field_roles"]["scope"]["product_cells"] = ["ORDER!B22"]

    with pytest.raises(ValueError, match="field-role evidence differs"):
        validate_source_view(evidence, "ordered-rows-scoped-roles-v1", text_digest(SOURCE))


def test_real_cli_keeps_unsupported_raw_body_and_scoped_variant_separate(
    service: ControlledService, gold: dict[str, object]
) -> None:
    config = load_experiment(service.project / "config/experiments.yaml")
    (service.project / "config/scoped.json").write_text(
        config.model_copy(update={"source_view": "ordered-rows-scoped-roles-v1"}).model_dump_json()
    )
    service.responses = [json.dumps(gold), json.dumps(gold)]
    raw = service.invoke("run", "--run-id", "scope-raw", "--input", "B02-S003-PO01")
    scoped = service.invoke(
        "run", "--config", "config/scoped.json", "--run-id", "scope-new", "--input", "B02-S003-PO01"
    )

    assert raw.returncode == scoped.returncode == 0
    manifest, _ = reload_records(service.project / "results/runs/scope-new")
    evidence = manifest.setup["source_views"]["B02-S003-PO01"]
    assert not evidence["field_roles"]["cue_applied"]
    chats = [
        payload
        for path, payload, _ in service.requests
        if path == "/api/chat" and payload and not payload.get("_debug_render_only")
    ]
    assert chats[-1]["messages"] == chats[-2]["messages"]
    assert chats[-1]["messages"][1]["content"] == evidence["original_text"]
    evaluated = service.invoke("evaluate", "scope-raw", "scope-new")
    assert evaluated.returncode == 0
    assert len(json.loads(evaluated.stdout)["variants"]) == 2
