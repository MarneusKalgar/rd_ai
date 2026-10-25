# Full-corpus v1 baseline review — plan 7.2

This review uses saved matrix outputs, the frozen schema/inputs/gold and their
existing annotation explanations. It does not create new human gold review or
alter labels. The same 10 gold cases were used in provider selection; subsequent
prompt changes informed by these cases are development-set tuning.

**Both full-corpus v1 baselines are complete and reviewed.** The native run
used the installed default thinking=true; the user accepted rebaselining with explicit
thinking disabled before creating v2. That rebaseline has completed, and v2 has
subsequently been drafted; no v2 inference has run. The separate
[stronger-model diagnostic](stronger-model-experiment.md) is complete.
See [execution and evidence](../plans/matrix-experiment.md).

## Provider observations

Gemini 3.5 Flash-Lite / `google-ai-studio`, unchanged v1/baseline, attempted all
30 inputs. There were 25 valid outputs and five retained truncations, with no
corrections/retries. Gold accuracy was 163/406 (40.15%); no gold document matched
exactly. Schema validity and factual/representation correctness are distinct.

| Gold case | Primary matches | Concrete observation |
| --- | ---: | --- |
| S003 | 9/39 | Four displayed product rows returned although only one has an ordered quantity. Three extra rows add 24 wrong field units and shift positional matching. |
| S012 | 9/39 | Three extra rows beyond the one expected ordered line. |
| S021 | 15/31 | All 15 expected fields match, but two extra product rows add 16 wrong field units. |
| S016 | 0/15 | Output truncated despite only one gold ordered line; raw output includes catalog rows rather than completing a small extraction. |
| S032 | 71/111 | All 13 ordered rows selected, but repeated field-role mistakes and address representation reduce matches. |
| S040 | 0/95 | Truncation leaves no usable complete PO; all 95 gold field units receive zero credit. |

Representative mistakes across saved outputs:

- Treating spreadsheet row coordinates as printed PO line numbers.
- Treating a generic article/product code as the buyer's product identifier
  without evidence of that role.
- Copying an order-level delivery date into every line although v1 requires
  an explicit line linkage.
- Including catalog rows whose ordered quantity is blank or zero. More output
  capacity alone would not correct this selection error.
- Joining ship-to components with commas/spaces when gold joins separate
  components with `; `. Exact comparison penalizes this representation even
  where the same address information is present. The frozen schema/v1 prompt
  do not fully specify that delimiter convention; it is a task-specification
  limitation as well as a scoring limitation.
- Misclassifying a supported uncommon unit as UNKNOWN instead of OTHER.

All five failed provider inputs ended with `length`, at 4,079–4,080 reported
output tokens. They were not context-overflow errors. Reported prompt tokens
and the advertised context remain in saved records/setup; a large advertised
window does not establish that every request was independently token-certified.
The partial outputs are retained, not repaired or scored as complete objects.

## Review boundary for the next prompt

Finish and inspect the native baseline before deciding the v2 changes. A future
prompt should express general source/role/selection/representation rules,
without copying expected case-specific answers, coordinates, identifiers or
product values. Preserve all frozen artifacts and v1 bytes, use the same
4,096-token allowance and execution policy, and record the examples used.
Do not relabel a revised scorer as an improvement in model extraction accuracy.

## Native observations and thinking-profile decision

The native run started at **14:50:01 UTC** on 22 October, using desktop Ollama
0.40.7, the pinned Gemma digest, GPU-resident model memory and 32,768 context.
All 30 inputs were attempted once: **19 valid outputs and 11 truncations**, no
correction/retry, zero untouched inputs, no dependency/budget stop. The manifest
is complete; application exit 1 records failed extractions. Sum of input
elapsed times is **2,200.325 seconds** (36 minutes 40 seconds); model loading
was recorded separately at 17.467 seconds.

| Metric | Provider 3.5 Flash-Lite | Native Gemma, default thinking |
| --- | ---: | ---: |
| Attempted corpus inputs | 30/30 | 30/30 |
| Schema-valid corpus outputs | 25/30 (83.33%) | 19/30 (63.33%) |
| Gold primary field matches | 163/406 (40.15%) | 89/406 (21.92%) |
| Gold exact documents | 0/10 | 0/10 |
| Gold header matches | 51/70 | 46/70 |
| Gold ordered-line matches | 112/336 | 43/336 |
| Input p50 / p95 | 2.614 / 9.588 s | 60.325 / 158.297 s |
| Physical calls / corrections | 30 / 0 | 30 / 0 |
| Reported API cost | $0.15360260 | $0, excluding machine/time costs |

