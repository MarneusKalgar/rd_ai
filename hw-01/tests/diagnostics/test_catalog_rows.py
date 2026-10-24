"""Source-evidence checks distinguish contradiction from unsupported interpretation."""

from copy import deepcopy

import pytest

from extraction_service.diagnostics.catalog_rows import check_ordered_rows
from extraction_service.diagnostics.types import DiagnosticReason, EvidenceStatus
from extraction_service.extraction.validation import JsonObject


def output(*names: str | None) -> JsonObject:
    return {"lineItems": [{"buyerProductName": name} for name in names]}


HU_CATALOG = (
    "ORDER!A21 Termék kódja: 001 | B21 Megnevezés: Catalog 25 kg | "
    "C21 Rendelt mennyiség: [blank] | D21 Mértékegység: L | G21 Ár: 9.00"
)
HU_ORDER = (
    "ORDER!A74 Termék kódja: 002 | B74 Megnevezés: Ordered 25 kg | "
    "C74 Rendelt mennyiség: 52 | D74 Mértékegység: L | G74 Ár: 44.91"
)


@pytest.mark.parametrize(
    ("text", "profile"),
    [
        (HU_CATALOG + "\n" + HU_ORDER, "hu-entered-order-quantity-v1"),
        (
            "FORM!E13 Artikelcode: 001 | C13 Omschrijving: Catalog 25 kg | "
            "F13 Aantal: [blank] | F12 Eenheid: Dozen\n"
            "FORM!E22 Artikelcode: 002 | C22 Omschrijving: Ordered 25 kg | "
            "F22 Aantal: 2.50 | F12 Eenheid: Dozen",
            "nl-entered-order-quantity-v1",
        ),
        (
            "FORM!B11 Cod produs: 001 | C11 Nume produs: Catalog 25 kg | "
            "D11 Comanda: [blank] | D9 Unitate: BX\n"
            "FORM!B17 Cod produs: 002 | C17 Nume produs: Ordered 25 kg | "
            "D17 Comanda: 9 | D9 Unitate: BX",
            "ro-entered-order-quantity-v1",
        ),
    ],
)
def test_known_layouts_use_order_column_not_package_size_or_price(
    text: str,
    profile: str,
) -> None:
    extraction = output("Catalog 25 kg", "Ordered 25 kg")
    before = deepcopy(extraction)

    result = check_ordered_rows(text, extraction)

    assert result.profile_id == profile
    assert result.status == EvidenceStatus.CONTRADICTED
    assert [row.status for row in result.findings] == [
        EvidenceStatus.CONTRADICTED,
        EvidenceStatus.SUPPORTED,
    ]
    assert result.findings[0].reason == DiagnosticReason.BLANK_ORDER_QUANTITY
    assert result.findings[0].output_path == "/lineItems/0"
    assert result.findings[0].source_rows[0].source_line == 1
    assert result.findings[0].source_rows[0].quantity_value == "[blank]"
    assert result.findings[0].source_rows[0].text == text.splitlines()[0]
    assert extraction == before


@pytest.mark.parametrize("quantity", ["0", "-1", "1,5", "NaN", "", "unknown"])
def test_uninterpreted_quantity_is_unknown_not_catalog(quantity: str) -> None:
    text = HU_ORDER.replace("Rendelt mennyiség: 52", f"Rendelt mennyiség: {quantity}")

    result = check_ordered_rows(text, output("Ordered 25 kg"))

    assert result.status == EvidenceStatus.UNKNOWN
    assert result.findings[0].reason in (
        DiagnosticReason.UNCLEAR_ORDER_QUANTITY,
        DiagnosticReason.AMBIGUOUS_SOURCE,
    )


@pytest.mark.parametrize(
    "text",
    [
        HU_ORDER.replace("C74 Rendelt mennyiség: 52 | ", ""),
        HU_ORDER.replace("C74 Rendelt mennyiség", "C73 Rendelt mennyiség"),
        HU_ORDER.replace("C74 Rendelt mennyiség", "OTHER!C74 Rendelt mennyiség"),
        HU_ORDER.replace("C74 Rendelt mennyiség", "C74 Package size"),
    ],
)
def test_quantity_requires_own_row_sheet_and_order_label(text: str) -> None:
    result = check_ordered_rows(text, output("Ordered 25 kg"))

    assert result.status == EvidenceStatus.UNKNOWN
    assert result.findings[0].reason == DiagnosticReason.UNCLEAR_ORDER_QUANTITY
    assert result.findings[0].source_rows[0].quantity_value is None


@pytest.mark.parametrize("quantity", ["[blank]", "7"])
@pytest.mark.parametrize(
    ("text", "profile"),
    [
        (
            "ORDER!A21 Termék kódja: 001 | B21 Megnevezés: Widget | "
            "H21 Rendelt mennyiség: QUANTITY",
            "hu-entered-order-quantity-v1",
        ),
        (
            "ORDER!E21 Artikelcode: 001 | C21 Omschrijving: Widget | H21 Aantal: QUANTITY",
            "nl-entered-order-quantity-v1",
        ),
        (
            "ORDER!B21 Cod produs: 001 | C21 Nume produs: Widget | H21 Comanda: QUANTITY",
            "ro-entered-order-quantity-v1",
        ),
    ],
)
def test_quantity_label_in_wrong_column_does_not_establish_order_evidence(
    text: str,
    profile: str,
    quantity: str,
) -> None:
    source = text.replace("QUANTITY", quantity)

    result = check_ordered_rows(source, output("Widget"))

    assert result.profile_id == profile
    assert result.status == EvidenceStatus.UNKNOWN
    assert len(result.findings) == 1
    finding = result.findings[0]
    assert finding.status == EvidenceStatus.UNKNOWN
    assert finding.reason == DiagnosticReason.UNCLEAR_ORDER_QUANTITY
    assert len(finding.source_rows) == 1
    assert finding.source_rows[0].quantity_cell is None
    assert finding.source_rows[0].quantity_value is None


