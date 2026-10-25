# Provider screening observations — 22 October 2026

**Evidence retrieval:** Bulk evidence is in the [submission-history archive](../../archive-index/31349837ab5acff7f512d02ef2ee56a93a7a2da63d01dd8a12ea85acd734288a.json). Follow the [restore instructions](../guides/archiving-results.md#historical-submission-evidence) before opening restored-file links. Original run IDs and export paths retain their historical meaning.

**7.1 is complete with the Gemini pair.** On 22 October 2026, the user accepted
finalizing selection from the two completed candidates and confirmed that
Mistral was optional. **Gemini 3.5 Flash-Lite / `google-ai-studio` is selected.**
Mistral remains unavailable and unranked after two upstream rate-limit stops.
Original run manifests remain incomplete because they include untouched Mistral
jobs; the accepted selection scope does not rewrite those historical outcomes.
All records, evaluations and unknown-charge holds are retained.

## Executed scope

Run `provider-screening-20261022-71` started at `2026-10-22T12:36:06Z`
(15:36:06 Europe/Kiev). The user approved the concrete command in
[screening preparation](../plans/provider-screening.md), limited to the remaining
$0.98481750 non-matrix allowance with $3.50 protected. All candidates used the
same 10 approved gold inputs, unchanged v1/baseline, full schema/source,
temperature 0, top_p 1 and a 4,096-token output allowance. The current main
configuration and prompt/data artifacts were preserved.

The manifest is **incomplete**: succeeded 15, failed 8, not_attempted 7,
`comparison_complete: false`. There was no budget stop. The application exited
3, wrapped by Make as error 2. There were **26 physical requests**: 10 per Gemini
candidate and six Mistral requests. No correction attempt was made.

## Completed Gemini comparison

The [shared evaluator](../reference/evaluation.md) scored both completed candidates over all
10 gold cases, with identical strict positional/representation rules. These
cases were used for selection and are development data.

| Metric | Gemini 3.1 Flash-Lite | Gemini 3.5 Flash-Lite |
| --- | ---: | ---: |
| Inputs attempted | 10/10 | 10/10 |
| First/final schema-valid | 7/10 | 8/10 |
| Exact documents | 0/10 | 0/10 |
| Primary field accuracy, including extra-row penalties | 141/406 = **34.73%** | 164/406 = **40.39%** |
| Expected-present field accuracy | 105/197 = 53.30% | 118/197 = 59.90% |
| Expected-null field accuracy | 36/145 = 24.83% | 46/145 = 31.72% |
| Header accuracy | 43/70 = 61.43% | 51/70 = 72.86% |
| Ordered-line accuracy | 98/336 = 29.17% | 113/336 = 33.63% |
| End-to-end p50 / p95 | 1.704 / 17.884 s | 1.583 / 10.324 s |
| Reported API cost | $0.03551070 | $0.04512240 |
| Scaled API cost / 1,000 attempted inputs | $3.55107 | $4.51224 |

The approved gold has 342 expected field units. Each candidate added eight
extra rows, adding 64 wrong field units to the primary denominator of 406.
Null/present subsets cover gold fields only. Strict string comparison and
positional line matching can penalize representational differences or row
shifts; these are the declared rules, not an independent semantic review.

Gemini 3.1 truncated S016, S040 and S044; Gemini 3.5 truncated S016 and S040.
Reported output usage was 4,079–4,081 with `finish_reason: length`. Those outputs
remain failed with their partial responses; no repair, output increase or
correction was introduced. Remaining outputs were schema-valid, which does
not establish factual accuracy. Latency uses 10 retry-inclusive input durations
per candidate and nearest-rank percentiles, excluding build/setup.

**Gemini 3.5 is selected from the completed Gemini pair:** its primary
accuracy is about 5.67 percentage points higher and final validity is 80%
versus 70%, at a higher observed cost. Both still have substantial quality
problems. This is a development-set provider selection under the accepted
two-candidate scope, not a production quality claim or a completed
three-candidate comparison.

## Mistral availability failure

`mistralai/mistral-small-2603` through `mistral/zdr` returned HTTP 429 on both
physical attempts for each of S002, S003 and S012. The error metadata identified
`upstream_provider_shared_pool`; no `Retry-After`, model output, token usage or
cost was supplied. Three consecutive failed inputs triggered
`dependency_unavailable:rate_limit`, leaving the other seven inputs untouched.
No route fallback or credential substitution occurred.

Mistral is **unranked**. The evaluator's failure-inclusive zero matches do not
measure this model's extraction capability. Its three short failed-request
durations do not measure generation speed. Catalog availability had passed
before execution; it did not establish shared-pool capacity.

## Accounting and retained evidence

Known screening charges remain **$0.08063310**. Across the original run and
approved retry, 12 Mistral failures have unknown charges, so **$0.50135040**
remains held. Combined screening accounted allowance is **$0.58198350**, not a
claim of billed cost. Including the earlier $0.01518250 smoke, cumulative
accounted spend is **$0.59716600**. Available non-matrix allowance is
**$0.40283400**; the **$3.50 matrix reserve is intact**. No reservation was
guessed free or released. Both runs stopped for dependency availability,
not budget exhaustion.

Before inference, the full offline gate passed 653 tests, Ruff lint/format,
strict mypy, gold validation and corpus preflight. Post-run commands exported
and revalidated all 30 records:

```sh
make hw01-evaluate ARGS='provider-screening-20261022-71'
make hw01-export-run ARGS='provider-screening-20261022-71'
make hw01-verify-export ARGS='provider-screening-20261022-71'
```

The [run bundle](../../results/restored/31349837ab5acff7f512d02ef2ee56a93a7a2da63d01dd8a12ea85acd734288a/submission/provider-screening-20261022-71/) contains
all records/checkpoints, raw returned evidence, resolved configuration, schema,
manifest and hashes. The separate
[evaluation bundle](../../results/restored/31349837ab5acff7f512d02ef2ee56a93a7a2da63d01dd8a12ea85acd734288a/submission/provider-screening-20261022-71-evaluation/)
contains evaluator JSON, a verified summary and byte hashes. Original results
remain unchanged. Raw process/plan logs, config snapshot and evaluation/accounting
evidence with checksums remain in the ignored persistent volume under
`results/screening-runs/provider-screening-20261022-71/`.

## Approved Mistral-only retry — executed and stopped

The user separately approved one fresh Mistral-only invocation within the then
remaining $0.65350920 non-matrix allowance, preserving all existing holds and
the $3.50 matrix reserve. It started at `2026-10-22T12:55:13Z`
(15:55:13 Europe/Kiev), with unchanged route, 10 gold cases, v1/baseline and
4,096 output tokens:

```sh
make hw01-run MODE=provider ARGS='--config config/screening.yaml --stage screening --model provider-mistral --prompt v1 --sampling baseline --coverage results/provider-screening-coverage-20261022.json --allow-server-context --allow-provider --run-id provider-screening-mistral-20261022-71-retry1'
```

Again, S002/S003/S012 each returned two HTTP 429 errors with
`limit_source: upstream_provider_shared_pool`, no `Retry-After`, and no output,
usage or charge. The dependency guard stopped after three failed inputs;
seven were not attempted. The manifest is **incomplete** with zero successes,
three failures and seven untouched inputs. Application exit 3 became Make
error 2. Six additional unknown-charge reservations retain **$0.25067520**.
Neither Gemini was rerun; no fallback or credential substitution occurred.

Saved records were reloaded and evaluated offline, independently checking
selection, sampling, errors, context admissions and cumulative accounting.
The [retry run bundle](../../results/restored/31349837ab5acff7f512d02ef2ee56a93a7a2da63d01dd8a12ea85acd734288a/submission/provider-screening-mistral-20261022-71-retry1/)
and separate
[retry evaluation bundle](../../results/restored/31349837ab5acff7f512d02ef2ee56a93a7a2da63d01dd8a12ea85acd734288a/submission/provider-screening-mistral-20261022-71-retry1-evaluation/)
retain all 10 terminal records and their provenance. Export verification ran in
a fresh offline container; all 24 exported payload hashes were checked on the
host. Process log, configuration, evaluation and accounting summary with
checksums remain in the persistent volume under
`results/screening-runs/provider-screening-mistral-20261022-71-retry1/`.
The original run and its exports remain unchanged. The two evaluations are
separate: pooling overlapping Mistral observations would double-count cases
and is rejected by the evaluator.

## Accepted selection and frozen configuration

The user accepted finalizing 7.1 with the Gemini pair on 22 October. Mistral was
optional and is excluded from capability ranking because neither invocation
returned an extraction. No additional model call was needed for this decision.

Select **Gemini 3.5 Flash-Lite**: it leads 3.1 by **23/406 field matches**, about
**5.67 percentage points**, with **8/10 versus 7/10** schema-valid outputs.
Present-value, null-value, header and ordered-line scores also improve. Observed
p50/p95 latency is lower. The tradeoff is **$0.00961170 more** over these 10 cases
(about **27.1%**): $0.04512240 versus $0.03551070. Accuracy was prioritized over
this measured cost difference; both candidates still have zero exact documents.
The 10 gold cases were used for selection and are development data, not an
independent held-out evaluation. The reasons for the low absolute scores include
truncation, extra catalog rows, conservative field semantics and strict string/
positional comparison. No prompt, output limit or scoring rule was tuned here.

[`config/experiments.yaml`](../../config/experiments.yaml) now freezes the main
provider as `google/gemini-3.5-flash-lite` through `google-ai-studio`, under the
main model ID `provider`. The selection evidence uses screening ID `provider-35`;
the model and route are identical. Screening configuration and historical
records retain their original IDs and bytes. The main configuration keeps
local as its safe default, v1/baseline, temperature 0, top_p 1, 4,096 output tokens
and the existing execution/budget policy.

**7.2 is next and has not run.** It begins with full-corpus v1/baseline on both
selected models. Refresh pricing/identity evidence and prepare coverage matching
the selected main ID/model before any paid matrix phase: historical 3.1 coverage
must not be reused under the now-3.5 `provider` ID. Matrix context policy and the
concrete paid invocation still require their own acceptance. No new inference
is authorized by completing 7.1. Cumulative accounting remains $0.59716600,
including $0.50135040 in unknown-charge holds; $0.40283400 remains outside the
protected $3.50 matrix reserve.
