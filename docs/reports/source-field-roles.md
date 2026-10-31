# Source-role evidence and Gemma advisory-context gold10

**Decision: retain the offline checks; do not adopt this context variant.**
The role-context trial scored 23.98% with 111 extra rows in 5m01s, versus the
saved hybrid's 77.05%, three extra rows and 1m53s. The previous raw-fallback
hybrid remains the preferred measured local workflow. All settings and prior
results remain available; no default configuration was changed.

## Scope and controls

After committing the raw-fallback workflow as `d11c43d`, the user requested
proceeding with the next proposed source-evidence work. This continuation first
implemented offline buyer identifier ownership and line-delivery-date checks,
then tested one separate advisory-context intervention on the same gold10.
No source/gold/schema/scorer changes, provider calls or remaining20 were included.

The source checker recognizes a declared neutral-cell vocabulary. Generic
article/product codes, supplier codes and barcodes do not establish buyer
ownership. Explicit buyer-code labels identify the value for that product.
Delivery dates on the product's own row identify line linkage; separate header
delivery/service dates do not. Unknown labels/free text, shared/unlinked critical
cells, conflicting values, unfamiliar date formats and ambiguous output/product
matches require abstention. It does not infer external customer master data.

`config/gemma-field-roles.yaml` selects `ordered-rows-field-roles-v1`. It preserves
the existing hybrid's selected/raw body and appends source-derived role rules,
explicit line evidence and order-only date context when scope can be resolved.
Actual source values are retained; no gold values, prior predictions or synthetic
worked examples enter requests. The audit is independent of input IDs.

The v2 instruction file remains frozen, but the added role cues change model
context: this is a separate optional workflow, not a prompt-only matrix result.
The model consumes the evidence through the user-context message; no skill
discovery, tool loop, training or automatic field repair is implemented. Semantic
flags do not trigger rejection or another correction call in this experiment.

Gemma4 e4b-it-qat, native runtime/digest/tokenizer, thinking=false, temperature
0/top_p 1, 49,152 context, 16,384 output, deadlines, retry and bounded schema
correction controls match the saved hybrid. Native Ollama performs inference;
application execution, checking and archival use Docker. Exactly ten new
observations ran; all four saved comparators were reused without regeneration.

## Offline assessment and verification

All ten frozen gold outputs passed the two field checks without a contradiction.
The legitimate buyer-owned code and three line-linked dates were supported.
Saved Gemini v2 gold outputs also had no contradictory findings. On uniquely
gold-name-matched fields in the saved Gemma trials, no correct values were
flagged and no observed mismatches went unflagged; unmatched/ambiguous products
remain outside that comparison. Full per-run denominators and unknown findings
are retained in the assessment summary. This is development agreement, not
held-out precision/recall or new human review of diagnostic labels.

The full gate passed 847 tests, Ruff lint/format, strict mypy, gold validation
and preflight. The 23 new cases cover legitimate and missing roles, null
counterexamples, ambiguous scope, unknown labels, shared cells, date formats,
duplicate/paraphrased names, input immutability, view provenance tampering and
real CLI generation with an unchanged system prompt. The existing no-gold
assessment test also passed with the extended report.

All ten initial requests passed non-generating admission. Each body retained its saved hybrid prefix exactly and added only the recorded cue. Maximum prompt bound was 7,872 tokens; minimum remaining context after output allowance was 24,896.

## Measured results

Processing time sums input durations, including correction/retry work, excluding
setup/loading. Hardware activity and caches differ; timings are observational.
Extra output rows add incorrect comparisons. Matched counts, exact documents,
validity and row errors accompany the percentages.

| Trial | Valid / 10 | Matched fields | Accuracy | Exact docs | Extra / missing rows | Calls | Processing time |
| --- | ---: | --- | ---: | ---: | --- | ---: | --- |
| Saved raw baseline | 10 | 198/2766 | 7.16% | 1 | 303 / 0 | 10 | 14m 00s |
| Full cell records | 9 | 144/2910 | 4.95% | 1 | 321 / 13 | 10 | 20m 14s |
| Selection + cell fallback | 10 | 277/1214 | 22.82% | 1 | 109 / 0 | 10 | 4m 50s |
| Selection + raw fallback | 10 | 282/366 | 77.05% | 1 | 3 / 0 | 10 | 1m 53s |
| Hybrid + source-role context | 10 | 295/1230 | 23.98% | 1 | 111 / 0 | 10 | 5m 01s |

The role-context trial matched 295 fields versus the hybrid's 282 (+13). Present values: 183/197; expected-null values: 112/145. First-valid inputs: 10/10; corrected inputs: 0.

### Target fields and legitimate values

| Trial | Buyer code present | Buyer code null | Line date present | Line date null |
| --- | --- | --- | --- | --- |
| Selection + raw fallback | 1/1 | 0/33 | 2/3 | 16/31 |
| Hybrid + source-role context | 1/1 | 4/33 | 2/3 | 29/31 |

### Per-input outcomes

