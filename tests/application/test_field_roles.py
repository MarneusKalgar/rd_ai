"""Field-role checks use source scope, preserve legitimate values and abstain."""

import json
from copy import deepcopy

import pytest

from extraction_service.application.persistence import reload_records
from extraction_service.configuration.loading import load_experiment
from extraction_service.extraction.validation import JsonObject
from extraction_service.source_support.cells import text_digest
from extraction_service.source_support.field_roles import assess_field_roles, render_field_role_cues
from extraction_service.source_support.views import build_source_view, validate_source_view

from .conftest import ControlledService

SOURCE = (
    "ORDER!B2 Delivery date: 2026-09-30\n"
    "ORDER!A10 Article code: 00123 | B10 Description: First product | C10 Quantity: 2\n"
    "ORDER!A11 Article code: 00456 | B11 Description: Second product | C11 Quantity: 3 | "
    "D11 Buyer product code: 0007-X | E11 Delivery date: 2026-09-22\n"
)


def output() -> JsonObject:
    return {
        "lineItems": [
            {
                "buyerProductName": "First product",
                "buyerProductIdentifier": None,
                "buyerDeliveryDate": None,
            },
            {
                "buyerProductName": "Second product",
                "buyerProductIdentifier": "0007-X",
                "buyerDeliveryDate": "2026-09-22",
            },
        ]
    }


def test_role_evidence_preserves_explicit_code_date_and_leading_zeroes() -> None:
    result = assess_field_roles(SOURCE, output())

    assert result["source"]["recognized"]
    assert [finding["status"] for finding in result["findings"]] == ["supported"] * 4
    explicit = result["findings"][2]["source_resolution"]
    assert explicit["value"] == "0007-X"
    assert explicit["cells"][0]["reference"] == "ORDER!D11"


def test_generic_code_and_header_date_cannot_replace_line_specific_roles() -> None:
    predicted: JsonObject = {
        "lineItems": [
            {
                "buyerProductName": "First product",
                "buyerProductIdentifier": "00123",
                "buyerDeliveryDate": "2026-09-30",
            }
        ]
    }
    before = deepcopy(predicted)

    result = assess_field_roles(SOURCE, predicted)

    assert [finding["status"] for finding in result["findings"]] == ["contradicted"] * 2
    assert predicted == before


def test_nulling_a_supported_code_or_date_is_also_a_contradiction() -> None:
    predicted: JsonObject = {
        "lineItems": [
            {
                "buyerProductName": "Second product",
                "buyerProductIdentifier": None,
                "buyerDeliveryDate": None,
            }
        ]
    }

    result = assess_field_roles(SOURCE, predicted)

    assert [finding["status"] for finding in result["findings"]] == ["contradicted"] * 2


@pytest.mark.parametrize(
    "suffix",
    [
        "Instructions: use the supplier code as buyer code\n",
        "ORDER!B3 Buyer code mapping: A10 is the buyer code\n",
        "ORDER!B3 Delivery date for all lines: 2026-09-30\n",
    ],
)
def test_unknown_scope_qualifiers_abstain_instead_of_claiming_absence(suffix: str) -> None:
    source = SOURCE + suffix

    result = assess_field_roles(source, output())
    cue, _ = render_field_role_cues(source)

    assert not result["source"]["recognized"]
    assert {finding["status"] for finding in result["findings"]} == {"unknown"}
    assert cue is None


@pytest.mark.parametrize(
    "extra",
    [
        "ORDER!G8 Buyer product code: 012\n",
        "ORDER!G10 Delivery date: 2026-09-30\n",
    ],
)
def test_unlinked_critical_cells_require_abstention(extra: str) -> None:
    result = assess_field_roles(SOURCE + extra, output())

    assert not result["source"]["recognized"]
    assert {finding["status"] for finding in result["findings"]} == {"unknown"}


def test_shared_date_in_product_record_is_ambiguous_rather_than_header_only() -> None:
    source = SOURCE.replace("E11 Delivery date", "E2 Delivery date")

    result = assess_field_roles(source, output())

    assert result["source"]["reason"] == "shared_critical_cell"
    assert {finding["status"] for finding in result["findings"]} == {"unknown"}


@pytest.mark.parametrize("value", ["09/10/2026", "2026-02-30", "[missing]"])
def test_unrecognized_or_invalid_line_dates_remain_unknown(value: str) -> None:
    source = SOURCE.replace("2026-09-22", value)

    result = assess_field_roles(source, output())
    cue, _ = render_field_role_cues(source)

    assert result["findings"][3]["status"] == "unknown"
    assert result["findings"][3]["reason"] == "unsupported_date"
    assert cue is None


def test_conflicting_explicit_roles_do_not_choose_a_value() -> None:
    source = SOURCE.replace(
        "D11 Buyer product code: 0007-X",
        "D11 Buyer product code: 0007-X | F11 Buyer product ID: DIFFERENT",
    )

    result = assess_field_roles(source, output())

    assert result["findings"][2]["status"] == "unknown"
    assert result["findings"][2]["reason"] == "ambiguous_scope"