Native gold cases S016/S032/S040 truncated and receive zero field matches.
S003/S012/S021 repeat the provider's extra catalog-row errors. S044 returned two
of three gold lines and misclassified the source bottle unit. Generic article
codes were also populated as buyer product IDs without established ownership.
These observations concern the declared contract and strict representation;
they do not measure general model intelligence or establish a held-out score.

**Important execution limitation:** all 30 saved native raw HTTP envelopes
contain nonempty `message.thinking`. Six truncations (S004/S005/S016/S028/S032/
S033) have empty `message.content` with `eval_count: 4096` and nonempty thinking
text. They exhausted the generation budget before any final answer appeared.
Other truncated outputs include partial JSON, including catalog rows. These are
different failure mechanisms; an empty final answer must not be described as
an oversized JSON answer or an input-context overflow.

A metadata-only `/api/show` check at 15:38:58 UTC confirmed the installed model's
`thinking.values: [false, true]` and `thinking.default: true`. The runner did not
supply a `think` override, so the installed default applied. The raw responses
retain the actual thinking field separately from the scored answer; thinking
text is not treated as a PO extraction. See the official
[Ollama thinking controls](https://docs.ollama.com/capabilities/thinking) and
[Gemma thinking templates](https://ai.google.dev/gemma/docs/capabilities/thinking).
No extra generation was used to diagnose this.

The [native run bundle](../../results/submission/matrix-native-v1-baseline-20261022-72/)
and [evaluation bundle](../../results/submission/matrix-native-v1-baseline-20261022-72-evaluation/)
retain all outcomes; a fresh offline container revalidated all 30 records.
Native model residency subsequently expired: `/api/ps` returned no models,
and the app/server processes were idle. The user reported about 12 GB while
the model was resident; no peak process-memory measurement was collected, so
setup's model-memory report must not be presented as peak whole-process memory.

Before continuing the required matched matrix, the user accepted explicitly
disabling thinking and rerunning all 30 native v1/baseline inputs. A changed thinking control is a new execution
profile, not a prompt-only improvement. The original run remains immutable;
the completed provider baseline can be reused because its controls are unchanged.
The new native baseline started only after its control/admission/evidence checks
passed. No additional provider inference was included in this profile change.

## Thinking-disabled baseline — completed and reviewed

The user-approved `matrix-native-v1-baseline-nothink-20261022-72` completed all
30 inputs under the same v1/schema/sampling/context/output/deadline settings,
with explicit thinking=false. All 30 raw envelopes have absent/empty thinking
fields, and saved setup/admission evidence confirms the control. Every input
was attempted once: **21 valid outputs, nine truncations, zero untouched**, no
correction/retry and no budget/dependency stop. Export/evaluation bundles and
fresh-container verification retain all outcomes. This run is the native
baseline for the required matched matrix; the earlier thinking-enabled run
remains a separate diagnostic, not an observation selected by per-case score.

| Metric | Thinking enabled (diagnostic) | Thinking disabled (matrix baseline) |
| --- | ---: | ---: |
| Valid corpus outputs | 19/30 | 21/30 |
| Truncations | 11 | 9 |
| Sum of input durations | 2,200.325 s (36m 40s) | 1,573.836 s (26m 14s) |
| Input p50 / p95 | 60.325 / 158.297 s | 22.037 / 174.031 s |
| Gold primary matches | 89/406 (21.92%) | 70/406 (17.24%) |
| Exact gold documents | 0/10 | 0/10 |
| Native API cost | $0 | $0 |

Disabling thinking reduced observed processing time by about **28.5%**, and
median latency by about **63.5%**, but did not improve every latency tail or
quality metric. Both are single sequential runs; caching, host load and normal
model variability were not independently controlled, so this is not an isolated
hardware benchmark or a repeated causal-effect estimate.

The gold score dropped by 19 matches: S044 changed from a valid 19/31 output to
a truncation; S002 lost two matches and S023 gained two. More schema-valid
outputs over the entire 30-input corpus therefore did not imply better accuracy
on the labeled subset. Catalog-row selection, unsupported field inference and
exact representation remain problems with v1. The nine new truncations have
answer text rather than empty thinking-only responses. More output tokens
alone would not fix returning unselected catalog rows.

Provider baseline raw usage reports zero reasoning tokens in all 30 responses.
Its controls are unchanged and its completed run remains reusable. Native
thinking=false stays fixed for all required v1/v2/sampling variants, as accepted
before the rerun. No per-case mixing of thinking profiles or prompt/limit changes
is used to improve the baseline score.

Both selected baselines have now completed and been reviewed. The next prompt
may clarify general ordered-row eligibility, field roles, source coordinates,
line-linked dates, address joining and unit/number representation. Record all
10 labeled cases as tuning examples; qualitative inspection of unlabeled outputs
cannot create factual accuracy labels. Preserve v1 and frozen data/schema/gold.
