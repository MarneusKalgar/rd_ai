# Gemma: application-loaded synthetic examples on gold10

## Question and scope

The user authorized one native examples-only gold10 comparison after discussing
how an application supplies a model with skill content. The application loads
SKILL.md and examples.json into the instructions; Gemma does not discover files,
select tools or execute scripts. The package is reusable organization and
versioning. Its actual instruction content, not its presence on disk, is the
experimental intervention.

The comparison reuses the saved scoped primary output population. Frozen v2
instruction bytes remain an exact prefix. The scoped source view, selected/raw
fallback bodies, schema, approved inputs/gold and scorer remain unchanged.
Native Gemma4 e4b-it-qat remains on the same runtime 0.40.7, digest and tokenizer,
thinking=false, temperature 0/top_p 1, 49,152 context and 16,384 output allowance.
JSON/schema validation, bounded schema correction, transport/deadline policy
remain shared. Behavioral semantic correction is disabled. No provider/JEV,
remaining20, alternate examples or second native trial ran.

## Loaded content and experimental limits

The three fictional examples illustrate existing rules:

1. A catalog table with blank/zero rows, a positive ordered quantity, package
   counts, generic codes and an order-level date.
2. Repeated ordered products with an explicit buyer-owned code, leading zeroes
   and a delivery date linked only to one line.
3. An explicitly selected product with unreadable quantity, alongside an
   unselected catalog entry.

Every expected example PO is validated against the authoritative schema in
tests. The full objects are examples, not expected outputs for benchmark cases.
Values are invented, but topics were chosen after inspecting development gold10
failures. This is benchmark-informed prompting, not independent evaluation.
The package README discloses that history and is not loaded into requests.
No new business-rule supplement was added. The comparison measures the whole
examples package including its reference-data wrapper; it does not isolate
individual examples, language effects or metadata wording.

The loader verifies pinned byte hashes, explicit order and package confinement.
Missing/changed/empty resources, aliases and escaping symlinks fail before model
setup. The rendered instruction hash is used by planning, admission and jobs.
Manifests retain full base/resource/rendered bytes and reload verifies their
binding without consulting current package files. Historical plain-prompt
serialization remains unchanged. Both adapters use the shared message serializer;
only native inference was performed in this experiment.

## Verification

The full offline gate passed 906 tests, Ruff lint/format, strict mypy, frozen gold
validation and preflight. Nineteen focused cases cover exact rendering/order,
plain-prompt compatibility, missing/altered/escaping resources, saved-content
tampering, real CLI admission/generation/export/reload, shared messages and
contract-valid fictional examples. These are bounded regression checks, not a
proof of model quality. Python and evidence processing ran in Docker; native
Ollama executed the model. No host Python packages or dependencies were added.

All ten complete initial requests passed non-generating admission. Maximum prompt bound: 9,032; minimum context headroom after the output allowance: 23,736. Every actual request, including any schema correction, is admitted separately.

## Measured results

Run: `gemma-examples-v2-gold-20261027-731`; configuration: `config/gemma-examples.yaml`.

Counts retain every input, failure and extra-row penalty. Processing time sums
input durations including bounded retries/schema corrections, excluding setup.
Hardware state and caches differ; timing is observational.

| Variant | Valid / 10 | Matched fields | Accuracy | Exact docs | Extra / missing rows | Calls | Processing seconds |
| --- | ---: | --- | ---: | ---: | --- | ---: | ---: |
| Saved scoped primary | 10 | 295/366 | 80.60% | 1 | 3 / 0 | 10 | 116.67 |
| Loaded examples | 10 | 296/390 | 75.90% | 2 | 6 / 0 | 10 | 129.89 |

Matched fields changed by **+1**; extra-row penalties may also change the denominator. Expected-present matches: 186/197; expected-null matches: 110/145. Corrected inputs under the shared schema policy: 0.

| Input | Scoped matches | Examples matches | Extra / missing rows | Exact | Status | Seconds |
| --- | --- | --- | --- | --- | --- | ---: |
| B02-S002-PO01 | 12/15 | 12/15 | 0 / 0 | False | succeeded | 18.34 |
| B02-S003-PO01 | 10/39 | 10/39 | 3 / 0 | False | succeeded | 10.48 |
| B02-S012-PO01 | 13/15 | 12/39 | 3 / 0 | False | succeeded | 9.27 |
| B02-S016-PO01 | 12/15 | 15/15 | 0 / 0 | True | succeeded | 5.62 |
| B02-S021-PO01 | 15/15 | 15/15 | 0 / 0 | True | succeeded | 5.25 |
| B02-S032-PO01 | 98/111 | 98/111 | 0 / 0 | False | succeeded | 28.57 |
| B02-S040-PO01 | 84/95 | 83/95 | 0 / 0 | False | succeeded | 22.64 |
| B02-S044-PO01 | 24/31 | 24/31 | 0 / 0 | False | succeeded | 20.70 |
| B02-S011-PO01 | 13/15 | 13/15 | 0 / 0 | False | succeeded | 4.22 |
| B02-S023-PO01 | 14/15 | 14/15 | 0 / 0 | False | succeeded | 4.80 |

