# HW-01 purchase-order extraction contract (v1)

## Scope and status

Version 1 is the fixed comparison target for the first HW-01 provider/local-model
run. It is a small, independent purchase-order contract, informed by the real
PO concepts: order identity, parties, shipping, currency/total, and repeating
ordered lines. It does not copy the integration schema, XML paths, master-data
requirements, or customer-specific rules. Any field change after labeling
requires a new schema version and a review of affected gold labels.

The output schema is [`purchase-order-extraction.v1.schema.json`](../../schemas/purchase-order-extraction.v1.schema.json).
One schema instance represents **one logical PO**, not necessarily one file,
sheet, or row. The deterministic input-preparation step may produce zero, one,
or several neutral text inputs from a workbook. Each input has one stable,
anonymous ID and one expected PO result. Unsupported documents are recorded
in the private preparation register and do not become empty PO outputs.

## Boundaries

| Boundary | Contract |
| --- | --- |
| Private source | Original Excel files remain outside Git and are never sent to a model. |
| Prepared input | Locally generated customer-neutral text preserves relevant labels, field presence, value formats and relationships, sheet aliases, cell coordinates, and row order. Sensitive values may be replaced consistently. Both models receive the same text. |
| Model output | A JSON object validated by the v1 schema. No source filenames, workbook metadata, model metadata, or private mapping appears here. |
| Run record | Separately logs anonymous input ID, schema/prompt/model versions, sampling settings, raw response, validation/retry outcome, latency, tokens, and cost. |
| Gold record | Separately stores a reviewed expected v1 object plus neutral cell references and labeling notes. Model drafts are not accepted as manual labels without source review. |

Preprocessing may decode workbook cell values, discard empty formatting-only
cells, identify the order-bearing sheet, split explicit per-order groups, and
attach cell coordinates. Synthetic replacement may alter a *present* value,
but must not manufacture a field that is absent in the source.
Visible cached formula results can be used only when present and attributable
to the order; formulas are not executed as part of extraction. Hidden lookup,
instruction, and duplicate display sheets must be inspected for privacy but
must not silently add order lines to the model input.

## Field meanings

The v1 schema uses familiar PO concept names where practical. Names in the
right column identify a *conceptual* later mapping, not a promise of direct
compatibility with another system's API.

| v1 field | Meaning and source rule | Related PO concept |
| --- | --- | --- |
| `purchaseOrderNumber` | Explicit identifier for this order; preserve leading zeros. | PO number |
| `purchaseOrderDateTime` | PO issue date, normalized to ISO date; never substitute delivery, entry, or cancellation date. | PO date |
| `buyerName` | Explicit buyer party; ship-to, bill-to, sender, and receiver are separate roles. | Buyer |
| `shipToInfo` | Source-supported neutral ship-to block as text; avoid guessed address components. | Ship To |
| `paymentTerms` | Explicit terms, if present. | Payment Terms |
| `buyerCurrency` | Selected currency code; an unselected currency list is not evidence. | Buyer Currency |
| `totalValue` | Explicit net product total for this order; never reuse an aggregate batch total. | Total Value |
| `lineItems[]` | Ordered rows belonging to this PO only. | Order line items |
| `lineItems[].buyerProductIdentifier` | Buyer product ID when identifiable; do not automatically treat a barcode as the buyer ID. | Buyer Product ID |
| `lineItems[].buyerProductName` | Ordered product description. | Buyer Product Name |
| `lineItems[].buyerProductQuantity` | Ordered quantity, not package size or a catalog quantity. | Buyer Product Quantity |
| `lineItems[].buyerProductUOM` | Supported source unit text/code. | Buyer Product UOM |
| `lineItems[].quantityUnit` | Normalized enum: `EACH`, `CASE`, `KILOGRAM`, `BOTTLE`, `OTHER`, or `UNKNOWN`. `OTHER` requires a known different unit; `UNKNOWN` means absent or uninterpretable. | Coded UOM, simplified for HW-01 |
| `lineItems[].buyerUnitPrice` | Explicit per-unit price. | Buyer Unit Price |
| `lineItems[].buyerDeliveryDate` | Delivery date only when linked to this line. | Line delivery date |