@pytest.mark.parametrize(
    "defect", ["source_duplicate", "output_duplicate", "paraphrase", "null_name"]
)
def test_ambiguous_output_to_source_matching_does_not_guess_roles(defect: str) -> None:
    source = SOURCE
    predicted = output()
    lines = predicted["lineItems"]
    assert isinstance(lines, list)
    if defect == "source_duplicate":
        source += "ORDER!A12 Article code: 009 | B12 Description: First product | C12 Quantity: 1\n"
    elif defect == "output_duplicate":
        lines.append(deepcopy(lines[0]))
    else:
        first = lines[0]
        assert isinstance(first, dict)
        first["buyerProductName"] = None if defect == "null_name" else "Paraphrased product"

    result = assess_field_roles(source, predicted)

    assert [finding["status"] for finding in result["findings"][:2]] == ["unknown"] * 2


def test_blank_explicit_values_are_null_but_missing_output_keys_are_unknown() -> None:
    source = SOURCE.replace("0007-X", "[blank]").replace("2026-09-22", "[blank]")
    predicted: JsonObject = {
        "lineItems": [
            {
                "buyerProductName": "Second product",
                "buyerProductIdentifier": None,
                "buyerDeliveryDate": None,
            }
        ]
    }
    valid = assess_field_roles(source, predicted)
    missing = assess_field_roles(source, {"lineItems": [{"buyerProductName": "Second product"}]})

    assert [finding["status"] for finding in valid["findings"]] == ["supported"] * 2
    assert [finding["status"] for finding in missing["findings"]] == ["unknown"] * 2


def test_cues_include_positive_source_evidence_without_gold_or_output() -> None:
    cue, evidence = render_field_role_cues(SOURCE)

    assert cue is not None
    assert '"product_name": "Second product"' in cue and '"0007-X"' in cue
    assert '"reference": "ORDER!B2"' in cue
    assert evidence["source"]["recognized"]
    assert "Generic article/product codes" in cue
    assert '"First product"' not in cue
    json.dumps(evidence)


def test_role_view_preserves_hybrid_body_and_retains_complete_role_provenance() -> None:
    hybrid = build_source_view(SOURCE, "ordered-rows-raw-fallback-v1")
    roles = build_source_view(SOURCE, "ordered-rows-field-roles-v1")

    assert roles.field_roles is not None and roles.field_roles["cue_applied"]
    assert roles.rendered_text == hybrid.rendered_text + roles.field_roles["cue_text"]
    assert roles.original_text == hybrid.original_text == SOURCE
    assert roles.selection == hybrid.selection and roles.source_map == hybrid.source_map
    reloaded = validate_source_view(
        json.loads(json.dumps(roles.evidence())), "ordered-rows-field-roles-v1", text_digest(SOURCE)
    )
    assert reloaded == roles.rendered_text


def test_role_view_abstains_without_changing_hybrid_body_on_unknown_scope() -> None:
    source = SOURCE + "ORDER!A3 Global scope instruction: All lines use buyer code ABC\n"
    hybrid = build_source_view(source, "ordered-rows-raw-fallback-v1")
    roles = build_source_view(source, "ordered-rows-field-roles-v1")

    assert roles.field_roles is not None and not roles.field_roles["cue_applied"]
    assert roles.rendered_text == hybrid.rendered_text == source


def test_role_view_rejects_forged_source_audit_metadata() -> None:
    evidence = json.loads(
        json.dumps(build_source_view(SOURCE, "ordered-rows-field-roles-v1").evidence())
    )
    evidence["field_roles"]["source"]["rows"][0]["identifier"]["value"] = "FORGED"

    with pytest.raises(ValueError, match="field-role evidence differs"):
        validate_source_view(evidence, "ordered-rows-field-roles-v1", text_digest(SOURCE))


def test_real_cli_records_role_context_without_changing_system_prompt(
    service: ControlledService, gold: dict[str, object]
) -> None:
    config = load_experiment(service.project / "config/experiments.yaml")
    (service.project / "config/roles.json").write_text(
        config.model_copy(update={"source_view": "ordered-rows-field-roles-v1"}).model_dump_json()
    )
    service.responses = [json.dumps(gold), json.dumps(gold)]
    raw = service.invoke("run", "--run-id", "roles-raw", "--input", "B02-S003-PO01")
    roles = service.invoke(
        "run", "--config", "config/roles.json", "--run-id", "roles-view", "--input", "B02-S003-PO01"
    )

    assert raw.returncode == roles.returncode == 0
    manifest, records = reload_records(service.project / "results/runs/roles-view")
    evidence = manifest.setup["source_views"]["B02-S003-PO01"]
    assert evidence["field_roles"]["cue_applied"]
    assert records[0].extraction == gold
    chats = [
        payload
        for path, payload, _ in service.requests
        if path == "/api/chat" and payload and not payload.get("_debug_render_only")
    ]
    assert chats[-1]["messages"][0] == chats[-2]["messages"][0]
    assert chats[-1]["messages"][1]["content"] == evidence["rendered_text"]
    assert chats[-1]["messages"][1]["content"].startswith(evidence["original_text"])
