# Gemma selection with raw fallback: gold10

## Scope and controls

On 26 October 2026 the user requested committing the completed source-support
work and proceeding with the proposed hybrid. The earlier implementation,
results and archive provenance were committed as `ac1d5cf` before this change.
This continuation generated exactly ten new native observations, not a composite
of the best saved outputs. The three earlier gold10 trials are reused unchanged.
Required matrix membership remains 240/240.

`config/gemma-raw-fallback.yaml` selects the distinct
`ordered-rows-raw-fallback-v1` identity. It retains the existing source-only
selector and rendered body for supported layouts. When that selector abstains,
the request receives the exact original approved text, including line endings.
No new layout rules were added. Selection still excludes only known explicit
blank catalog rows, preserves order, duplicate products and shared cells, and
abstains for ambiguous quantities or additional order evidence.

Frozen v2, approved inputs/gold/schema/scorer, Gemma4 e4b-it-qat native artifact,
49,152 context, 16,384 output tokens, temperature 0/top_p 1, thinking=false,
deadlines, retries and bounded schema correction remain unchanged. Runtime,
digest and tokenizer were checked against the saved selected-source run.
No gold answers enter selection or requests. Python and verification execute
in Docker; inference uses native desktop Ollama, not Docker Ollama.

## Preparation and tests

All ten full initial requests passed non-generating admission. Three selected
request bodies matched the saved selected-source trial exactly; the other seven
matched their approved raw source bytes. The hybrid keeps its own identity even
where a body equals an earlier variant. Original text, rendered source, hashes,
maps, decisions and implementation identity accompany each new run.

The full offline gate passed 824 tests, Ruff lint/format, strict mypy, gold
validation and preflight. The nine new cases cover selected-body equivalence,
exact raw preservation, uncertain quantities, marked rows with null quantities,
tamper rejection and actual CLI generation/evaluation. Historical saved-run
evaluations were also reproduced without rewriting their records.

Maximum prompt bound: 7,655 tokens. Minimum context headroom after the 16,384 output allowance: 25,113 tokens.

## Measured comparison

Processing time sums attempted input durations, including corrections/retries,
and excludes setup/loading. Host activity and caches differ; these are observed
timings, not a controlled hardware benchmark. Extra rows add incorrect field
comparisons; matched counts, validity and exact documents accompany percentages.

| Trial | Valid / 10 | Matched fields | Accuracy | Exact docs | Extra / missing rows | Calls | Processing time |
| --- | ---: | --- | ---: | ---: | --- | ---: | --- |
| Saved raw baseline | 10 | 198/2766 | 7.16% | 1 | 303 / 0 | 10 | 14m 00s |
| Full cell records | 9 | 144/2910 | 4.95% | 1 | 321 / 13 | 10 | 20m 14s |
| Selection + full-cell fallback | 10 | 277/1214 | 22.82% | 1 | 109 / 0 | 10 | 4m 50s |
| Selection + raw fallback | 10 | 282/366 | 77.05% | 1 | 3 / 0 | 10 | 1m 53s |

The new hybrid matched 282 fields versus the saved raw baseline's 198 (+84). Present fields: 186/197; expected-null fields: 96/145. First-valid outputs: 10/10; corrected inputs: 0.

### Per-input hybrid results

| Input | Source branch | Matched fields | Extra / missing rows | Exact | Status | Seconds |
| --- | --- | --- | --- | --- | --- | ---: |
| B02-S002-PO01 | Raw fallback | 12/15 | 0 / 0 | False | succeeded | 12.0 |
| B02-S003-PO01 | Raw fallback | 10/39 | 3 / 0 | False | succeeded | 10.2 |
| B02-S012-PO01 | Raw fallback | 13/15 | 0 / 0 | False | succeeded | 4.2 |
| B02-S016-PO01 | Selected | 13/15 | 0 / 0 | False | succeeded | 5.0 |
| B02-S021-PO01 | Raw fallback | 15/15 | 0 / 0 | True | succeeded | 4.6 |
| B02-S032-PO01 | Selected | 97/111 | 0 / 0 | False | succeeded | 27.5 |
| B02-S040-PO01 | Selected | 71/95 | 0 / 0 | False | succeeded | 22.4 |
| B02-S044-PO01 | Raw fallback | 24/31 | 0 / 0 | False | succeeded | 18.6 |
| B02-S011-PO01 | Raw fallback | 13/15 | 0 / 0 | False | succeeded | 4.0 |
| B02-S023-PO01 | Raw fallback | 14/15 | 0 / 0 | False | succeeded | 4.7 |