All keys are present in every output; unsupported or absent scalar values are
`null`. Dates use `YYYY-MM-DD`. Amounts and quantities are decimal strings
with `.` as separator, avoiding binary floating-point differences. Identifiers
remain strings. Line items retain source order. The schema requires at least
one ordered line for an eligible PO. A failed or unsupported input is tracked
as a run outcome rather than coerced into a schema-valid PO.

The real PO integration's `OrderCreate`/`OrderChange` message type is not a v1
extraction field: it is an integration action and cannot be inferred from the
mere absence of a change notice. The HW-01 enum is the explicitly defined
quantity-unit category. A later product adapter can map supported values to
its own code list; `OTHER` and `UNKNOWN` must not be passed off as exact codes.

## Historical four-workbook pilot assessment

These IDs describe workbook *shapes* only and explain the initial boundary
decisions; the pilot is separate from the frozen submission dataset. Private
filename-to-ID mapping stays out of the repository.

| Pilot | Observed structure | v1 decision |
| --- | --- | --- |
| S01 | Macro-enabled catalog/order template; one order header and 33 rows with entered order quantities among many catalog rows. Hidden help, comments, drawings, custom XML, and a VBA project are present. | One logical PO. Read order quantities from entered order cells; catalog-only rows are not line items. Produce neutral text, not a repackaged workbook. |
| S02 | International PO form with one filled product line and separate reference/article sheets. | One logical PO. Reference/article rows are not ordered lines. Distinguish PO date from requested ETA and selected currency from currency choices. |
| S03 | Internal sample/gift order request with ten filled quantity rows and several hidden reference/price sheets. | Out of scope for the core supplier-facing PO benchmark. Keep as an eligibility/negative pilot; do not count it toward the 30 PO texts or 10 PO gold records without a documented scope change. |
| S04 | Order export with one batch header, 87 item rows, four distinct per-line order IDs, a hidden duplicate, and two presentation subsets. | Split into four logical POs with 28, 28, 27, and 4 lines. Do not copy batch-level total or an entry/cancellation date into a per-PO field. |

This pilot therefore contains six eligible logical POs across three source
workbooks, plus one out-of-scope request. Four files must not be reported as
four evaluation documents. Multiple POs from one workbook share a layout and
must be kept together when assigning development versus held-out gold groups
to avoid near-duplicate leakage.

## Golden-set and scoring rules

The frozen [`dataset`](../../data/README.md) contains 30 approved neutral PO texts
and 10 manually reviewed v1 gold objects, satisfying the assignment's minimum
counts. These are separate from the six pilot POs. Gold cases span distinct
source layouts, languages, missing fields and line counts; copied rows or
identifier variants do not create independent cases. The internal pilot
request can test rejection separately from PO field-level accuracy.

Evaluate both models against the same prepared input and schema. Validate the
entire JSON response first. Compare header fields individually. Compare line
counts and ordered line fields, with a documented matching rule when repeated
product IDs occur. Score `null` against `null` explicitly, but report the
number of present-value fields too so a model cannot appear accurate by
returning mostly `null`. Keep structural validity, retry outcome, latency,
cost, and source/normalization errors separate from model field accuracy.

## Privacy and handoff

Customer-neutral text needs stable replacement of party names, contacts,
addresses, order numbers, product names/codes, and other identifying values
while preserving role distinctions, repeats, formats, dates, quantities, and
calculation relationships. A single generic company name for every party
would destroy buyer/supplier/ship-to evidence. The private mapping, raw
workbooks, and any unreviewed extracts stay outside Git. A sanitizer check
must inspect hidden sheets, comments, custom XML, drawings, and workbook
metadata before any whole-workbook copy is considered shareable. The default
HW-01 artifacts are reviewed neutral text and JSON, not sanitized Excel files.

The submission includes the frozen neutral texts, reviewed gold objects,
neutral annotations and approval manifests. Its dataset README records the
offline preparation method and evaluation limits. The one-off preparation
tool and private review material stay outside Git; running HW-01 does not
require access to them. Additional source preparation must flag unresolved
order boundaries, party roles, units or privacy replacements for review
rather than inventing values or rules.
