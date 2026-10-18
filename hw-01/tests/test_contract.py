import hashlib
import json
from dataclasses import asdict
from pathlib import Path
from typing import Any, Final, Never

import pytest
from conftest import PROJECT_DIR, first_line

from hw01.extraction import ContractLoadError, ExtractionContract
from hw01.extraction.validation import JsonObject, JsonValue

MANIFEST: Final[dict[str, Any]] = json.loads((PROJECT_DIR / "data/manifest.json").read_text())
GOLD_CASES: Final[list[dict[str, Any]]] = MANIFEST["cases"]
GOLD_CASE_IDS: Final[list[str]] = [case["inputId"] for case in GOLD_CASES]


@pytest.mark.parametrize(
    "case",
    GOLD_CASES,
    ids=GOLD_CASE_IDS,
)
def test_approved_gold_passes_without_changing_values_or_line_order(
    contract: ExtractionContract,
    case: dict[str, Any],
) -> None:
    raw_response = (PROJECT_DIR / "data" / case["goldFile"]).read_text()
    expected = json.loads(raw_response)

    result = contract.validate_json(raw_response)

    assert result.is_valid
    assert result.value == expected
    assert result.raw_response == raw_response
    assert result.schema.sha256 == MANIFEST["schemaSha256"]


@pytest.mark.parametrize("scope", ["header", "line"])
def test_nullable_fields_are_required_even_when_the_expected_value_is_null(
    contract: ExtractionContract,
    gold: JsonObject,
    scope: str,
) -> None:
    target = gold if scope == "header" else first_line(gold)
    nullable_field = "paymentTerms" if scope == "header" else "buyerProductIdentifier"

    present_result = contract.validate_json(json.dumps(gold))

    assert target[nullable_field] is None
    assert present_result.is_valid

    del target[nullable_field]

    result = contract.validate_json(json.dumps(gold))

    assert not result.is_valid
    assert result.value is None
    assert result.issues[0].keyword == "required"
    assert result.issues[0].instance_path == ("" if scope == "header" else "/lineItems/0")


@pytest.mark.parametrize("scope", ["header", "line"])
@pytest.mark.parametrize(
    "metadata", ["model", "prompt", "sampling", "latency", "cost", "retryCount"]
)
def test_attempt_metadata_is_rejected_inside_extraction_objects(
    contract: ExtractionContract,
    gold: JsonObject,
    scope: str,
    metadata: str,
) -> None:
    target = gold if scope == "header" else first_line(gold)
    target[metadata] = "belongs in the attempt record"

    result = contract.validate_json(json.dumps(gold))

    assert not result.is_valid
    assert len(result.issues) == 1
    assert result.issues[0].stage == "schema"
    assert result.issues[0].keyword == "additionalProperties"
    assert result.issues[0].instance_path == ("" if scope == "header" else "/lineItems/0")


@pytest.mark.parametrize("value", [None, "TONNE", "kg", 1])
def test_unit_enum_rejects_null_unknown_categories_and_wrong_types(
    contract: ExtractionContract,
    gold: JsonObject,
    value: JsonValue,
) -> None:
    first_line(gold)["quantityUnit"] = value

    result = contract.validate_json(json.dumps(gold))

    assert not result.is_valid
    expected_keywords = {"type", "enum"} if value is None or value == 1 else {"enum"}
    actual_keywords = {issue.keyword for issue in result.issues}

    assert actual_keywords == expected_keywords

    for issue in result.issues:
        assert issue.stage == "schema"
        assert issue.instance_path == "/lineItems/0/quantityUnit"


@pytest.mark.parametrize(
    "value", ["2026-02-29", "2026-04-31", "20/08/2026", "2026-8-20", "2026-08-20T00:00:00Z"]
)
@pytest.mark.parametrize("field", ["purchaseOrderDateTime", "buyerDeliveryDate"])
def test_date_format_checks_real_calendar_dates_on_headers_and_lines(
    contract: ExtractionContract,
    gold: JsonObject,
    field: str,
    value: str,
) -> None:
    target = gold if field == "purchaseOrderDateTime" else first_line(gold)
    target[field] = value

    result = contract.validate_json(json.dumps(gold))

    assert not result.is_valid
    assert len(result.issues) == 1
    assert result.issues[0].stage == "schema"
    assert result.issues[0].keyword == "format"
    expected_path = f"/{field}" if field == "purchaseOrderDateTime" else f"/lineItems/0/{field}"
    expected_schema_path = (
        f"/properties/{field}/format"
        if field == "purchaseOrderDateTime"
        else f"/properties/lineItems/items/properties/{field}/format"
    )

    assert result.issues[0].instance_path == expected_path
    assert result.issues[0].schema_path == expected_schema_path


