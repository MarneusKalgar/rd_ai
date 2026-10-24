# Revised v1 baseline results

Verified 23 October 2026. Both models attempted all 30 frozen inputs using
unchanged v1, temperature 0, top_p 1 and a 16,384-token output allowance.
Native Gemma used 49,152 context and thinking=false. Flash retained its default
reasoning and provider-enforced context admission. These are distinct model
profiles, not an isolated test of model size or reasoning settings.

**Stop for user review:** no v2 creation, freezing or execution, and no
exploratory sampling, before further user direction. Section 7.2 remains open.

## Results

| Measurement | Gemini 3.5 Flash | Native Gemma4 E4B QAT |
| --- | ---: | ---: |
| Attempted inputs | 30/30 | 30/30 |
| Schema-valid final outputs | 30/30 | 29/30 |
| Physical inference calls | 30 | 30 |
| Gold field accuracy | 278/342 = **81.29%** | 164/3,494 = **4.69%** |
| Exact gold documents | 1/10 | 0/10 |
| Missing / extra gold line items | 0 / 0 | 0 / 394 |
| Header field accuracy | 66/70 = 94.29% | 61/70 = 87.14% |
| Line field accuracy | 212/272 = 77.94% | 103/3,424 = 3.01% |
| Input latency p50 / p95 | 11.983 / 33.568 seconds | 21.791 / 519.550 seconds |
| Sum of input durations | 7m 40.563s | 57m 55.918s |
| Known API cost | $1.20499515 | $0; machine costs excluded |

Quality is measured on **gold10 only**. Validity, latency and cost cover all30,
including the retained native failure. Duration sums combine reused and new
observations; they are not the wall-clock duration of one uninterrupted batch.
Gold10 has been used during development and is not a held-out test set.

Native S033 reached exactly 16,384 output tokens and was recorded as
`truncated`, after 532.952 seconds. It is outside gold10, so it affects validity
and latency but not the gold field score. No correction or retry ran for either
baseline. The continuation terminal state is complete because all selected
inputs were attempted; that does not imply every extraction succeeded.

## Why native accuracy is so low

The evaluator penalizes every extra row's eight fields. Gold10 expects 34
ordered line items; Gemma returned 428. Its 394 extra rows add 3,152 penalties:
the 342 expected field positions plus 3,152 equals the reported denominator
of 3,494. This is the same scoring rule used for Flash, which returned no
extra rows. Fields on expected rows are compared in order; extra rows can also
shift alignment. The low score must not be described as merely a JSON failure.

The largest gold over-selections were S040 (+146 rows), S032 (+119), S016
(+66) and S044 (+55). More output capacity let Gemma finish long JSON outputs
containing many unwanted rows. Header extraction remained substantially better
than line selection. This does not establish that every field in every native
document is wrong, or that a larger context alone would fix the problem.

Flash's remaining gold errors are concentrated in buyer product identifiers,
line delivery dates and shipping-address representation. All 158 expected
non-null line fields were correct, while only 54/114 expected-null line fields
were correct. Across headers and lines, 193/197 expected-present fields and
85/145 expected-null fields were correct. These measurements motivate a review
of contract adherence; they do not authorize prompt changes.

## Evidence, reuse and accounting

The provider baseline combines saved gold10
`flash-v1-gold-16384-20261022` with the approved remaining20 run
`matrix-provider-v1-baseline-remaining-20261023-72`. Gold10 was not rerun.
The native baseline combines saved S008
`native-s008-49152-16384-20261022` with remaining29 run
`matrix-native-v1-baseline-remaining-20261023-72`.

The evaluator verified matching generation/runtime controls and exactly 30
unique inputs per model. Explicit audited-budget compatibility preserves the
original $4.50 source policies alongside the new $10 policies. Original records
and hashes remain unchanged. Historical 4,096/8,192 diagnostics remain separate.

- [Combined comparison and membership](../results/submission/revised-v1-baseline-review-20261023/verified-summary.json)
- [Full evaluation](../results/submission/revised-v1-baseline-review-20261023/evaluation.json)
- [240-entry membership inventory](../results/submission/revised-v1-baseline-review-20261023/membership.json): 60 baseline observations covered; 180 unexecuted behind the review gate.
- [Native continuation evaluation](../results/submission/matrix-native-v1-baseline-remaining-20261023-72-evaluation/verified-summary.json)
- [Provider continuation evaluation](../results/submission/matrix-provider-v1-baseline-remaining-20261023-72-evaluation/verified-summary.json)
- [Native final runtime and unload evidence](../results/submission/revised-v1-native-runtime-20261023/runtime.json)

The new provider20 cost **$0.87513165**, with every charge settled. Current
cumulative accounted spend is **$2.64845470**, including **$0.50135040** in
unchanged earlier unknown-charge holds; known charges total **$2.14710430**.
The $10 cap leaves **$7.35154530**, including **$1.44871130** protected matrix
funds. No additional paid invocation is authorized.

The native model was unloaded after the batch; `/api/ps` returned no resident
models. Final metadata still reports Ollama 0.40.7 and the same model digest.
Raw continuation exports passed the offline verifier; review/evaluation/runtime
payload hashes were independently checked. The implementation gate remains
684 offline tests plus lint, format, types, gold validation and preflight.
