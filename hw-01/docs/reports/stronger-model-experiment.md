# Stronger-model diagnostic before v2 inference

## Question and comparison

Does Gemini 3.5 Flash improve extraction over the selected Gemini 3.5 Flash-Lite
under unchanged v1/baseline? This is an optional diagnostic on all 10 approved
gold documents, separate from the required 240-observation matrix. It does not
replace the accepted provider or authorize remaining matrix invocations.

The user requested this comparison before running v2. The v2 draft already
exists, but no v2 inference has run. Keep that draft unchanged during this
diagnostic and disclose any later changes informed by its outputs.

Use `config/stronger-model.yaml`: `google/gemini-3.5-flash` through
`google-ai-studio`, v1, temperature 0, top_p 1 and 4,096 output tokens. Preserve
the frozen inputs, schema, gold, scorer and bounded retry/correction policy.
Reuse the same 10 documents from the saved Lite full-corpus baseline; do not
rerun Lite or select only cases that the stronger model completes.

Provider reasoning is not explicitly controlled by the current adapter. Flash
advertises medium thinking by default; the Lite baseline reported zero
reasoning tokens. This compares the two deployed model profiles, not model
weights with identical reasoning allocation. Retain raw reasoning usage and
report any resulting output-budget exhaustion separately. Do not silently
increase the token allowance to rescue this run.

Report full-gold accuracy, exact-document matches, validity, truncation, extra
rows, latency, usage and actual cost. Include per-case differences and a
secondary comparison on cases both models complete, clearly labeled as that
subset. The full-gold result remains primary. These are development examples
already used in screening and prompt review, not a held-out generalization test.

## Metadata and budget

Public endpoint metadata checked at **2026-10-22 18:13:25 UTC** confirmed the
required parameters, healthy route, 1,048,576 context tokens and 65,536 maximum
output tokens. The experiment requests only 4,096 output tokens. Rates were
$1.50/million input and $9/million output, including the catalog's reasoning
rate where supplied. No fixed request fee, compression, fallback or paid tools.

