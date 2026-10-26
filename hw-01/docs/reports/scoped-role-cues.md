# Membership-scoped role cues: Gemma gold10

**Outcome: modest development-set improvement; review pending.** The scoped
policy matched 295/366 fields (80.60%) versus the hybrid's 282/366 (77.05%), with
the same three extra rows and one exact document. Processing was 1m57s versus
1m53s. This is a separately measured candidate; no default configuration changed.

## Scope and controls

The user approved committing the negative role-context experiment, adding scope
counterexamples and one matched scoped-cue gold10 trial. The previous work was
committed as `aeddae8` first. The failed unscoped profile remains reconstructible.
This continuation does not revise frozen v2, gold, inputs, schema or scorer.

`config/gemma-scoped-roles.yaml` selects the separate
`ordered-rows-scoped-roles-v1` profile. The unchanged row selector must confirm
order membership before any role cue is rendered. Field-role rows are intersected
with its exact retained product-cell references. Caller-supplied names or flags
cannot authorize membership. Catalog facts are not promoted into ordered-row
guidance. Ambiguous matching or unsupported membership receives no cue, retaining
the existing hybrid body; repeated ordered products are not deduplicated.

No layout rules or universal non-null quantity filter were added. A marked row
with an unknown quantity remains present on abstention. The existing role rules
and cue wording are reused; this isolates their exposure policy. Full source,
selection certificate, scope/cell references, role facts, cue text/hashes and
implementation identity accompany the manifest and are reconstructed on reload.

The three confirmed gold layouts receive scoped role cues; seven unsupported
layouts keep exact raw fallback. On this cohort the three rendered cue bodies
also match the earlier unscoped trial byte-for-byte, while the seven raw bodies
match the stronger hybrid exactly. All ten earlier unscoped bodies and audit
metadata were reconstructed unchanged after extracting the shared renderer.

Frozen v2 instruction bytes, native Gemma4 e4b-it-qat runtime/digest/tokenizer,
thinking=false, temperature 0/top_p 1, 49,152 context, 16,384 output, deadlines,
retry and bounded schema correction are unchanged. Added cues identify a separate
optional workflow, not another required matrix result. No gold/prior outputs or
synthetic examples enter request construction. Python and checks run in Docker;
native Ollama performs inference. Ten actual new observations ran; no best-case
combination of saved outputs substitutes for this measured policy trial.

## Offline assessment and verification

The source-role check development controls and legitimate-value counterexamples
from the preceding experiment remain available in the retained evidence. They
assess individual field roles, not whole-order correctness or held-out accuracy.

The full gate passed 855 tests, Ruff lint/format, strict mypy, gold validation
and preflight. Eight new cases exercise catalog rows with valid buyer codes,
unchanged selector rules, marked rows with unknown quantities, ambiguous names
and coordinates, scope-certificate tampering, confirmed-cell isolation and real
CLI fallback/evaluation separation. Existing role checks and legacy source-view
tests also passed. No source or output is silently deleted or repaired.

All ten requests passed non-generating admission: three cued requests over 25 confirmed product cells, seven exact raw fallbacks. Maximum prompt bound was 7,655 tokens; minimum remaining context after output allowance was 25,113.

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
| Unscoped role context | 10 | 295/1230 | 23.98% | 1 | 111 / 0 | 10 | 5m 01s |
| Membership-scoped role context | 10 | 295/366 | 80.60% | 1 | 3 / 0 | 10 | 1m 57s |

The scoped trial matched 295 fields versus the hybrid's 282 (+13). Present values: 188/197; expected-null values: 107/145. First-valid inputs: 10/10; corrected inputs: 0.

### Target fields and legitimate values

| Trial | Buyer code present | Buyer code null | Line date present | Line date null |
| --- | --- | --- | --- | --- |
| Selection + raw fallback | 1/1 | 0/33 | 2/3 | 16/31 |
| Unscoped role context | 1/1 | 4/33 | 2/3 | 29/31 |
| Membership-scoped role context | 1/1 | 0/33 | 2/3 | 28/31 |

### Per-input outcomes

