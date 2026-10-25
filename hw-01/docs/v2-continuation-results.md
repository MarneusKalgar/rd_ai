# Frozen v2 continuation — 24 October 2026

**Evidence availability — 25 October 2026:** the [compact review snapshot](../results/submission/v2-baseline-review-20261025/summary.json) and [availability index](../results/submission/v2-baseline-review-20261025/evidence-index.json) are included in this checkpoint. New v2 raw/preparation/detailed evaluation bundles referenced below are retained locally and intentionally unversioned pending archival. A fresh checkout cannot reproduce their saved-run evaluation yet. See the [checkpoint notes](../results/submission/v2-baseline-review-20261025/README.md).

## Requested scope and preparation

The user requested native Gemma on the disjoint remaining20 and stronger Gemini
Flash on gold10. Reuse the [verified native v2 gold10](native-v2-gold.md), without
rerunning it. This completes native all30 only when the continuation has checked
terminal records for every input; provider gold10 is not provider all30.

Frozen v2 SHA-256:
`6a03379937695a2e5b127d292fc6ddb2301c9048b730ca3f9982d6c6443d155b`.
Both phases use `config/matrix.yaml`, matrix stage, baseline-16384 (temperature
0, top_p 1) and the unchanged schema, preprocessing, correction/retry policy
and scorer. No skill/examples, Qwen or exploratory invocation is included.

- Native run: `matrix-native-v2-remaining-20261024-72`; Gemma QAT, native Ollama
  0.40.7, matching saved model/tokenizer identity, context 49,152, thinking=false.
  All 20 initial requests passed render-only admission; maximum prompt bound
  22,863 plus 16,384 output allowance. Actual correction requests need their
  own admission. Preparation (local-only: `../results/submission/native-v2-remaining-20261024-preparation/preparation.json`).
- Provider run: `matrix-provider-v2-gold-20261024-72`; Gemini 3.5 Flash through
  `google-ai-studio`, default reasoning retained, 16,384 output allowance.
  Provider-enforced context policy already approved for matrix execution; full
  inputs/schema, no prompt compression or route fallback. The refreshed route
  advertises 1,048,576 context and 65,536 maximum completion tokens. Reserve
  $1.720320 per physical call; settle reported costs, retain unknown charges.
  Ten primaries, at most 40 physical calls including bounded retries/correction.
  Preparation (local-only: `../results/submission/provider-v2-gold-20261024-preparation/preparation.json`).

Preparation performed no inference and did not change the ledger: $2.64845470
accounted, including $0.50135040 prior unknown holds; $7.35154530 remaining under
the $10 cumulative cap, including $1.44871130 protected matrix funds. The user separately approved the concrete provider gold10 invocation within this
remaining allowance; the approval does not extend to a later paid invocation.

## Subsequent provider continuation approval

The user additionally requested and separately approved the disjoint provider
remaining20 invocation: `matrix-provider-v2-remaining-20261024-72`. It reuses
verified v2 gold10 and the same route/profile/coverage, with at most 80 physical
calls for 20 primaries. Its opening accounted balance is $2.86977220 and
remaining allowance $7.13022780 under the unchanged $10 cap. Each call reserves
$1.720320; earlier unknown holds remain preserved. This continuation subsequently
completed and supplies no approval for any later invocation.
Preparation (local-only: `../results/submission/provider-v2-remaining-20261024-preparation/preparation.json`).

## Execution status

The refreshed offline gate passed 732 tests plus lint/types/gold/preflight.
Both all30 v2 baselines are complete and verified; see terminal results below.
No automatic later invocation is authorized.

## Provider gold10 verified

Gemini v2 saved 10/10 schema-valid outputs, one call each, no retry/correction.
Gold score is **342/342 (100%)**, headers 70/70, line fields 272/272,
**10/10 exact documents**, zero extra/missing rows. An independent direct JSON
object comparison also matched every gold object; this is not only a normalized
scoring result. Gold10 informed development, so this is not held-out evidence.

The matched v1 Flash gold10 scored 278/342 (81.29%), with one exact document.
V2 processing durations sum to 78.466 seconds; p50/p95 are 6.117/14.323 seconds.
Known cost is **$0.22131750**, versus v1 gold10 $0.32986350. All ten charges
settled; no new unknown holds. Cumulative accounted spend is **$2.86977220**,
remaining allowance **$7.13022780**, protected matrix funds **$1.22739380**.
Prior unknown holds remain $0.50135040. No later paid invocation is approved.

The post-hoc source-row diagnostic reports 25 supported, zero contradicted and
nine unknown output rows. Unknown means the check has no conclusive evidence;
it is not an extraction error label. These categories are distinct from field
accuracy and did not change output, correction behavior or scoring.

- Raw provider run (local-only: `../results/submission/matrix-provider-v2-gold-20261024-72/`).
- Provider summary (local-only: `../results/submission/matrix-provider-v2-gold-20261024-72-evaluation/verified-summary.json`).
- Matched v1/v2 comparison (local-only: `../results/submission/matrix-provider-v2-gold-20261024-72-evaluation/comparison.json`).
- Compact source-row diagnostic (local-only: `../results/submission/matrix-provider-v2-gold-20261024-72-evaluation/diagnostic-summary.json`).

