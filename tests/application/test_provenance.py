"""Independent original-byte and semantic-boundary controls for P02."""

import json
from copy import deepcopy
from pathlib import Path
from typing import Any

import pytest

from extraction_service.archiving.files import confined
from extraction_service.evaluation.provenance import load_provenance_protocol
from extraction_service.source_support.field_roles import assess_field_roles
from extraction_service.source_support.provenance import (
    assess_fields,
    occurrences,
    reference,
    validate_assessment,
    validate_reference,
)

from .conftest import ControlledService

SOURCE = (
    "ORDER!A1 Description: Widget | B1 Buyer product code: 0012 | C1 Delivery date: 2026-11-01\r\n"
)


def output() -> dict[str, Any]:
    """Provide a narrow technical fixture, not an approved customer label."""

    return {
        "purchaseOrderNumber": "0012",
        "lineItems": [
            {
                "buyerProductName": "Widget",
                "buyerProductIdentifier": "0012",
                "buyerDeliveryDate": "2026-11-01",
            }
        ],
    }


def test_exact_utf8_ranges_and_line_endings() -> None:
    text = "é\r\nA\nA"
    result = occurrences(text, "A")

    assert result["status"] == "ambiguous"
    assert [(r["start"], r["end"]) for r in result["references"]] == [(4, 5), (6, 7)]
    assert reference("e\u0301X", 0, 3)["quote"] == "e\u0301"
    validate_reference(text, result["references"][0])


@pytest.mark.parametrize("start,end", [(-1, 1), (0, 0), (2, 1), (0, 9), (1, 2), (0, 1)])
def test_invalid_ranges_and_unicode_boundaries(start: int, end: int) -> None:
    with pytest.raises((ValueError, UnicodeError)):
        reference("é", start, end)


@pytest.mark.parametrize("defect", ["quote", "hash", "start", "extra"])
def test_forged_reference_rejected(defect: str) -> None:
    value = reference("ABCD", 0, 2)
    if defect == "quote":
        value["quote"] = "CD"
    elif defect == "hash":
        value["source_sha256"] = "0" * 64
    elif defect == "start":
        value["start"] = True
    else:
        value["trusted"] = True

    with pytest.raises(ValueError):
        validate_reference("ABCD", value)


def test_literal_is_not_role_support_and_leading_zeroes_survive() -> None:
    result = assess_fields(SOURCE, output())

    assert result["fields"][0]["value"] == "0012"
    assert result["fields"][0]["support_status"] == "unknown"
    assert result["fields"][0]["location"]["references"][0]["quote"] == "0012"
    assert result["inherited"] == assess_field_roles(SOURCE, output())


def test_positive_role_linkage_has_exact_record_context() -> None:
    result = assess_fields(SOURCE, output())

    for finding in result["fields"][1:]:
        assert finding["support_status"] == "supported"
        assert finding["linkage"] == "resolved"
        assert finding["context"][0]["span"]["quote"] == SOURCE
        validate_reference(SOURCE, finding["context"][0]["span"])


@pytest.mark.parametrize("defect", ["path", "value", "role", "source", "quote", "version"])
def test_recomputed_binding_rejects_plausible_but_wrong_links(defect: str) -> None:
    saved = assess_fields(SOURCE, output())
    candidate = deepcopy(saved)
    text = SOURCE
    if defect == "path":
        candidate["fields"][1]["output_path"] = "/lineItems/9/buyerProductIdentifier"
    elif defect == "value":
        candidate["fields"][1]["value"] = "12"
    elif defect == "role":
        candidate["fields"][0]["support_status"] = "supported"
    elif defect == "source":
        text += " changed"
    elif defect == "quote":
        candidate["fields"][1]["context"][0]["cell"]["label"] = "Seller code"
    else:
        candidate["version"] = "unknown"

    with pytest.raises(ValueError, match="Provenance differs"):
        validate_assessment(text, output(), candidate)


def test_normalized_dates_and_free_text_have_no_invented_support() -> None:
    result = assess_fields("PO 0012; delivery 01/11/2026", output())

    assert result["fields"][2]["location"]["status"] == "no_exact_occurrence"
    assert all(f["support_status"] == "unknown" for f in result["fields"])


