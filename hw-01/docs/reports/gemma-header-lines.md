# Gemma: independent header and line-item extraction on gold10

## Question and design

The user requested a matched native Gemma experiment splitting headers from
line items after reviewing the uneven header/line accuracy. The existing scoped
gold10 primaries are the comparator. Ten new documents receive two sequential
independent stage calls, then deterministic assembly by disjoint field ownership.
The baseline predictions are never sent to either stage. Neither stage receives
the other's output. No examples, semantic correction, source cropping, prompt
trimming, row chunking or new layout rules are part of this intervention.

Both stages receive each input's exact saved scoped source body, including its
selected/raw fallback behavior. Frozen v2 remains an exact instruction prefix;
a stage-specific suffix restricts the output scope. Business rules remain in
the prefix even when relevant only to the other stage. This tests output-task
decomposition, not a minimal header-only/line-only business prompt.

The header schema projects the authoritative seven top-level header properties;
the line schema projects its existing lineItems definition. Each keeps original
field types, required keys, nullability, date formats and item constraints.
Derived schemas have distinct hashes; the authoritative parent file/hash and
scorer stay unchanged. No second handwritten PO model was introduced. The final
PO is composed from the two actual disjoint stage outputs and validated against
the full parent schema. If either stage fails, the final PO is unavailable;
valid partial evidence remains, with no fallback to a previous run or field repair.

## Controls, bounds and verification

Native Gemma4 e4b-it-qat retains runtime 0.40.7, the same digest/tokenizer,
49,152 context, thinking=false and temperature 0/top_p 1. Stage calls retain
the baseline's 16,384 output allowance and its bounded schema-correction,
transport retry, request-timeout and per-stage input deadline. Both coordinators
share one dependency-stop state. Provider and Docker adapters are rejected.

There are twenty primary stage jobs rather than ten whole-PO jobs. Combined
primary output allowance is 32,768 per document. At most eighty physical calls
are configured including schema corrections/transport retries. Each stage has
a 7,205s input deadline; their configured sum is 14,410s plus orchestration
overhead, not a shared aggregate timer. These aggregate ceilings differ from the
one-call baseline. Actual tokens/time/calls are measured below, not assumed equal.

Python, verification and archiving run in Docker; inference uses native Ollama.
The full offline gate passed 927 tests, Ruff lint/format, strict mypy, frozen
gold validation and preflight. Twenty-one focused cases cover derived-schema
constraints and ownership, independent full-source calls, partial failure,
schema correction, stage-specific admission, shared dependency stops, native-only
guards, real loopback HTTP, gold-independent execution, export/offline CLI,
tampered evidence and failure-aware evaluation populations. Passing tests do
not prove model accuracy or complete test coverage.

Twenty initial stage requests passed non-generating admission. Maximum prompt bound: 7,450; minimum remaining context after output allowance: 25,318. Every actual request, including any schema correction, is admitted separately.

Run: `gemma-header-lines-gold-20261027-732`. Policy: `header-lines-split-v1`. Configuration: `config/gemma-scoped-roles.yaml`.

## Complete-input results

Accuracy scores the assembled whole PO on all ten gold documents. If either
stage fails, no successful partial field subset is substituted. Extra rows add
incorrect comparisons. Stage operation counts remain separate from document
counts. Processing sums measured complete-input durations, including both stages;
it excludes setup/loading and is not reconstructed from old outputs.

| Variant | Valid / 10 | Matched fields | Accuracy | Header matches | Line matches | Exact docs | Extra / missing rows | Calls | Seconds |
| --- | ---: | --- | ---: | --- | --- | ---: | --- | ---: | ---: |
| Saved scoped whole-PO | 10 | 295/366 | 80.60% | 68/70 | 227/296 | 1 | 3 / 0 | 10 | 116.67 |
| Independent headers + lines | 10 | 278/366 | 75.96% | 69/70 | 209/296 | 1 | 3 / 1 | 20 | 148.01 |

| Stage | First / final valid | Calls | Processing seconds | p50 / p95 seconds |
| --- | --- | ---: | ---: | --- |
| headers | 10 / 10 | 10 | 55.18 | 4.24 / 13.49 |
| lines | 10 / 10 | 10 | 92.62 | 4.43 / 23.69 |