def test_valid_leap_day_and_explicit_missing_scalars_are_accepted(
    contract: ExtractionContract,
    gold: JsonObject,
) -> None:
    line_item = first_line(gold)

    gold["purchaseOrderDateTime"] = "2028-02-29"
    line_item["buyerDeliveryDate"] = None
    line_item["buyerProductUOM"] = None
    line_item["quantityUnit"] = "UNKNOWN"

    result = contract.validate_json(json.dumps(gold))

    assert result.is_valid


@pytest.mark.parametrize("field", ["totalValue", "buyerProductQuantity", "buyerUnitPrice"])
@pytest.mark.parametrize("value", [12.5, True, "12,50", "1e3", "-1", "", " 12.5 "])
def test_amounts_and_quantities_must_be_decimal_strings_without_coercion(
    contract: ExtractionContract,
    gold: JsonObject,
    field: str,
    value: JsonValue,
) -> None:
    target = gold if field == "totalValue" else first_line(gold)
    target[field] = value

    result = contract.validate_json(json.dumps(gold))

    assert not result.is_valid
    assert result.value is None
    assert target[field] == value
    assert len(result.issues) == 1
    expected_keyword = "pattern" if isinstance(value, str) else "type"
    expected_path = f"/{field}" if field == "totalValue" else f"/lineItems/0/{field}"

    assert result.issues[0].stage == "schema"
    assert result.issues[0].keyword == expected_keyword
    assert result.issues[0].instance_path == expected_path


@pytest.mark.parametrize(
    "value,expected_keyword,expected_path",
    [
        ([], "minItems", "/lineItems"),
        (None, "type", "/lineItems"),
        ({}, "type", "/lineItems"),
        ([None], "type", "/lineItems/0"),
    ],
)
def test_lines_must_be_a_nonempty_array_of_complete_objects(
    contract: ExtractionContract,
    gold: JsonObject,
    value: JsonValue,
    expected_keyword: str,
    expected_path: str,
) -> None:
    gold["lineItems"] = value

    result = contract.validate_json(json.dumps(gold))

    assert not result.is_valid
    assert len(result.issues) == 1
    assert result.issues[0].stage == "schema"
    assert result.issues[0].keyword == expected_keyword
    assert result.issues[0].instance_path == expected_path


@pytest.mark.parametrize("raw", ["[]", "null", '"a purchase order"', "123"])
def test_response_root_must_be_a_po_object(contract: ExtractionContract, raw: str) -> None:
    result = contract.validate_json(raw)

    assert not result.is_valid
    assert result.issues[0].stage == "schema"
    assert result.issues[0].instance_path == ""
    assert result.issues[0].keyword == "type"


@pytest.mark.parametrize(
    "raw,keyword",
    [
        ('{"buyerName": "A", "buyerName": "B"}', "duplicate_key"),
        ('{"lineItems": [{"quantityUnit": "CASE", "quantityUnit": "EACH"}]}', "duplicate_key"),
        ('{"totalValue": NaN}', "non_finite_number"),
        ('{"totalValue": Infinity}', "non_finite_number"),
        ('{"totalValue": -Infinity}', "non_finite_number"),
        ("```json\n{}\n```", "syntax"),
        ("{} {}", "syntax"),
        ('{"buyerName": "A",}', "syntax"),
    ],
)
def test_invalid_or_ambiguous_json_is_not_salvaged(
    contract: ExtractionContract,
    raw: str,
    keyword: str,
) -> None:
    result = contract.validate_json(raw)

    assert not result.is_valid
    assert result.raw_response == raw
    assert result.value is None
    assert len(result.issues) == 1
    assert result.issues[0].stage == "json"
    assert result.issues[0].keyword == keyword


def test_syntax_errors_keep_line_and_column_for_correction(contract: ExtractionContract) -> None:
    result = contract.validate_json('{\n"purchaseOrderNumber":\n}')

    assert result.issues[0].line == 3
    assert result.issues[0].column == 1


