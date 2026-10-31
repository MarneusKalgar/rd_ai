# Reviewed data: corpus-v1 / gold-v1

Ten customer-neutral text inputs and their expected extraction objects were
accepted together by the user on **2026-10-17**, after reviewing the proposed
gold packet. The approval was at case level, with no individual field edits.
It is recorded in `manifest.json` with hashes of every exported artifact and
the extraction schema. Original Excel files and private source mappings are
not required to use this dataset.

The user subsequently approved the remaining 20 selected neutral inputs on
2026-10-17. **All 30 benchmark texts are now frozen**, with 10 gold objects.
This second approval covers the input texts; the other 20 draft extraction
objects remain private and are not gold labels.

| Path | Contents |
| --- | --- |
| `inputs/<inputId>.txt` | Frozen neutral input, exactly as reviewed. |
| `gold/<inputId>.json` | Expected object for one of the 10 gold cases, conforming to the v1 schema. |
| `annotations/<inputId>.json` | Field-specific neutral evidence, decision notes, order-line selection and distractors; no original source values. |
| `manifest.json` | Approval record, hashes, languages and anonymous grouping metadata. |
| `corpus-manifest.json` | All 30 approved input paths and hashes; identifies the 10 gold cases and both approval records. |

## Preparation and review

Private Excel workbooks were inspected offline to identify logical purchase
orders, their ordered lines, field roles and supported values. Separate orders
were split into individual texts; lookup and catalog rows were excluded from
ordered lines. Ambiguous or unsupported workbooks were deferred.

Deterministic fictional replacements were applied to identifying values,
including parties, addresses, products and identifiers. Dates, quantities and
prices were also replaced while retaining relevant formats, repeated-value
relationships and supported total calculations. Missing fields remained
missing. The outputs are text projections, not sanitized Excel copies.

Private review packets showed source cells, their neutral replacements and
draft extraction values side by side. The user approved the 10 proposed gold
pairs at case level, then approved the other 20 neutral inputs. Schema
validation and artifact hashes were checked before freezing the dataset.
Reproducing model runs requires only the included texts and gold objects;
original workbooks, private mappings, review packets and the one-off preparation
tool are excluded from Git.

## Annotation documentation, revision 2

The gold JSON objects contain the expected extraction labels used for scoring.
The annotation files explain those labels. Every header field and every field
of each ordered line records its expected `value`, relevant `evidence`,
`decision` and `note`. Evidence is a quote or cell-labeled fragment from the
neutral input, not the original workbook. The expected values repeat the gold
object for readability; the gold object remains the scoring target.

| Decision | Meaning |
| --- | --- |
| `direct` | Explicit value copied from the appropriate labeled role. A note may be empty for a straightforward copy. |
| `normalized` | Supported date, unit or address formatting is mapped to the contract representation. |
| `absent` | The required value is not stated; keep `null` without inventing a default. |
| `role_not_established` | Related information exists, but does not establish the requested role, such as buyer ownership of a product code or a delivery date tied to a line. |

Notes explain nulls, date and unit normalization, buyer versus other product
codes, printed versus spreadsheet line numbers, and explicit quantity versus
package size. `relatedEvidence` or `rejectedEvidence` identifies a nearby
value that must not be substituted. `lineSelection` records the ordered and
excluded catalog-row counts, with up to three excluded-row examples.
`distractors` explains order-level dates that must not become issue dates or
line delivery dates.

These explanations were added by the agent at the user's request after the
original case-level approval. They document the existing labels and do not
claim a new human field review. The 30 input texts, 10 gold objects and schema
are unchanged. `manifest.json` records annotation revision 2 and retains the
original annotation hashes alongside the updated hashes; the corpus manifest
references the updated gold manifest.

## Evaluation scope

These 10 cases contain **34 ordered lines**, cover **8 document languages**
and **10 layout groups**, and collectively provide non-null examples of all
15 contract fields. Product descriptions are generated from an English
vocabulary even where document labels are in another language. The corpus
contains synthetic projections of source layouts, so measurements describe
these prepared texts; they do not establish Excel, PDF or OCR accuracy.

Missing fields remain `null`; approval does not invent unavailable data.
Keep every `sourceGroup` and shared `layoutGroup` together in evaluation
splits. Do not tune against the gold answers and then present those same
cases as an untouched test set.

The dataset satisfies the assignment's minimum **30 texts and 10 manually
reviewed gold objects**. The full corpus spans 30 source groups and 25 layout
groups. Use `corpus-manifest.json` to enumerate model inputs and `manifest.json`
for gold evaluation. The remaining private candidate pool is not part of the
submission dataset.

Frozen files must not be overwritten by preparation runs. Changed inputs,
labels or schema require a new review and an explicitly versioned snapshot.