| Input | Baseline matches | Split matches | Extra / missing rows | Exact | Header seconds | Line seconds | Total seconds |
| --- | --- | --- | --- | --- | ---: | ---: | ---: |
| B02-S002-PO01 | 12/15 | 12/15 | 0 / 0 | False | 10.47 | 4.61 | 15.10 |
| B02-S003-PO01 | 10/39 | 10/39 | 3 / 0 | False | 4.73 | 7.98 | 12.72 |
| B02-S012-PO01 | 13/15 | 13/15 | 0 / 0 | False | 2.55 | 3.02 | 5.58 |
| B02-S016-PO01 | 12/15 | 14/15 | 0 / 0 | False | 3.33 | 3.35 | 6.74 |
| B02-S021-PO01 | 15/15 | 15/15 | 0 / 0 | True | 2.65 | 2.71 | 5.38 |
| B02-S032-PO01 | 98/111 | 98/111 | 0 / 0 | False | 5.03 | 23.69 | 28.74 |
| B02-S040-PO01 | 84/95 | 73/95 | 0 / 0 | False | 4.24 | 23.10 | 27.35 |
| B02-S044-PO01 | 24/31 | 17/31 | 0 / 1 | False | 13.49 | 16.47 | 29.97 |
| B02-S011-PO01 | 13/15 | 12/15 | 0 / 0 | False | 4.01 | 4.43 | 8.45 |
| B02-S023-PO01 | 14/15 | 14/15 | 0 / 0 | False | 4.68 | 3.27 | 7.97 |

| Field | Present matches | Null matches |
| --- | --- | --- |
| buyerCurrency | 5/5 | 5/5 |
| buyerName | 8/8 | 2/2 |
| lineItems/*/buyerDeliveryDate | 2/3 | 16/31 |
| lineItems/*/buyerProductIdentifier | 1/1 | 1/33 |
| lineItems/*/buyerProductName | 32/34 | 0/0 |
| lineItems/*/buyerProductQuantity | 32/34 | 0/0 |
| lineItems/*/buyerProductUOM | 33/34 | 0/0 |
| lineItems/*/buyerUnitPrice | 14/14 | 19/20 |
| lineItems/*/purchaseOrderLineNumber | 3/4 | 27/30 |
| lineItems/*/quantityUnit | 29/34 | 0/0 |
| paymentTerms | 3/3 | 7/7 |
| purchaseOrderDateTime | 10/10 | 0/0 |
| purchaseOrderNumber | 6/6 | 3/4 |
| shipToInfo | 5/5 | 5/5 |
| totalValue | 2/2 | 8/8 |

| Stage | Reported input tokens | Reported output tokens |
| --- | ---: | ---: |
| headers | 23974 | 745 |
| lines | 25254 | 2806 |

Matched fields changed by **-17**. Expected-present matches: 185/197; expected-null matches: 93/145. Measured complete-input processing: **148.01s**, versus the baseline's **116.67s**. Phase wall time including setup: **157.73s**.

## Interpretation and next boundary

This output-scope split is not preferred over the scoped whole-PO comparator on
this observation. It gained one header match but lost eighteen line matches,
giving seventeen fewer matched fields overall, the same one exact document and
31.34s more processing. S044 omitted one of its three ordered rows. Expected-null
line-date matches fell from 28/31 to 16/31; buyer-code null matches remained weak
at 1/33. These observed error classes matter more than schema validity alone.
Keep the frozen result as negative evidence rather than adopting the split or
combining its favorable headers with earlier line outputs.

Compare matched counts, header/line errors, exact documents, row membership,
validity and both-stage cost/time together. Separating output ownership does not
guarantee correct row selection or buyer-code semantics. A valid projected stage
does not establish factual correctness. The combined ceiling is larger and the
source is processed twice; this is a pipeline trade-off, not equal-compute proof
of a model capability change. Cache/hardware state and a reused single baseline
also limit causal timing claims.

Gold10 is development evidence, not a held-out reliability estimate. One pass
does not establish stability or the best possible stage-specific prompt. Keep
this frozen intervention distinct from later prompt trimming, source cropping,
chunking, example loading or semantic checks. Do not combine favorable fields
from this and saved alternatives to claim an executed result. No further run,
remaining20 or provider/JEV work is authorized by completion. Stop for review.

The provider ledger and saved baselines remained byte-for-byte unchanged. Native
API charges were zero, excluding hardware, electricity and human time. The model
was unloaded and empty residency verified. Historical matrix membership remains
240/240; these ten two-stage observations are separately identified.

## Retained evidence

- [Archive index](../../archive-index/693267625c687b930be9274c8b90f842d21d13071e21bb144a68ac3d67f44aed.json).
- [Garage upload/full GET receipt](../../archive-index/693267625c687b930be9274c8b90f842d21d13071e21bb144a68ac3d67f44aed.remote.json).
- [Restored comparison verification](../../archive-index/693267625c687b930be9274c8b90f842d21d13071e21bb144a68ac3d67f44aed.verification.json).

Selection `gemma-header-lines` retains both stage schemas, exact source/prompt
bindings, admissions/checkpoints, stage raw responses and failures, assembled
POs, original controls, implementation/test snapshots, drivers and logs. All
restored bytes matched. Seven historical standard gold10 evaluations, the prior
correction evaluation and the new split evaluation reproduced exactly. Bulk
evidence remains ignored by Git; Garage and its cache remain on this laptop.