def test_json_decoder_nesting_failure_returns_evidence_instead_of_escaping(
    contract: ExtractionContract,
    gold: JsonObject,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    raw_response = json.dumps(gold)

    def fail_decoding(response: str) -> Never:
        raise RecursionError("decoder nesting limit reached")

    # Decoder nesting thresholds vary across Python runtimes. Exercise its
    # failure boundary without depending on a particular stack-depth limit.
    monkeypatch.setattr("hw01.extraction.contract.parse_json", fail_decoding)

    result = contract.validate_json(raw_response)

    assert not result.is_valid
    assert result.value is None
    assert result.raw_response == raw_response
    assert len(result.issues) == 1
    assert result.issues[0].stage == "json"
    assert result.issues[0].keyword == "nesting"
    assert result.issues[0].message == "JSON nesting exceeds the decoder limit"


def test_decoder_number_limits_are_model_failures_not_uncaught_exceptions(
    contract: ExtractionContract,
) -> None:
    oversized_number = "9" * 5000
    raw_response = '{"totalValue":' + oversized_number + "}"

    result = contract.validate_json(raw_response)

    assert not result.is_valid
    assert result.issues[0].stage == "json"
    assert result.issues[0].keyword == "decoder"


def test_multiple_schema_errors_are_serializable_attempt_evidence(
    contract: ExtractionContract,
    gold: JsonObject,
) -> None:
    gold["buyerCurrency"] = "eur"
    first_line(gold)["buyerProductQuantity"] = 5

    result = contract.validate_json(json.dumps(gold))

    paths = {issue.instance_path for issue in result.issues}
    serialized_result = json.dumps(asdict(result))
    result_record = json.loads(serialized_result)

    assert paths == {"/buyerCurrency", "/lineItems/0/buyerProductQuantity"}
    assert result.value is None
    assert result_record["issues"][0]["schema_path"]


def test_identifier_strings_and_leading_zeros_survive_validation(
    contract: ExtractionContract,
    gold: JsonObject,
) -> None:
    line_item = first_line(gold)

    gold["purchaseOrderNumber"] = "00012-A/03"
    line_item["buyerProductIdentifier"] = "000789"

    result = contract.validate_json(json.dumps(gold))

    assert result.value == gold
    assert result.value is not None

    validated_line = first_line(result.value)

    assert validated_line["purchaseOrderLineNumber"] == "002"

    line_item["buyerProductIdentifier"] = 789

    invalid_result = contract.validate_json(json.dumps(gold))

    assert not invalid_result.is_valid


def test_adapter_schema_copies_cannot_weaken_the_shared_validator(
    contract: ExtractionContract,
    gold: JsonObject,
) -> None:
    provider_schema = contract.schema_for_provider()

    provider_schema["additionalProperties"] = True
    provider_schema["properties"]["lineItems"]["items"]["required"].clear()
    gold["model"] = "metadata"
    del first_line(gold)["buyerProductIdentifier"]

    result = contract.validate_json(json.dumps(gold))
    unchanged_schema = contract.schema_for_provider()

    assert not result.is_valid
    violations = {(issue.keyword, issue.instance_path) for issue in result.issues}
    original_schema = json.loads(
        (PROJECT_DIR / "schemas/purchase-order-extraction.v1.schema.json").read_text()
    )

    assert violations == {("additionalProperties", ""), ("required", "/lineItems/0")}
    assert unchanged_schema == original_schema


def test_contract_is_loaded_once_and_reloading_changed_bytes_fails(
    tmp_path: Path,
    gold: JsonObject,
) -> None:
    original = PROJECT_DIR / "schemas/purchase-order-extraction.v1.schema.json"
    path = tmp_path / original.name
    path.write_bytes(original.read_bytes())

    contract = ExtractionContract.load(path, expected_sha256=MANIFEST["schemaSha256"])

    path.write_text("{}")

    result = contract.validate_json(json.dumps(gold))

    assert result.is_valid

    with pytest.raises(ContractLoadError, match="hash differs"):
        ExtractionContract.load(path, expected_sha256=MANIFEST["schemaSha256"])


def test_invalid_schema_with_matching_hash_is_a_setup_error(tmp_path: Path) -> None:
    path = tmp_path / "purchase-order-extraction.v1.schema.json"
    data = b'{"$schema":"https://json-schema.org/draft/2020-12/schema","type":42}'
    path.write_bytes(data)

    expected_sha256 = hashlib.sha256(data).hexdigest()

    with pytest.raises(ContractLoadError, match="Invalid extraction schema"):
        ExtractionContract.load(path, expected_sha256=expected_sha256)


@pytest.mark.parametrize("dialect", [None, "http://json-schema.org/draft-07/schema#"])
def test_missing_or_wrong_dialect_is_rejected_even_with_a_matching_hash(
    tmp_path: Path,
    dialect: str | None,
) -> None:
    schema: dict[str, Any] = {"type": "object"}

    if dialect is not None:
        schema["$schema"] = dialect

    path = tmp_path / "purchase-order-extraction.v1.schema.json"
    schema_bytes = json.dumps(schema).encode("utf-8")
    path.write_bytes(schema_bytes)
    expected_sha256 = hashlib.sha256(schema_bytes).hexdigest()

    with pytest.raises(ContractLoadError, match="must declare JSON Schema Draft 2020-12"):
        ExtractionContract.load(path, expected_sha256=expected_sha256)