| Input | Hybrid matches | Scoped-cue matches | Extra / missing rows | Exact | Status | Seconds |
| --- | --- | --- | --- | --- | --- | ---: |
| B02-S002-PO01 | 12/15 | 12/15 | 0 / 0 | False | succeeded | 12.9 |
| B02-S003-PO01 | 10/39 | 10/39 | 3 / 0 | False | succeeded | 10.2 |
| B02-S012-PO01 | 13/15 | 13/15 | 0 / 0 | False | succeeded | 4.5 |
| B02-S016-PO01 | 13/15 | 12/15 | 0 / 0 | False | succeeded | 5.5 |
| B02-S021-PO01 | 15/15 | 15/15 | 0 / 0 | True | succeeded | 5.0 |
| B02-S032-PO01 | 97/111 | 98/111 | 0 / 0 | False | succeeded | 28.1 |
| B02-S040-PO01 | 71/95 | 84/95 | 0 / 0 | False | succeeded | 22.4 |
| B02-S044-PO01 | 24/31 | 24/31 | 0 / 0 | False | succeeded | 19.1 |
| B02-S011-PO01 | 13/15 | 13/15 | 0 / 0 | False | succeeded | 4.2 |
| B02-S023-PO01 | 14/15 | 14/15 | 0 / 0 | False | succeeded | 4.8 |

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
| lineItems/*/buyerProductIdentifier | 1/1 | 0/33 | 33 |
| lineItems/*/buyerProductName | 32/34 | 0/0 | 2 |
| lineItems/*/buyerProductQuantity | 33/34 | 0/0 | 1 |
| lineItems/*/buyerProductUOM | 34/34 | 0/0 | 0 |
| lineItems/*/quantityUnit | 30/34 | 0/0 | 4 |
| lineItems/*/buyerUnitPrice | 14/14 | 20/20 | 0 |
| lineItems/*/buyerDeliveryDate | 2/3 | 28/31 | 4 |

## Interpretation and review gate

The scope guard avoided the preceding trial's structural regressions: S021
returned its one ordered row and S044 its three, instead of the unscoped
variant's three and 109. All three remaining extra rows are in S003. The score
denominator is the same 366 comparisons as the stronger hybrid, so the thirteen
additional matches are not a denominator-only gain.

The improvement is concentrated: S040 gained thirteen correct fields, S032 one,
and S016 lost one. The seven raw-fallback cases retained their earlier field
scores. Exact documents stayed 1/10. This is evidence for a narrowly gated
context policy on these development layouts, not broad reliability.

Expected-null date matches rose from 16/31 to 28/31. Buyer identifier ownership
did not improve: all 33 expected-null identifiers remain populated, although
the one legitimate identifier remains correct. Those 33 errors account for
most of the 47 remaining wrong expected gold fields. A future source-grounded
correction experiment should target that ownership evidence and preserve the
legitimate value, rather than universally nulling identifiers or changing
context/output allowances again. No such correction experiment ran here.

These checks cover two semantic roles, not whole-document correctness. Passing
them is insufficient to accept a PO, route it without review or claim 100%
accuracy. Row membership, units, prices, party/order identity and other fields
remain independently assessable. Unknown findings are abstentions, not passes.
No generated fields were silently nulled or repaired; every new extraction came
from an actual recorded model call and retained its original raw response.

Gold10 is development data used to select these conventions and the scope policy. This single pass
is not an unseen-document reliability estimate or stability test. Assess field
counts and exact documents together with time/calls before choosing another
intervention or independently reviewed evaluation data. No automatic semantic
rejection/correction, JEV/provider work, remaining20 or second native trial is
authorized by completion. Stop for user review.

## Retained evidence

The provider ledger remained byte-for-byte unchanged; the model was unloaded
and empty residency verified. Native API cost is zero, excluding machine,
electricity and time. Verbose assessments/raw responses remain ignored by Git.

- [Archive index](../../archive-index/912b2b9fe8f31fc6a690f2bcf31fc6e4d7eb670a86963a3ed922147e972fe2d7.json).
- [Garage upload and full GET verification](../../archive-index/912b2b9fe8f31fc6a690f2bcf31fc6e4d7eb670a86963a3ed922147e972fe2d7.remote.json).
- [Restored-payload and six-evaluation verification](../../archive-index/912b2b9fe8f31fc6a690f2bcf31fc6e4d7eb670a86963a3ed922147e972fe2d7.verification.json).

Selection: `scoped-roles`. All restored payloads matched originals, all six
gold10 evaluation reports reproduced exactly and required matrix membership
remained 240/240. The archive retains preceding controls/comparators and new
findings/hashes, admission, scope decisions, source/cue identities,
configuration, implementation snapshots, drivers and execution/full-check logs.
Garage and its cache remain local to this laptop.
