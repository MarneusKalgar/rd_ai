# Native Gemma v2 gold10

**Evidence availability — 25 October 2026:** the [compact review snapshot](../../results/submission/v2-baseline-review-20261025/summary.json) and [availability index](../../results/submission/v2-baseline-review-20261025/evidence-index.json) are included in this checkpoint. New v2 raw/preparation/detailed evaluation bundles referenced below are retained locally and intentionally unversioned pending archival. A fresh checkout cannot reproduce their saved-run evaluation yet. See the [checkpoint notes](../../results/submission/v2-baseline-review-20261025/README.md).

## Scope and frozen profile

On 24 October 2026 the user requested native Gemma on the approved gold10 with
v2. Run ID: `matrix-native-v2-gold-20261024-72`. All ten outputs are saved,
verified and scored. Native remaining20 require user
review and approval. No provider or exploratory invocation is authorized.

The instruction-only revision preserves the 22 October draft's history and
adds no worked examples, skill resources or semantic correction workflow.
It binds the order quantity to its logical product entry and limits catalog
exclusion to source order-entry evidence. The same frozen instructions are
available for a later separately approved stronger Flash phase.

- Frozen v2 SHA-256: `6a03379937695a2e5b127d292fc6ddb2301c9048b730ca3f9982d6c6443d155b`.
- Original unexecuted draft SHA-256: `c2c6c61dcdd3fe9c93fcaf9b40d6f811a30fb9351e6918fcaa899459021e5ba0`.
- Config: `config/matrix.yaml`; `local`, `v2`, `baseline-16384`, matrix stage.
- Native Ollama 0.40.7; `gemma4:e4b-it-qat`, matching the revised v1 digest.
- Context 49,152; output allowance 16,384; thinking=false; temperature 0; top_p 1.
- Existing deadlines, bounded retries/correction, schema and scorer unchanged.

The full offline gate passed **732 tests**, lint/format, strict types, gold
validation and preflight. All ten complete initial requests passed render-only
admission with the matching native tokenizer/runtime. Maximum conservative
prompt bound: **15,811** plus **16,384** output allowance, within 49,152.
This bound is not measured prompt usage; each actual correction still requires
admission. Preparation used no generation probes and left the budget ledger
unchanged.

The preparation bundle (local-only: `../../results/submission/native-v2-gold-20261024-preparation/preparation.json`)
records exact membership, command, prompt/configuration hashes, model/tokenizer
identity, admission evidence and baseline source identity. It also retains the
old draft and frozen prompt/configuration bytes with checksums.

## Verified results

The comparison uses exactly the same ten gold inputs and matched generation
controls. All ten v2 outputs passed schema validation on the first call, with
no correction or retry. No provider inference ran; API spend was zero and the
cumulative budget ledger is byte-for-byte unchanged. Gemma was unloaded after
completion and native residency was confirmed empty.

| Metric | Revised native v1 gold10 | Native v2 gold10 |
| --- | ---: | ---: |
| Schema-valid outputs | 10/10 | 10/10 |
| Overall gold field accuracy | 164/3,494 (4.69%) | 198/2,766 (7.16%) |
| Header accuracy | 61/70 (87.14%) | 68/70 (97.14%) |
| Line-field accuracy | 103/3,424 (3.01%) | 130/2,696 (4.82%) |
| Extra rows by scored array counts | 394 | 303 |
| Missing rows by scored array counts | 0 | 0 |
| Exact documents | 0 | 1 (S021) |
| Physical inference calls | 10 | 10 |
| Sum of input processing durations | 18m 40.761s | 14m 00.110s |

The v2 denominator is 342 expected field positions plus eight penalties per
extra row: `342 + 303 × 8 = 2,766`. Header improvements and fewer extra rows
improve the score, but substantial catalog over-selection remains. Zero missing
rows by count does not prove that every ordered product was correctly extracted.
Timing excludes setup/model loading; the v2 load took a separate 7.154 seconds.
This single run does not establish a general latency improvement.

S012 and S044 now have the expected row counts, and S021 is exact. S032 falls
from 132 output rows to 101 against 13 gold rows. S016 remains 67 against one,
and S040 remains 157 against 11. The post-hoc source-row diagnostic independently
flags 66, 94 and 146 contradicted rows respectively in those three catalog
documents. Diagnostic source-evidence categories and scorer array-count
differences measure different properties. No diagnostic filtered output,
altered scores or triggered model correction.

Evidence:

- Raw run (local-only: `../../results/submission/matrix-native-v2-gold-20261024-72/`).
- Verified summary (local-only: `../../results/submission/matrix-native-v2-gold-20261024-72-evaluation/verified-summary.json`).
- Matched comparison (local-only: `../../results/submission/matrix-native-v2-gold-20261024-72-evaluation/comparison.json`).
- Evaluation (local-only: `../../results/submission/matrix-native-v2-gold-20261024-72-evaluation/evaluation.json`).
- Required matrix membership (local-only: `../../results/submission/matrix-native-v2-gold-20261024-72-evaluation/membership.json`): 70/240 covered, 170 unexecuted.
- Compact row diagnostic (local-only: `../../results/submission/matrix-native-v2-gold-20261024-72-evaluation/diagnostic-summary.json`); the full report stays ignored under `results/diagnostics/native-v2-gold-20261024/`.

## Review gate

The user subsequently authorized native remaining20; that invocation is recorded
in [v2 continuation results](v2-continuation-results.md). The gate below describes
the stop after this original gold10 phase and remains applicable to any changed
prompt/profile; it is not an instruction to interrupt the approved continuation.

Compare gold10 quality and operations with the same ten revised v1 native
observations. Gold10 has already informed development; it is not held out.
Retain failures and distinguish schema validity from factual extraction quality.
Run any deterministic source-row diagnostic only after extraction, without
filtering results or changing scores.

Do not start native remaining20 until user approval. A subsequent prompt/profile
change needs an explicit new revision and a fresh gold10 before aggregation;
do not combine gold results from this revision with changed remaining20 runs.