### Expected-field errors remaining

The following counts use expected gold positions only, separating present and
null fields. Extra-row penalties remain included in the headline score above.

| Field | Present matches | Null matches | Incorrect expected fields |
| --- | --- | --- | ---: |
| purchaseOrderNumber | 6/6 | 3/4 | 1 |
| purchaseOrderDateTime | 10/10 | 0/0 | 0 |
| buyerName | 8/8 | 2/2 | 0 |
| shipToInfo | 5/5 | 5/5 | 0 |
| paymentTerms | 3/3 | 7/7 | 0 |
| buyerCurrency | 5/5 | 5/5 | 0 |
| totalValue | 2/2 | 8/8 | 0 |
| lineItems/*/purchaseOrderLineNumber | 3/4 | 30/30 | 1 |
| lineItems/*/buyerProductIdentifier | 1/1 | 0/33 | 33 |
| lineItems/*/buyerProductName | 32/34 | 0/0 | 2 |
| lineItems/*/buyerProductQuantity | 33/34 | 0/0 | 1 |
| lineItems/*/buyerProductUOM | 34/34 | 0/0 | 0 |
| lineItems/*/quantityUnit | 30/34 | 0/0 | 4 |
| lineItems/*/buyerUnitPrice | 12/14 | 20/20 | 2 |
| lineItems/*/buyerDeliveryDate | 2/3 | 16/31 | 16 |

## Interpretation and review gate

Only S016, S032 and S040 are eligible for deterministic selection. This trial
does not demonstrate autonomous tool use or general source understanding by the
model. Unsupported layouts remain subject to the raw model's errors. Gold10 is
development data; the layout rules and fallback were chosen after reviewing
earlier outcomes. One new pass is not a held-out reliability or stability test.

The comparison isolates a source-processing policy with unchanged prompt and
generation controls. Equal request bodies do not guarantee equal outputs on
every repetition; caching and native execution can vary. Review row membership
separately from buyer/supplier identifier roles, unit normalization, linked dates
and null semantics. Correct row selection alone cannot certify all PO fields.

The main remaining expected-field errors are specific: all 33 expected-null
buyer product identifiers were populated, and delivery dates had 16 mismatches
(15 expected-null fields and one present value). Together these account for
49 of the 60 mismatches on expected gold fields. The model also matched the one
legitimate buyer identifier, so universally nulling identifiers would destroy
correct evidence. S003 contributes all three extra rows.

The next proposed focus is source evidence for identifier ownership and explicit
line-date linkage, with abstention and legitimate-value counterexamples, rather
than increasing context/output again. Those checks would be a separate scoped
semantic experiment; no output was silently repaired and no new rules were
added in this trial.

No remaining20, provider/JEV inference, new examples or expanded layout rules
were run. Stop for user review before choosing a corpus continuation or another
semantic intervention. Required matrix observations are unchanged; optional
workflow trials remain separately identified.

## Reproducibility

The provider ledger remained byte-for-byte unchanged. Native API cost is zero,
excluding hardware/electricity/time. The model was explicitly unloaded and empty
residency verified. Raw payloads and detailed evaluations remain ignored by Git.

- [Archive index](../../archive-index/095895db1cfb618b9c7062f65d56259af42efa2fd298d143aa09f1af27927be6.json).
- [Garage upload/full GET receipt](../../archive-index/095895db1cfb618b9c7062f65d56259af42efa2fd298d143aa09f1af27927be6.remote.json).
- [Restored payload and four-evaluation verification](../../archive-index/095895db1cfb618b9c7062f65d56259af42efa2fd298d143aa09f1af27927be6.verification.json).

Archive selection: `gemma-raw-fallback`. Every source/restored payload matched,
all four gold10 evaluation reports reproduced exactly, and membership remained
240/240. The archive retains the new run, prior comparators, source snapshots,
configurations, admission, drivers and full offline/execution logs. Garage and
the archive cache are local storage on this machine.