For scale only, the saved Lite gold subset used 47,883 input and 12,211 output
tokens. Identical usage at Flash's rates would cost $0.18172350. This is not a
quote or spending cap: Flash may use different token counts, reasoning and
corrections. Its default thinking behavior is documented on the
[OpenRouter model page](https://openrouter.ai/google/gemini-3.5-flash).

Evidence is retained in the results volume under
`results/setup/stronger-model-20261022/`; proposed coverage is
`results/provider-stronger-model-coverage-20261022.json`.
Preparation performed no inference. Coverage-file creation is not approval.

The full-context reservation is **$1.60972800 per physical call**, settled to
reported cost. Unknown charges retain that reservation. The existing ledger
accounts for $0.75076860, including $0.50135040 in earlier unknown-charge holds;
$3.74923140 remains under the unchanged $4.50 cumulative cap.

Only $0.40283400 is available outside the protected matrix reserve. Therefore
the screening stage cannot admit this diagnostic. Proposed execution uses the
matrix accounting stage with exactly the 10 explicit gold IDs. This requires
explicit human approval to use matrix funds for the optional diagnostic and
provider-enforced context admission. Its observations remain excluded from the
required matrix membership. No ledger reset or release of prior holds is allowed.

There are 10 primary requests and at most 40 physical calls under existing
bounds. The unrestricted reservation total is not an expected bill; cumulative
budget and dependency guards may stop execution earlier. After an incomplete
stop, report the saved outcomes before requesting any further paid invocation.

## Verification and proposed invocation

The user explicitly approved this invocation, provider-enforced context and
use of matrix funds on 22 October 2026. The approval covers this diagnostic
only. The command below was then started; no v2/native work is included.

The complete offline gate passed **672 tests**, Ruff lint/format, strict mypy,
gold validation and corpus preflight. The offline plan independently matches
the frozen gold manifest's exact 10 IDs and preserves the original v1 hash.
No generation was performed during these checks.

From the repository root, only after explicit paid-run approval:

```sh
make hw01-run MODE=provider ARGS='--config config/stronger-model.yaml --stage matrix --model provider-flash --prompt v1 --sampling baseline --input B02-S002-PO01 --input B02-S003-PO01 --input B02-S011-PO01 --input B02-S012-PO01 --input B02-S016-PO01 --input B02-S021-PO01 --input B02-S023-PO01 --input B02-S032-PO01 --input B02-S040-PO01 --input B02-S044-PO01 --coverage results/provider-stronger-model-coverage-20261022.json --allow-server-context --allow-provider --run-id stronger-flash-v1-gold-20261022'
```

## Completed result

Run `stronger-flash-v1-gold-20261022` attempted every selected document exactly
once, with no corrections/retries, untouched inputs, dependency stop or budget
stop. Eight outputs validated and two truncated. The manifest is complete;
application exit 1 records failed extractions, not an interrupted comparison.

Both columns below use exactly the same 10 gold documents. Lite operational
metrics are recomputed for that subset, not copied from its 30-input population.

| Metric | Gemini 3.5 Flash-Lite | Gemini 3.5 Flash |
| --- | ---: | ---: |
| Valid outputs | 8/10 | 8/10 |
| Primary field accuracy | 163/406 (40.15%) | 120/358 (33.52%) |
| Exact documents | 0/10 | 0/10 |
| Extra rows in valid outputs | 8 | 2 |
| Gold header matches | 51/70 | 53/70 |
| Input latency p50 / p95 | 1.564 / 9.628 s | 9.946 / 17.807 s |
| Actual API charges | $0.04489240 | $0.29324205 |

Denominators differ because the unchanged scorer adds eight wrong field units
per extra line. The fixed gold contains 342 expected field units; Lite adds 64
extra-row penalties and Flash adds 16. Invalid/truncated outputs earn no matches.
There is no scorer change or partial-JSON recovery.

### Paired case observations

| Gold case | Lite matches | Flash matches | Observation |
| --- | ---: | ---: | --- |
| S002 | 11/15 | 14/15 | More expected fields matched. |
| S003 | 9/39 | 13/15 | Removed three unwanted catalog rows. |
| S011 | 13/15 | 13/15 | Same match count. |
| S012 | 9/39 | 12/15 | Removed three unwanted catalog rows. |
| S016 | 0/15 | 11/15 | Flash completed where Lite truncated. |
| S021 | 15/31 | 15/31 | Both retained two unwanted rows. |
| S023 | 13/15 | 14/15 | One additional expected field matched. |
| S032 | 71/111 | 0/111 | Flash truncated where Lite completed. |
| S040 | 0/95 | 0/95 | Both truncated. |
| S044 | 22/31 | 28/31 | More expected fields matched. |

The seven documents both models completed score **92/185 (49.73%)** for Lite
and **109/137 (79.56%)** for Flash. This is a secondary, outcome-selected subset;
it must not replace the primary full-gold result or be presented as a held-out
accuracy estimate. It does provide evidence that model/profile choice affects
row selection and field correctness on these examples.

### Reasoning and interpretation

Lite reported zero reasoning tokens on every gold response. Flash reported
nonzero reasoning on every response. Both Flash failures, S032 and S040,
reported **3,933 reasoning tokens out of 4,081 completion tokens**, with finish
reason `length`. Only 148 reported completion tokens remained outside reasoning.
This is output-budget exhaustion, not evidence of an input-context overflow.

Flash therefore improved several completed extractions but did not improve the
overall result under the same 4,096-token cap. It cost about **6.53 times** as
much and had about **6.36 times** the median latency on this subset. This is one
run per model with different default reasoning profiles, not an isolated causal
measurement of model weights or a general claim that expensive models are worse.

Keep Flash-Lite as the selected matrix provider. A separately approved Flash
reasoning-control or larger-output-budget experiment could distinguish the
reasoning budget issue, but neither is authorized by the completed invocation.
No v2 inference has run. Retain the v2 draft unchanged while interpreting this
diagnostic; any subsequent tuning informed by these outputs must be disclosed.

### Evidence and remaining budget

The saved run and separate evaluation/comparison bundles are under
`results/submission/stronger-flash-v1-gold-20261022/` and
`results/submission/stronger-flash-v1-gold-20261022-evaluation/`.
Fresh offline reload validates all records, input/schema hashes and ledger bounds.
Raw responses retain reasoning usage and failures. Operator process/plan logs,
configuration and summaries are archived in the results volume under
`results/matrix-runs/stronger-flash-v1-gold-20261022/`.

All $0.29324205 of this run's charges were reported and settled; it added no
unknown-charge holds. Cumulative accounted spend is **$1.04401065**, including
the unchanged **$0.50135040** of earlier holds. **$3.45598935** remains under the
$4.50 cap, of which **$3.05315535** remains protected for matrix work. Reservation
totals across sequential calls are not actual charges or simultaneous holds.

## Follow-up: both Flash profiles at 8,192 tokens

The user requested an 8,192-token run for both Flash-Lite and Flash before v2.
Prepare `config/flash-output-8192.yaml` with the same v1, temperature 0 and
top_p 1. The explicit `baseline-8192` sampling ID distinguishes this diagnostic
from the required 4,096-token matrix. Select the same 10 gold IDs for each
model: 20 primary requests, at most 80 physical calls with existing bounds.
Provider reasoning defaults are unchanged; preserve their actual reported usage.

Fresh metadata at **2026-10-22 18:33:09 UTC** verified both `google-ai-studio`
routes, required parameters, 1,048,576 context and 65,536 maximum output tokens.
Rates remain $0.30/$2.50 per million input/output tokens for Flash-Lite and
$1.50/$9 for Flash. Full-context per-call reservations become **$0.33505280**
and **$1.64659200**, respectively. Settle known charges and retain unknowns.

Coverage is `results/provider-flash-output-8192-coverage-20261022.json`;
metadata is archived in `results/setup/flash-output-8192-20261022/`.
Preparation performs no inference. Use existing matrix-stage context admission
and accounting only with explicit paid-invocation approval; preserve all prior
holds and the $4.50 cumulative cap. The proposed invocation can use only the
remaining $3.45598935, including protected matrix funds. No budget is reset.
The prior 672-test gate covers the unchanged implementation; the new configuration
and exact job selection are additionally checked by the offline planning command.

The user explicitly approved the exact 20-request paid invocation and use of
matrix funds on 22 October. The invocation has started; no v2 inference has
run. Retain all four model/output-limit observations per gold case for the
comparison, including failures; this is not an expansion of required matrix membership.

### Completed 8,192-token result

Run `flash-pair-v1-gold-8192-20261022` completed all 20 selected observations with
one physical call each, no corrections/retries, no untouched inputs and no
dependency/budget stops. Both models produced nine valid outputs and one
truncation, S040. All charges were reported and settled. The complete manifest
retains both failures; application exit 1 is expected for failed extractions.

| Gold-only metric | Lite 4,096 | Lite 8,192 | Flash 4,096 | Flash 8,192 |
| --- | ---: | ---: | ---: | ---: |
| Field accuracy | 163/406 (40.15%) | 170/934 (18.20%) | 120/358 (33.52%) | 205/342 (59.94%) |
| Valid outputs | 8/10 | 9/10 | 8/10 | 9/10 |
| Exact documents | 0/10 | 0/10 | 0/10 | 1/10 |
| Extra rows in valid outputs | 8 | 74 | 2 | 0 |
| Median input latency | 1.564 s | 1.641 s | 9.946 s | 9.421 s |
| Actual API charges | $0.04489240 | $0.06088240 | $0.29324205 | $0.33856650 |

The denominators change because extra rows incur eight wrong field units each:
342 expected units plus 592 extra-row penalties give Lite's 934. Its lower
percentage does not mean fewer matching expected fields: matches increased
from 163 to 170, but its newly completed S016 includes **66 unwanted rows**
(67 predicted versus one expected). S016 scores 8/543. This exposes an existing
row-selection problem once enough output space is available. Merely making
the JSON complete does not make the extraction correct.

Flash completed S032 at 5,452 reported completion tokens, including 4,396
reasoning tokens, and scored 84/111 there. This accounts for 84 of its 85 new
matches; the other net match came from S016. S021 now has the correct single
line and scores 15/15, producing the first exact document. Flash's S040 still
truncated at 8,177 completion tokens, including **7,412 reasoning tokens**.
Lite also truncated S040 at 8,176 tokens, reporting no reasoning usage. Preserve
these distinct failure mechanisms; neither response establishes input overflow.

At 8,192, Flash costs about **5.56 times** as much as Lite and has about
**5.74 times** its median latency, with substantially better measured extraction
on this development set. Both model/profile choice and output allowance matter
here. Each configuration has one observation per document, and the non-failing
outputs also vary between calls despite temperature 0. This is evidence about
these deployed profiles, not a repeated causal estimate or held-out benchmark.

The stronger profile is now a credible quality candidate for a separately
agreed matrix extension or revised provider choice. The required matrix's
selected Flash-Lite/4,096 profile remains unchanged pending an explicit scope
decision. Do not mix these gold-only observations into the original 30-input
matrix or silently increase its output allowance. No v2 inference ran.

The new run bundle and separate evaluation/comparison bundle are in
`results/submission/flash-pair-v1-gold-8192-20261022/` and
`results/submission/flash-pair-v1-gold-8192-20261022-evaluation/`.
Fresh offline verification checked all 20 records, exact gold membership,
original v1/schema hashes, sampling controls and preserved prior holds.
The volume archive under `results/matrix-runs/flash-pair-v1-gold-8192-20261022/`
includes the four-profile paired comparison, configuration, plan/process logs
and checksums.

The follow-up cost **$0.39944890**. Cumulative accounted spend is now
**$1.44345955**, including the unchanged **$0.50135040** in earlier holds.
Remaining cumulative allowance is **$3.05654045**, including **$2.65370645**
protected for matrix work. No additional inference is approved.

## Follow-up: stronger Flash at 16,384 tokens on all gold documents

The user requested the full gold10, not just S040. Prepared
`config/flash-output-16384.yaml` selects only Gemini 3.5 Flash through
`google-ai-studio`, unchanged v1, temperature 0, top_p 1 and default reasoning,
with explicit `baseline-16384`. Preserve every earlier run. This diagnostic is
separate from the required matrix and includes no Lite, native or v2 inference.

Metadata checked at **2026-10-22 18:45:17 UTC** confirmed the route remains
healthy with required parameters, 1,048,576 context and 65,536 maximum output
tokens. Rates remain $1.50/million input and $9/million output; the full-context
reservation is **$1.72032000 per physical call**. Coverage is
`results/provider-flash-output-16384-coverage-20261022.json`; metadata is under
`results/setup/flash-output-16384-20261022/`. Preparation performs no inference.

The proposed invocation selects all 10 exact frozen gold IDs, 10 primary
requests and at most 40 physical calls under existing retry/correction bounds.
Its configuration and membership are checked offline. Implementation remains
the version that passed 672 tests; no runtime code changes are needed.

The user explicitly approved the concrete invocation, provider-enforced context
and continued use of matrix funds on 22 October; that invocation has started.
Retain the $4.50 cumulative cap, current
$1.44345955 accounted spend and $0.50135040 earlier unknown-charge holds.
At most the existing $3.05654045 remaining allowance is available, including
$2.65370645 protected matrix funds. Settle known charges, retain unknowns and
stop on budget/dependency guards. A single unknown Flash reservation could
prevent another Flash call under this remaining allowance. Do not release it
or replay the invocation automatically to complete the comparison.

### Completed 16,384-token result

Run `flash-v1-gold-16384-20261022` completed **10/10 valid outputs**, one call
each, no corrections/retries, no untouched inputs, no budget/dependency stop
and no truncation. The application exited 0. All outputs, raw envelopes,
evaluation and five-profile comparison were exported and independently checked.

| Stronger Flash metric | 4,096 allowance | 8,192 allowance | 16,384 allowance |
| --- | ---: | ---: | ---: |
| Gold field accuracy | 120/358 (33.52%) | 205/342 (59.94%) | 278/342 (81.29%) |
| Valid outputs | 8/10 | 9/10 | 10/10 |
| Exact documents | 0/10 | 1/10 | 1/10 |
| Extra / missing rows | 2 / 24 | 0 / 11 | 0 / 0 |
| Input latency p50 / p95 | 9.946 / 17.807 s | 9.421 / 35.017 s | 11.314 / 26.503 s |
| Actual API charges | $0.29324205 | $0.33856650 | $0.32986350 |

The full accuracy gain over 8,192 is S040's **73/95 matches**, previously zero
because it truncated. The other nine documents retain the same match counts;
the secondary common-valid score remains 205/247 (83.00%). There are no extra
or missing rows in any of the 10 final valid outputs. S021 remains the only
exact document.

S040 reported **6,260 completion tokens**, including **5,364 reasoning tokens**,
and finish reason `stop`. Its successful output is smaller than the previous
8,192 allowance. Therefore the experiment does not establish that S040 always
requires more than 8,192 tokens or that the higher cap alone caused success.
The saved 8,192 run used 7,412 reasoning tokens and truncated; model reasoning
and outputs vary even with temperature 0. These are single runs, not a repeated
estimate of a token threshold. Increasing a maximum allowance also does not
force the model to consume it: all responses in the new run used at most 6,260
reported completion tokens, and total actual cost was slightly lower than the
8,192 run.

The remaining **64 field mismatches** are 33 buyer product identifiers, 27
line delivery dates and four ship-to representations. Present-value matches
are 193/197; expected-null matches are 85/145. The outstanding quality problem
therefore includes unsupported field-role/date inference and exact address
representation, rather than incomplete JSON or missing rows. Keep the frozen
gold/scorer unchanged; the existing v2 draft's general rules can be evaluated
later without claiming that prompt tuning is held-out testing.

**Stop increasing the allowance for this diagnostic.** It has now completed
every gold document with no truncations. Further quality work should evaluate
the contract/prompt rules and preserve these successful and failed profiles.
This observation supports considering Flash as a quality candidate, but the
required matrix profile is unchanged until a scope decision. No v2 inference
or additional paid invocation is authorized.

The run and separate comparison/evaluation bundles are under
`results/submission/flash-v1-gold-16384-20261022/` and
`results/submission/flash-v1-gold-16384-20261022-evaluation/`.
The results volume archive at
`results/matrix-runs/flash-v1-gold-16384-20261022/` retains configuration,
plan/process logs, evaluation, paired comparisons and checksums. Verification
checks exact gold membership, v1/schema hashes, controls and prior ledger holds.

All **$0.32986350** of this run's charges were reported and settled, with no
new unknown-charge holds. Cumulative accounted spend is **$1.77332305**,
including the unchanged **$0.50135040** earlier holds. **$2.72667695** remains
under the $4.50 cap, including **$2.32384295** protected matrix funds.
