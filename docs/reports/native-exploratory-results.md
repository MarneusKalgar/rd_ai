# Native Gemma exploratory matrix continuation

## Authorized scope

The user authorized the remaining native observations after checked preparation:
30 v1 exploratory inputs, followed by the twenty v2 inputs disjoint from saved
gold10. Both use temperature 0.2, top_p 0.9, 16,384 output tokens, 49,152 native
context and thinking=false. The frozen prompts, schema, approved inputs/gold,
native model/digest/tokenizer and bounded retry/correction/deadline policy remain
unchanged. Python runs in Docker; model inference uses the native desktop app.

The ten v2 gold observations from `native-v2-gold-t02-p090-20261025` are reused
through the checked sampling-ID map. They are not rerun or relabeled. See the
[reuse and preparation report](matrix-exploratory-preparation.md). Provider
exploratory execution remains unapproved; this task creates no paid requests.

## Execution

Run IDs:

- `matrix-native-v1-exploratory-20261025-72`: all thirty approved inputs.
- `matrix-native-v2-exploratory-20261025-72`: exactly the twenty non-gold inputs.

The runner rechecked the native runtime and installed digest against preparation
before starting. Every actual request still passes full-context admission.
Records and checkpoints are persisted incrementally. Failed attempts remain
visible; output caps, timeouts and correction policy are not enlarged after a
failure. The provider ledger and the reused source hashes are checked unchanged
after each phase. Gemma is unloaded after the sequence.

## Verified terminal results

All fifty new inputs reached attempted terminal records. The checked v2 union
uses the ten existing gold observations once and twenty disjoint new non-gold
observations. Each native exploratory variant now contains all thirty inputs.
The scorer and original run records were not changed to improve results.
Baseline rows retain the [committed checkpoint](../../results/submission/v2-baseline-review-20261025/summary.json)
figures; exploratory rows are regenerated from checked terminal records. The
historical baseline budget-only policy revision remains disclosed separately.

| Prompt | Sampling | Final valid / 30 | Gold correct / comparisons | Gold accuracy | Exact gold docs | Extra gold rows | Processing time |
| --- | --- | --- | --- | ---: | ---: | ---: | --- |
| v1 | baseline, 0 / 1 | 29/30 | 164/3494 | 4.69% | 0 | 394 | 57m 56s |
| v1 | exploratory, 0.2 / 0.9 | 28/30 | 105/2542 | 4.13% | 0 | 275 | 58m 03s |
| v2 | baseline, 0 / 1 | 29/30 | 198/2766 | 7.16% | 1 | 303 | 43m 12s |
| v2 | exploratory, 0.2 / 0.9 | 30/30 | 197/2214 | 8.90% | 1 | 234 | 26m 52s |

For v2, the primary percentage rises while the correct-field count changes from 198 to 197. This is not a net increase in matched gold fields: extra-row penalties and failed predictions change the comparison denominator. Interpret the score together with validity and the retained failures.

The fifty new observations consumed **73m 09s** of summed input
processing time. The v2 exploratory row includes the reused gold10's measured
time; do not count it again as new execution. Times exclude setup/model loading,
and input duration includes any bounded retries/corrections. Output lengths,
cache state and host activity are not controlled hardware-throughput benchmarks.

Gold accuracy covers the same ten development cases. The other twenty inputs
per variant supply operations and post-hoc qualitative evidence, not new gold
labels. Extra returned rows add wrong field comparisons to the denominator;
failed outputs receive zero matches on their expected fields. Report correct
counts, validity and per-document row errors alongside headline percentages.

### New operational outcomes

| Prompt | First-valid / 30 | Final-valid / 30 | Physical calls | Corrected inputs | p50 input seconds | p95 input seconds |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| v1 | 28 | 28 | 30 | 0 | 21.729 | 500.241 |
| v2 | 30 | 30 | 30 | 0 | 20.148 | 225.909 |

Retained failures:

- v1 `B02-S004-PO01`: truncated; 16384 reported output tokens, 1 physical request(s).
- v1 `B02-S032-PO01`: truncated; 16384 reported output tokens, 1 physical request(s).
- v2: none.

### Detection-only source-row evidence

| Prompt | Supported returned rows | Contradicted returned rows | Unknown returned rows |
| --- | ---: | ---: | ---: |
| v1 | 12 | 212 | 771 |
| v2 | 9 | 247 | 320 |

These checks cover specific recognized source layouts and do not replace gold
scoring. Unknown is not a factual-error label. Diagnostics do not filter output,
reject returned rows or trigger correction. Full regenerable diagnostic files
remain ignored; their sizes and hashes are retained in the archived summary.

## Membership, spending and retained evidence

Required membership is now **180/240 covered**, including attempted failures.
All four native prompt/sampling variants are complete. The sixty provider
exploratory observations remain unexecuted and unapproved. Provider baseline
results and the other optional diagnostics are unchanged.

The provider ledger remained byte-for-byte unchanged; these runs made no paid
provider requests. Native API cost is zero, excluding machine/electricity/time.
Gemma was unloaded after completion and empty native residency was verified.

The [verified archive](../../archive-index/52651c481b8e315050e59090e9fe7be485633006fad89d03a91130d897a31420.json), [Garage receipt](../../archive-index/52651c481b8e315050e59090e9fe7be485633006fad89d03a91130d897a31420.remote.json)
and [restore verification](../../archive-index/52651c481b8e315050e59090e9fe7be485633006fad89d03a91130d897a31420.verification.json) retain
the complete required source provenance, the reused gold10, preparation and new
evaluations. Every source/restored payload matched; restored exploratory scores
reproduced the original reports exactly. The [full comparison](../../results/restored/52651c481b8e315050e59090e9fe7be485633006fad89d03a91130d897a31420/submission/native-exploratory-20261025-evaluation/summary.json)
and [240-slot membership](../../results/restored/52651c481b8e315050e59090e9fe7be485633006fad89d03a91130d897a31420/submission/native-exploratory-20261025-evaluation/membership.json)
are available after the standard archive retrieval workflow. Use selection
`native-exploratory-results` to package the original sources again.

No additional inference is scheduled or approved by this report. Section 7.2
still requires the provider exploratory phases; sections 8–9 retain final
reporting and reproducibility/acceptance work. Gold10 is development evidence,
not a held-out generalization estimate.