The later provider remaining20 continuation is complete, as recorded below.
Native remaining20 subsequently completed, as recorded below.

## Provider all30 verified

The approved continuation saved **20/20 schema-valid outputs**, one call each,
no retries/corrections or dependency/budget stops. The checked union with saved
gold10 contains exactly 30 distinct frozen inputs under the same v2 profile.
Gold quality remains 342/342 and 10/10 exact documents; the other20 provide
operational and qualitative evidence, not new factual accuracy labels.

Across all30: **30/30 first/final valid**, 30 physical inference calls, no
truncations, p50/p95 input latency **8.379/22.966 seconds**, summed input
processing **309.870 seconds (5m 09.870s)**, excluding setup. Gold10 and
remaining20 took 78.466 and 231.405 seconds respectively. Native inference
was running concurrently; retain that condition when interpreting timing.

Continuation cost is **$0.65932440**; combined provider v2 cost is
**$0.88064190**, all charges settled. Cumulative accounted spend is
**$3.52909660**, remaining allowance **$6.47090340**, protected matrix funds
**$0.56806940**. Earlier unknown holds remain **$0.50135040**.

The full source-row diagnostic reports 25 supported, zero contradicted and
255 unknown output rows. Most forms are outside its conclusive evidence
coverage; this is not proof that all unlabeled outputs are correct.

- Raw continuation (local-only: `../results/submission/matrix-provider-v2-remaining-20261024-72/`).
- All30 summary (local-only: `../results/submission/matrix-provider-v2-remaining-20261024-72-evaluation/verified-summary.json`).
- All30 v1/v2 comparison (local-only: `../results/submission/matrix-provider-v2-remaining-20261024-72-evaluation/comparison.json`).
- Compact all30 diagnostic (local-only: `../results/submission/matrix-provider-v2-remaining-20261024-72-evaluation/diagnostic-summary.json`).

Provider completion brought required coverage to 100/240; the final native
continuation increases this to 120/240 below. No further paid invocation is approved.

## Native all30 verified

The continuation saved all **20/20 terminal records**: **19/20 schema-valid**,
1 failed. Retained failures: B02-S004-PO01 (truncated; 16384 output tokens).
Every continuation input used one physical inference call; no retries or corrections
were introduced. The checked union with saved v2 gold10 contains exactly all30
inputs under the same prompt, native runtime/model/tokenizer, context and thinking
controls. Failed attempted inputs remain in the required membership inventory.

Across all30: **29/30 schema-valid**, 30 inference calls,
gold **198/2,766 (7.16%)**, one exact gold document and 303 extra gold rows.
Remaining20 did not add gold labels or change the reused gold10 score.
Compared with v1, gold accuracy rose from 4.69%, but catalog over-selection remains
substantial. V1 all30 also had 29/30 schema-valid outputs, with S033 truncated.
V2 makes S033 schema-valid but introduces S004's truncation. Neither document
has a gold label; distinguish these operational outcomes from factual quality.

The detection-only all30 diagnostic reports 19 supported, 306 contradicted and
514 unknown returned rows. Its conclusive catalog checks cover only specific
source structures; unknown is not an error label, and failed S004 has no parsed
rows to classify. These flags did not alter extraction, correction or scoring.

Summed input processing durations: continuation **29m 12s**;
combined native v2 all30 **43m 12s**, versus native v1
**57m 56s**. V2 p50/p95 input latency is
**18.807/368.810 seconds**.
These sums exclude setup/loading. The native v2 gold10 and remaining20 were separate
invocations; provider work ran concurrently with the continuation. Keep these
conditions visible when comparing timings.

Native API spend is zero. Gemma was unloaded after completion; native residency
was verified empty. No further model invocation is authorized.

- Raw native continuation (local-only: `../results/submission/matrix-native-v2-remaining-20261024-72/`).
- Combined native summary (local-only: `../results/submission/matrix-native-v2-remaining-20261024-72-evaluation/verified-summary.json`).
- All30 native v1/v2 comparison (local-only: `../results/submission/matrix-native-v2-remaining-20261024-72-evaluation/comparison.json`).
- Compact native diagnostic (local-only: `../results/submission/matrix-native-v2-remaining-20261024-72-evaluation/diagnostic-summary.json`).
- Native unload evidence (local-only: `../results/submission/matrix-native-v2-remaining-20261024-72-evaluation/native-runtime.json`).
- Final required membership (local-only: `../results/submission/matrix-native-v2-remaining-20261024-72-evaluation/membership.json`).

## Final scope and budget

The v1 and v2 baseline variants are now attempted over all30 on both selected
models: **120/240 required observations covered**. The four exploratory
prompt/model variants (**120 primaries**) remain unexecuted and require further
direction and paid-invocation approval where applicable. Qwen remains a separate
planned gold10 diagnostic; no Qwen weights or inference were requested here.

New provider v2 spending across both approved invocations is **$0.88064190**.
The final cumulative ledger accounts **$3.52909660**, including unchanged prior
unknown holds **$0.50135040**, leaving **$6.47090340** under the unchanged $10 cap.
All new charges settled. No provider reservation was created by native work.
The refreshed offline gate passed **732 tests**, lint/format, strict types,
frozen gold validation and preflight. Checked exports retain raw responses,
failures, identities and hashes; verbose diagnostics remain ignored.