| Field | Present matches | Null matches |
| --- | --- | --- |
| purchaseOrderNumber | 6/6 | 2/4 |
| purchaseOrderDateTime | 9/10 | 0/0 |
| buyerName | 8/8 | 2/2 |
| shipToInfo | 5/5 | 5/5 |
| paymentTerms | 3/3 | 7/7 |
| buyerCurrency | 5/5 | 5/5 |
| totalValue | 2/2 | 8/8 |
| lineItems/*/purchaseOrderLineNumber | 3/4 | 30/30 |
| lineItems/*/buyerProductIdentifier | 1/1 | 1/33 |
| lineItems/*/buyerProductName | 32/34 | 0/0 |
| lineItems/*/buyerProductQuantity | 32/34 | 0/0 |
| lineItems/*/buyerProductUOM | 34/34 | 0/0 |
| lineItems/*/quantityUnit | 30/34 | 0/0 |
| lineItems/*/buyerUnitPrice | 14/14 | 20/20 |
| lineItems/*/buyerDeliveryDate | 2/3 | 30/31 |

Checked selected fictional PO numbers, buyer/product names and buyer code in retained extractions. Findings: `[]`. No prediction was filtered or repaired before scoring. This marker check does not prove the absence of all possible example influence or leakage.

## Interpretation and next boundary

This package is not preferred over the saved scoped primary on this observation:
matched fields increased by only one (295 to 296), while extra rows increased
from three to six and field accuracy fell from 80.60% to 75.90%. S012 produced
four rows instead of one; S003 retained its existing three extra rows. Exact
documents increased from one to two, so the result is mixed rather than a
regression on every metric. Expected-present matches fell from 188/197 to
186/197; expected-null matches rose from 107/145 to 110/145. Processing increased
from 116.67s to 129.89s. Keep the package as measured negative evidence; do not
promote it or silently tune it after observing this run. This does not establish
that all synthetic examples, skill content or local models are ineffective.

Judge gains by matches, exact documents, row errors, validity and processing time
together. A skill package gives no extra reasoning capability beyond its actual
rendered content, and a negative result must be retained without revising the
examples and attributing it to the original run. Do not pool favorable fields
from this trial and saved alternatives into an unmeasured extraction.

The earlier identifier-correction pipeline reached 309/366 (84.43%), two exact
documents with nine additional correction calls and 269.38s reconstructed total
processing. That is a separate workflow reference, not the instruction-only
baseline and not measured live end-to-end time.

Gold10 was reused for development. One pass cannot establish stability, unseen
layout reliability, model-independent skill effectiveness or whole-document
acceptance. Further independent evaluation needs separately reviewed documents
and frozen content/policy. Stop for review before another example variant,
remaining20, behavioral correction or provider/JEV work.

The provider ledger and saved baselines stayed byte-for-byte unchanged. Native
API cost was zero, excluding hardware/electricity/human time. Empty native
residency was verified after unload. Historical matrix membership remains
240/240; this trial is separately identified.

## Evidence

- [Archive index](../../archive-index/2a0b237b4c0a68764df194c794ca27f1b4ef4c2e19c9ab463b501689a3c36e6e.json).
- [Garage upload/full GET receipt](../../archive-index/2a0b237b4c0a68764df194c794ca27f1b4ef4c2e19c9ab463b501689a3c36e6e.remote.json).
- [Restore and evaluation verification](../../archive-index/2a0b237b4c0a68764df194c794ca27f1b4ef4c2e19c9ab463b501689a3c36e6e.verification.json).

Selection `gemma-examples` retains the exact package, content hashes, rendered
instructions, source evidence, admissions, requests/responses, implementation
and test snapshots, drivers, logs and evaluations. All restored bytes matched;
all seven standard gold10 evaluations and the prior correction evaluation
reproduced exactly. Bulk evidence stays ignored by Git. Garage and its cache
remain on this laptop.
