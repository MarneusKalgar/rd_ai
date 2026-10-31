# Gemma source-support gold10 experiment

## Scope and fixed controls

On 26 October 2026 the user requested committing the existing Qwen work, then
offline source-check assessment, one representation-only Gemma gold10 trial,
review and a separate staged-selection trial if row errors persisted. The
existing work was committed as `60fbdd1` before implementation. These optional
observations do not replace any part of the completed 240-observation matrix.

Both new trials use frozen v2, the same ten approved gold inputs and schema,
Gemma4 e4b-it-qat, the saved native digest/runtime/tokenizer, 49,152 context,
16,384 output tokens, temperature 0/top_p 1 and thinking=false. Existing
deadlines, retries and bounded schema correction remain unchanged. The scorer
and gold answers were not changed. The model runs in native Ollama; application
code, preparation, checks, evaluation and archival run in Docker.

`cell-records-v1` retains all source rows and literals, exposing each cell on a
separate line in its original record group. `ordered-rows-v1` adds a source-only
deterministic selection stage under three recognized order-form conventions.
Only explicit blank catalog rows are excluded; unsupported evidence retains
the full representation. Headers, shared unit cells, order and duplicate ordered
products are preserved. This is deterministic selection followed by extraction,
not an additional model call. Full original text, rendered source, hashes,
source map, exclusion decision and implementation identity accompany the run.
Gold answers never enter selection or request construction. See the
[source-support guide](../guides/source-support.md) for boundaries and commands.

## Offline evidence and admission

Assessment of all 120 saved native matrix observations read no gold answers.
Completeness was supported in seven, contradicted in four and unknown in 109.
Quantity findings were supported in 34, contradicted in 26 and unknown in 1,101.
The selector could apply in only twelve observations across the repeated three
recognized layouts; 108 retained full source. These populations differ from
the older per-output-row diagnostic and must not be combined as one accuracy.

For a separate development check, the three recognized gold sources contained
25 positively ordered rows and 443 explicit blank catalog rows. Selected
descriptions matched all 25 gold rows in order with no additional or missed
rows. This validates these development cases, not general held-out precision
or recall. A null quantity can be legitimate on other layouts; the selector
does not impose a universal non-null rule.

All ten representation requests passed non-generating render admission. The
maximum prompt bound was 20,769 tokens, leaving at least 11,999 context slots
after the output allowance. The existing 49,152 context was sufficient. The
full offline gate passed 815 tests, Ruff, strict mypy, gold validation and
preflight. Focused tests cover preservation, ambiguity, abstention, sheet
inheritance, shared context, duplicates, tampering and CLI execution.

## Measured results

The raw comparator is the saved native v2 gold10 run, not a newly rerun baseline.
Processing time sums input durations including corrections/retries and excludes
setup/model loading. Host activity and caching differ; timing is observational.

| Trial | Valid / 10 | Matched fields | Accuracy | Exact docs | Extra rows | Missing rows | Calls | Processing time |
| --- | ---: | --- | ---: | ---: | ---: | ---: | ---: | --- |
| Raw v2 baseline | 10 | 198/2766 | 7.16% | 1 | 303 | 0 | 10 | 14m 00s |
| Cell records only | 9 | 144/2910 | 4.95% | 1 | 321 | 13 | 10 | 20m 14s |
| Selected ordered rows + cell records | 10 | 277/1214 | 22.82% | 1 | 109 | 0 | 10 | 4m 50s |

Extra rows enlarge the denominator. Judge matched fields, exact documents,
missing rows and validity together with the percentage; shorter incorrect or
truncated outputs are not an improvement by themselves.

| Trial | Present fields | Null fields | First valid | Corrected inputs |
| --- | --- | --- | ---: | ---: |
| Raw v2 baseline | 103/197 | 95/145 | 10 | 0 |
| Cell records only | 79/197 | 65/145 | 9 | 0 |
| Selected ordered rows + cell records | 180/197 | 97/145 | 10 | 0 |

Cell records only matched 144 fields versus the saved baseline's 198 (-54), with 9/10 valid outputs.

Selected ordered rows + cell records matched 277 fields versus the saved baseline's 198 (+79), with 10/10 valid outputs.

### Recognized layouts and abstained layouts

These populations separate the three forms eligible for row selection from
the seven that retain their full representation. Field counts use the unchanged
exact scorer; they are not source-selector precision/recall estimates.

| Trial | Layout population | Matched fields | Valid | Extra / missing rows | Processing seconds |
| --- | --- | --- | ---: | --- | ---: |
| Raw v2 baseline | Recognized three | 97/2621 | 3 | 300 / 0 | 782.6 |
| Raw v2 baseline | Other seven | 101/145 | 7 | 3 / 0 | 57.5 |
| Cell records only | Recognized three | 48/1917 | 2 | 212 / 13 | 972.5 |
| Cell records only | Other seven | 96/993 | 7 | 109 / 0 | 241.2 |
| Selected ordered rows + cell records | Recognized three | 181/221 | 3 | 0 / 0 | 53.5 |
| Selected ordered rows + cell records | Other seven | 96/993 | 7 | 109 / 0 | 236.4 |

The pre-registered conditional selection gate was triggered: recognized-layout row errors or unusable output remain. Its decision and affected cases were saved after the representation trial and before any staged-selection generation.