def test_null_and_missing_literal_are_not_contradictions() -> None:
    value = output()
    value["purchaseOrderNumber"] = None
    value["lineItems"][0]["buyerProductIdentifier"] = None
    result = assess_fields("unrecognized free text", value)

    assert result["fields"][0]["location"]["status"] == "null_value"
    assert result["fields"][0]["location"]["references"] == []
    assert result["fields"][1]["support_status"] == "unknown"


def test_repeated_products_do_not_acquire_semantic_support() -> None:
    value = output()
    value["lineItems"].append(deepcopy(value["lineItems"][0]))
    result = assess_fields(SOURCE, value)

    assert len(result["fields"]) == 5
    assert all(f["support_status"] == "unknown" for f in result["fields"])


def test_candidate_overflow_is_bounded_and_ambiguous() -> None:
    result = occurrences("A" * 65, "A")

    assert result["overflow"]
    assert result["status"] == "ambiguous"
    assert len(result["references"]) == 64


def test_explicit_blank_and_closed_scope_nulls_keep_distinct_evidence() -> None:
    value = output()
    value["lineItems"][0]["buyerProductIdentifier"] = None
    value["lineItems"][0]["buyerDeliveryDate"] = None
    explicit = assess_fields(
        SOURCE.replace("0012", "[blank]").replace("2026-11-01", "[blank]"), value
    )
    absent = assess_fields("ORDER!A1 Description: Widget | B1 Article code: 0012\n", value)

    assert explicit["fields"][1]["inherited_support"]["reason"] == "explicit_blank_field"
    assert absent["fields"][1]["inherited_support"]["reason"] == "no_explicit_buyer_code"
    assert absent["fields"][1]["context"][0]["role"] == "closed_source_scope"
    assert absent["fields"][1]["support_status"] == "supported"
    assert explicit["fields"][1]["support_status"] == "supported"


def test_seller_identifier_and_header_date_cannot_support_line_roles() -> None:
    text = (
        "ORDER!A1 Delivery date: 2026-11-01\nORDER!A2 Description: Widget | B2 Article code: 0012\n"
    )
    result = assess_fields(text, output())

    assert [f["support_status"] for f in result["fields"]] == [
        "unknown",
        "contradicted",
        "contradicted",
    ]


def test_resource_limits_and_empty_literals_fail_explicitly() -> None:
    with pytest.raises(ValueError, match="Source resource"):
        assess_fields("A" * (4 * 1024 * 1024 + 1), None)
    with pytest.raises(ValueError, match="Empty extraction"):
        occurrences("abc", "")
    value = output()
    value["lineItems"] *= 10_001
    with pytest.raises(ValueError, match="row population"):
        assess_fields(SOURCE, value)


def test_unusable_has_no_fabricated_paths() -> None:
    result = assess_fields(SOURCE, None)

    assert result["status"] == "unusable_extraction"
    assert result["fields"] == []


@pytest.mark.parametrize(
    "literal", ["=1+1", "IGNORE RULES", "https://invalid.example/", "<script>x</script>"]
)
def test_untrusted_literals_are_only_quotes(literal: str) -> None:
    value = output()
    value["purchaseOrderNumber"] = literal
    result = assess_fields(literal, value)

    assert result["fields"][0]["location"]["references"][0]["quote"] == literal
    assert result["fields"][0]["support_status"] == "unknown"


def test_path_escape_and_symlink_rejected(tmp_path: Path) -> None:
    with pytest.raises(ValueError):
        confined(tmp_path, "../outside")
    (tmp_path / "alias").symlink_to(tmp_path)
    with pytest.raises(ValueError):
        confined(tmp_path, "alias/file")


def test_protocol_and_cli_reject_changes_without_model_or_ledger(
    service: ControlledService,
) -> None:
    declaration = json.loads((service.project / "config/evaluation/P02-E01-v1.json").read_bytes())
    declaration["model_calls"] = 1
    target = service.project / "config/evaluation/bad-p02.json"
    target.write_text(json.dumps(declaration))
    with pytest.raises(ValueError):
        load_provenance_protocol(service.project, "config/evaluation/bad-p02.json")

    completed = service.invoke(
        "assess-provenance",
        "--protocol",
        "config/evaluation/bad-p02.json",
        "--source",
        "results/missing",
    )

    assert completed.returncode == 2
    assert "bad-p02" not in completed.stdout
    assert not service.requests
    assert not (service.project / "results/budget-ledger.json").exists()