| Input | Hybrid matches | Role-context matches | Extra / missing rows | Exact | Status | Seconds |
| --- | --- | --- | --- | --- | --- | ---: |
| B02-S002-PO01 | 12/15 | 13/15 | 0 / 0 | False | succeeded | 13.6 |
| B02-S003-PO01 | 10/39 | 11/39 | 3 / 0 | False | succeeded | 10.7 |
| B02-S012-PO01 | 13/15 | 14/15 | 0 / 0 | False | succeeded | 4.8 |
| B02-S016-PO01 | 13/15 | 12/15 | 0 / 0 | False | succeeded | 5.2 |
| B02-S021-PO01 | 15/15 | 15/31 | 2 / 0 | False | succeeded | 9.6 |
| B02-S032-PO01 | 97/111 | 98/111 | 0 / 0 | False | succeeded | 28.4 |
| B02-S040-PO01 | 71/95 | 84/95 | 0 / 0 | False | succeeded | 22.8 |
| B02-S044-PO01 | 24/31 | 19/879 | 106 / 0 | False | succeeded | 195.5 |
| B02-S011-PO01 | 13/15 | 14/15 | 0 / 0 | False | succeeded | 4.7 |
| B02-S023-PO01 | 14/15 | 15/15 | 0 / 0 | True | succeeded | 5.7 |

### Remaining expected-field errors

Counts below use expected gold positions only; headline percentages also
penalize extra rows. A source-field audit can support individual values on an
extra catalog row without certifying that the row belongs to the order.

| Field | Present matches | Null matches | Incorrect expected fields |
| --- | --- | --- | ---: |
| purchaseOrderNumber | 6/6 | 3/4 | 1 |
| purchaseOrderDateTime | 10/10 | 0/0 | 0 |
| buyerName | 8/8 | 2/2 | 0 |
| shipToInfo | 5/5 | 5/5 | 0 |
| paymentTerms | 3/3 | 7/7 | 0 |
| buyerCurrency | 5/5 | 4/5 | 1 |
| totalValue | 2/2 | 8/8 | 0 |
| lineItems/*/purchaseOrderLineNumber | 3/4 | 30/30 | 1 |
| lineItems/*/buyerProductIdentifier | 1/1 | 4/33 | 29 |
| lineItems/*/buyerProductName | 30/34 | 0/0 | 4 |
| lineItems/*/buyerProductQuantity | 30/34 | 0/0 | 4 |
| lineItems/*/buyerProductUOM | 34/34 | 0/0 | 0 |
| lineItems/*/quantityUnit | 30/34 | 0/0 | 4 |
| lineItems/*/buyerUnitPrice | 14/14 | 20/20 | 0 |
| lineItems/*/buyerDeliveryDate | 2/3 | 29/31 | 3 |

## Interpretation and review gate

The target-field gains were outweighed by structural regressions. S044 changed
from three ordered rows to all 109 source rows, adding 106 catalog rows. S021,
previously exact, returned three rows instead of one. S003 retained its three
extra rows. These explain all 111 extras. Some individual fields improved,
especially line-date null handling, but total extraction quality and time
regressed. Additional context is not automatically helpful to this model.

The failed trial does not invalidate the source checks: their offline controls
and the model's ability to use their rendered context are different properties.
The experiment changed both source evidence presentation and advisory rules;
one pass cannot isolate the exact mechanism of the row regressions. Do not
silently remove the added rows or combine the best fields from saved trials.

There is a concrete cue-design limitation in S021. Its raw source has a buyer
code on the one ordered row and on two catalog rows whose quantities are blank.
The role renderer listed all three as explicit source-field evidence without
qualifying order membership. Those facts are individually true, but presenting
them as line-role guidance can promote non-ordered rows. The trial therefore
does not establish that Gemma cannot use correctly scoped role cues. This
profile is frozen as measured and is not promoted; correcting that scope would
be a separately identified intervention. Future rendering tests need catalog
rows with legitimate buyer codes as counterexamples, alongside ordered rows
with legitimate unknown quantities. Do not add a universal non-null filter.

These checks cover two semantic roles, not whole-document correctness. Passing
them is insufficient to accept a PO, route it without review or claim 100%
accuracy. Row membership, units, prices, party/order identity and other fields
remain independently assessable. Unknown findings are abstentions, not passes.
No generated fields were silently nulled or repaired; every new extraction came
from an actual recorded model call and retained its original raw response.

Gold10 is development data used to select these conventions. This single pass
is not an unseen-document reliability estimate or stability test. Assess field
counts and exact documents together with time/calls before choosing another
intervention or independently reviewed evaluation data. No automatic semantic
rejection/correction, JEV/provider work, remaining20 or second native trial is
authorized by completion. Stop for user review.

The next candidate, if requested, is a separately scoped bounded correction
workflow starting from the stronger raw-fallback output and using source checks
as evidence. It would need explicit intermediate/final provenance, limits on
additional calls, preservation of legitimate values and a fresh matched
comparison. It is not implemented or run here. New independently reviewed
documents would also be needed before treating development-set gains as
reliability evidence.

## Retained evidence

The provider ledger remained byte-for-byte unchanged; the model was unloaded
and empty residency verified. Native API cost is zero, excluding machine,
electricity and time. Verbose assessments/raw responses remain ignored by Git.

- [Archive index](../../archive-index/4cc0e7a3ab9e9fe99edf3c30a359fd6c9ecdd2c80cec2bfc40711b644257fb4f.json).
- [Garage upload and full GET verification](../../archive-index/4cc0e7a3ab9e9fe99edf3c30a359fd6c9ecdd2c80cec2bfc40711b644257fb4f.remote.json).
- [Restored-payload and five-evaluation verification](../../archive-index/4cc0e7a3ab9e9fe99edf3c30a359fd6c9ecdd2c80cec2bfc40711b644257fb4f.verification.json).

Selection: `field-roles`. All restored payloads matched originals, all five
gold10 evaluation reports reproduced exactly and required matrix membership
remained 240/240. The archive contains source-label inventory, gold development
controls, saved-run findings and hashes, admission, source/cue identities,
configuration, implementation snapshots, drivers and execution/full-check logs.
Garage and its cache remain local to this laptop.