### Per-input review

Each cell reports matched/comparison fields, extra/missing rows and input
processing seconds. Failures remain in the table and in the score population.

| Input | Raw baseline | Cell records | Selected rows |
| --- | --- | --- | --- |
| B02-S002-PO01 | 12/15; +0/−0; 12.0s (succeeded) | 13/15; +0/−0; 13.1s (succeeded) | 13/15; +0/−0; 12.1s (succeeded) |
| B02-S003-PO01 | 10/39; +3/−0; 10.3s (succeeded) | 10/39; +3/−0; 10.8s (succeeded) | 10/39; +3/−0; 10.3s (succeeded) |
| B02-S012-PO01 | 13/15; +0/−0; 4.3s (succeeded) | 12/15; +0/−0; 5.3s (succeeded) | 12/15; +0/−0; 5.0s (succeeded) |
| B02-S016-PO01 | 8/543; +66/−0; 141.7s (succeeded) | 9/543; +66/−0; 129.6s (succeeded) | 13/15; +0/−0; 4.4s (succeeded) |
| B02-S021-PO01 | 15/15; +0/−0; 4.4s (succeeded) | 15/15; +0/−0; 4.9s (succeeded) | 15/15; +0/−0; 4.4s (succeeded) |
| B02-S032-PO01 | 60/815; +88/−0; 272.1s (succeeded) | 0/111; +0/−13; 530.9s (failed) | 97/111; +0/−0; 27.1s (succeeded) |
| B02-S040-PO01 | 29/1263; +146/−0; 368.8s (succeeded) | 39/1263; +146/−0; 312.0s (succeeded) | 71/95; +0/−0; 22.0s (succeeded) |
| B02-S044-PO01 | 24/31; +0/−0; 18.2s (succeeded) | 19/879; +106/−0; 198.1s (succeeded) | 19/879; +106/−0; 195.8s (succeeded) |
| B02-S011-PO01 | 13/15; +0/−0; 3.6s (succeeded) | 13/15; +0/−0; 4.1s (succeeded) | 13/15; +0/−0; 4.0s (succeeded) |
| B02-S023-PO01 | 14/15; +0/−0; 4.6s (succeeded) | 14/15; +0/−0; 4.9s (succeeded) | 14/15; +0/−0; 4.8s (succeeded) |

Only S016, S032 and S040 match the declared selection layouts. Other sources
fall back to the same full cell-record representation. Repeated unknown-layout
outputs can vary even with temperature zero; differences there cannot be
attributed to row filtering. All ten cases are reported rather than selecting
the best outcomes. These gold cases are development data and one pass per
intervention does not establish reliability on unseen forms.

S044 is an important abstained case: its Spanish source has two product panels
with separate quantity columns. It falls outside the three declared profiles.
The existing agent-written annotation describes three positive ordered rows and 106 blank
catalog rows, but those annotations are explanatory agent-written notes, not a
new human review and not an input to the selector. Extending support to that
layout would be a separate intervention with explicit panel-order, shared-unit,
blank-quantity and ambiguity controls. It was not added after seeing trial
outputs, and no further inference was performed to optimize this result.

## Interpretation and next decision

Deterministic selection fixed row membership on the recognized three: zero
extra/missing rows, 181/221 matched fields and 53.5 seconds, versus 97/2621
matched fields and 782.6 seconds in their saved raw baseline. Field errors
remain even after correct selection; the workflow does not establish complete
purchase-order correctness.

The full cell-record format harmed an unsupported case. Raw S044 had no extra
rows and scored 24/31; both formatted trials included its 106 blank catalog
rows and scored 19/879. S003 contributes the other three extra rows. Thus the
109 remaining extras are explained by retained case-level evidence rather than
an unexplained aggregate score.

The next candidate for review is a separately identified hybrid: use selection
only when its narrow source rules apply, and preserve the original raw text
when they abstain. That avoids assuming the unsuccessful format is a safe
fallback. Such a hybrid has not been run, and mixing saved best-case outputs
would not constitute a measured hybrid result. Profile expansion, semantic
field checks and further corpus runs require their own reviewed scope.

## Retention and review gate

No provider inference ran and the provider ledger remained byte-for-byte
unchanged. Gemma was unloaded and empty residency verified after execution.
Full payloads, assessments, implementation snapshot, preparation, drivers,
logs and evaluations remain outside Git. Compact archive provenance is retained:

- [Archive index](../../archive-index/15c6edb330d05e608bb1542e719313cc3169579c8daca72d2e447c1f875eeddb.json).
- [Garage upload and full GET receipt](../../archive-index/15c6edb330d05e608bb1542e719313cc3169579c8daca72d2e447c1f875eeddb.remote.json).
- [Restored-payload and evaluation verification](../../archive-index/15c6edb330d05e608bb1542e719313cc3169579c8daca72d2e447c1f875eeddb.verification.json).

All source/restored payloads matched, all 3 gold10 evaluation reports
reproduced exactly, and required matrix membership remained 240/240. Selection:
`gemma-source-support`. Garage and its cache are local to this machine.

Stop for review. No remaining20, new prompt, examples, provider/JEV calls or
additional local inference are authorized by this completion. Review the
measured row/field trade-offs before deciding whether to expand a workflow.