@pytest.mark.parametrize(
    "text",
    [
        "Order: one widget, amount unspecified",
        HU_ORDER.replace("A74 Termék kódja", "Z74 Termék kódja"),
        HU_ORDER + " | C74 Rendelt mennyiség: [blank]",
        HU_ORDER + "\n" + HU_ORDER,
        HU_ORDER + "\n" + "FORM!B11 Cod produs: 1 | C11 Nume produs: Other | D11 Comanda: 3",
        HU_ORDER + " | malformed cell",
        HU_ORDER.replace("B74 Megnevezés", "B74 Unknown description"),
    ],
)
def test_unknown_or_ambiguous_structure_never_claims_support(text: str) -> None:
    result = check_ordered_rows(text, output("Ordered 25 kg"))

    assert result.status == EvidenceStatus.UNKNOWN
    assert result.profile_id is None
    assert result.findings[0].source_rows == ()


@pytest.mark.parametrize("name", [None, "invented", "ordered 25 kg", "Ordered"])
def test_product_matching_is_exact_and_does_not_guess(name: str | None) -> None:
    result = check_ordered_rows(HU_ORDER, output(name))

    assert result.status == EvidenceStatus.UNKNOWN
    assert result.findings[0].reason == DiagnosticReason.UNMATCHED_PRODUCT


def test_duplicate_name_with_order_and_catalog_evidence_is_unknown() -> None:
    text = HU_CATALOG.replace("Catalog 25 kg", "Ordered 25 kg") + "\n" + HU_ORDER

    result = check_ordered_rows(text, output("Ordered 25 kg"))

    assert result.status == EvidenceStatus.UNKNOWN
    assert result.findings[0].reason == DiagnosticReason.AMBIGUOUS_PRODUCT
    assert len(result.findings[0].source_rows) == 2


def test_duplicate_names_all_blank_prove_catalog_inclusion_without_guessing_row() -> None:
    text = HU_CATALOG + "\n" + HU_CATALOG.replace("21", "22")

    result = check_ordered_rows(text, output("Catalog 25 kg"))

    assert result.status == EvidenceStatus.CONTRADICTED
    assert len(result.findings[0].source_rows) == 2
    assert {row.quantity_cell for row in result.findings[0].source_rows} == {
        "ORDER!C21",
        "ORDER!C22",
    }


def test_repeated_output_cannot_reuse_one_ordered_row_as_multiple_supported_rows() -> None:
    result = check_ordered_rows(HU_ORDER, output("Ordered 25 kg", "Ordered 25 kg"))

    assert result.status == EvidenceStatus.UNKNOWN
    assert [row.output_path for row in result.findings] == ["/lineItems/0", "/lineItems/1"]
    assert [row.status for row in result.findings] == [EvidenceStatus.UNKNOWN] * 2
    assert [row.reason for row in result.findings] == [DiagnosticReason.REPEATED_OUTPUT_PRODUCT] * 2


def test_repeated_source_orders_are_not_silently_deduplicated() -> None:
    text = HU_ORDER + "\n" + HU_ORDER.replace("74", "75")

    result = check_ordered_rows(text, output("Ordered 25 kg", "Ordered 25 kg"))

    assert result.status == EvidenceStatus.UNKNOWN
    assert [row.output_path for row in result.findings] == ["/lineItems/0", "/lineItems/1"]
    assert [row.status for row in result.findings] == [EvidenceStatus.UNKNOWN] * 2
    assert [row.reason for row in result.findings] == [DiagnosticReason.AMBIGUOUS_PRODUCT] * 2


@pytest.mark.parametrize("unknown_first", [False, True])
def test_contradicted_row_determines_record_status_even_with_unknown_rows(
    unknown_first: bool,
) -> None:
    names = ["Catalog 25 kg", "Unmatched product"]
    statuses = [EvidenceStatus.CONTRADICTED, EvidenceStatus.UNKNOWN]
    reasons = [DiagnosticReason.BLANK_ORDER_QUANTITY, DiagnosticReason.UNMATCHED_PRODUCT]

    if unknown_first:
        names.reverse()
        statuses.reverse()
        reasons.reverse()

    result = check_ordered_rows(HU_CATALOG, output(*names))

    assert result.status == EvidenceStatus.CONTRADICTED
    assert [row.output_path for row in result.findings] == ["/lineItems/0", "/lineItems/1"]
    assert [row.status for row in result.findings] == statuses
    assert [row.reason for row in result.findings] == reasons


def test_row_support_does_not_assert_quantity_field_correctness() -> None:
    extraction: JsonObject = {
        "lineItems": [{"buyerProductName": "Ordered 25 kg", "buyerProductQuantity": None}]
    }

    result = check_ordered_rows(HU_ORDER, extraction)

    assert result.status == EvidenceStatus.SUPPORTED


@pytest.mark.parametrize("extraction", [None, {}, {"lineItems": []}])
def test_unusable_extraction_has_unknown_status_not_vacuous_success(
    extraction: JsonObject | None,
) -> None:
    result = check_ordered_rows(HU_ORDER, extraction)

    assert result.status == EvidenceStatus.UNKNOWN
    assert result.reason == DiagnosticReason.UNUSABLE_EXTRACTION
    assert result.findings == ()
