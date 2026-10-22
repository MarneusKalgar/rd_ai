# Required provider/local matrix — plan 7.2

## Latest status after the stronger-model diagnostic

**Latest follow-up:** the separately approved stronger Flash gold10 run at
16,384 is complete: 10/10 valid, no truncations, 278/342 (81.29%) field accuracy,
one exact document and no extra/missing rows. The entire gain over its 8,192
run is S040 completion. S040 used only 6,260 tokens this time, so reasoning
variability prevents claiming a necessary token threshold. No further allowance
increase is needed for this diagnostic. See the
[full comparison](stronger-model-experiment.md).
After its $0.32986350 cost, cumulative accounted spend is $1.77332305,
including unchanged $0.50135040 earlier holds. Current remaining allowance is
$2.72667695, including $2.32384295 protected matrix funds. Required matrix
profiles remain unchanged; no v2 inference or additional paid run is approved.

**Follow-up update:** the separately approved 8,192-token comparison on the
same gold10 is complete: Flash-Lite 18.20%, Flash 59.94%, nine valid outputs
each; both truncated S040. The diagnostic cost $0.39944890. Current cumulative
accounted spend is $1.44345955, including the unchanged $0.50135040 prior holds;
$3.05654045 remains, including $2.65370645 protected matrix funds. The result
and its extra-row/output-budget interpretation are retained in the
[diagnostic report](stronger-model-experiment.md). The selected required matrix
profiles remain unchanged pending a scope decision; no v2 inference has run.

Both required v1/baseline runs are complete, including the native thinking=false
rebaseline (21/30 valid, nine truncations, 17.24% gold field accuracy). The
thinking-enabled native run remains diagnostic. V2 and exploratory sampling
have been drafted after baseline review; neither has been run. The updated
offline gate passed 672 tests, lint/format, types, gold validation and preflight.

At the user's request, remaining variants were deferred for a separately
approved [Flash gold-set diagnostic](stronger-model-experiment.md), now complete
and excluded from required matrix membership. Flash scored 33.52% against
Lite's 40.15% under v1/4,096 tokens, with reasoning-heavy truncations. Flash-Lite
remains the selected provider; no further paid invocation is approved.

After the diagnostic's $0.29324205 settled cost, cumulative accounted spend is
$1.04401065 (including $0.50135040 of earlier unknown-charge holds). Remaining
total allowance is $3.45598935; protected matrix funds are $3.05315535. Historical
phase-opening balances below are retained as history, not current availability.
The remaining required matrix still contains 180 primary requests.

## Scope and phase boundaries

The matrix uses all 30 frozen neutral inputs for each of eight variants:
selected provider/local × v1/v2 × two sampling settings. That is **240 primary
requests**, plus bounded corrections/retries. Factual accuracy is scored on the
10 approved gold cases; all 30 contribute operational metrics. Gold cases used
for screening and prompt development are development data.

The selected provider is Gemini 3.5 Flash-Lite through `google-ai-studio`.
The selected local deployment is the existing native Ollama desktop server with
`gemma4:e4b-it-qat`, the pinned digest and a 32,768-token effective context.
Python and evidence handling remain in Docker. Docker CPU results remain a
separate compatibility/runtime comparison.

1. **Full-corpus baseline:** run unchanged v1/baseline on both models, 30 inputs
   each, with temperature 0, top_p 1 and 4,096 output tokens. Preserve the resolved
   configuration, prompt/schema/input hashes, runtime identities and admissions.
2. **Review:** evaluate both saved baseline runs and inspect failures and
   representative outputs. A schema failure/truncation is a measured outcome;
   a stopped run with untouched inputs is an incomplete phase. Do not create v2
   until both baseline runs have completed and their evidence has been reviewed.
3. **Remaining variants:** freeze v2 and a second explicit sampling setting,
   then run v1/second-sampling and v2/both-sampling on both models over all 30
   inputs: 180 additional primary requests. Keep matched execution/output limits.
4. **Aggregate:** retain the baseline's 60 observations once, with their original
   run/configuration hashes. Use the shared evaluator; do not pool overlapping
   observations, screening or smoke records into a matrix variant.

No v2 or second sampling setting is introduced before the baseline review.
No output limit, frozen data/schema/gold or scoring rule is changed to improve
this baseline's score. See [the accepted provider selection](provider-screening-results.md)
and [evaluation rules](evaluation.md).

## Provider context and spending

On 22 October 2026 the user accepted extending provider-enforced context to the
**matrix stage**. Each coverage document must explicitly include
`server_context_stages: ["matrix"]`, and the invocation still requires
`--allow-server-context`. Historical smoke/screening coverage does not authorize
matrix execution. The repetition stage remains excluded.

Retain full source and schema, disabled compression and route fallback, the
standard/default service tier, and an explicitly unverified complete-request
token count. Refresh exact endpoint capabilities, context and pricing before
execution. Reserve the full advertised context plus the output allowance and
applicable fees before every physical call. Settle to reported actual cost;
unknown charges retain their reservations. The policy acceptance does not
approve a paid invocation or attest that an individual request fits.

The existing cumulative ledger must be reopened, not reinitialized. Before this
phase it accounts for **$0.59716600**, including **$0.50135040** held for unknown
Mistral error charges. **$3.50** is protected for matrix work; the remaining total
budget is **$3.90283400**. Matrix calls may consume that reserve and reduce its
remaining amount. The runner enforces the existing $4.50 cumulative budget,
below the assignment's $5 cap. Each paid phase requires separate approval of
its exact command and allowance; no automatic continuation is authorized.

## Readiness and evidence

Preparation checks public provider metadata and native `/api/version`,
`/api/tags` and `/api/ps` without generation. Actual local composition checks
version compatibility, weights, installed tokenizer, loaded context and
CPU/GPU placement; each request then passes complete rendered-request admission.
Model loading/setup is recorded separately from input latency. Stop Docker
Ollama before native execution to avoid competing resident model memory.

Use unique run IDs for provider and local phases, preserve incremental attempts
and all terminal outcomes, then export and verify each run independently in a
fresh offline container. Save process logs, metadata/pricing evidence, ledger
summaries and offline evaluation with checksums. Track curated submission
bundles in Git; keep credentials, working logs and the mutable ledger ignored.

**Initial baselines are complete; the user-approved thinking-disabled local rebaseline is running.** The offline gate passed **659 tests**,
Ruff lint/format, strict mypy, all 10 gold validations and 30-input preflight.
Six new controlled regressions verify full-corpus matrix scheduling, gold-only
accuracy, prior-spend preservation, matrix-reserve accounting and stage/opt-in
rejection. Both initial native/provider baseline invocations completed all 30 inputs.
The user separately approved the concrete provider command and initial
$3.90283400 remaining cumulative allowance on 22 October. The user accepted explicit local thinking=false and a new 30-input native
baseline; no v2 or later phase has started.

### Metadata preparation — 22 October 2026

At 14:43 UTC, metadata-only preparation confirmed native Ollama **0.40.7** and
model digest `ee665637121887cf3befff38abbb1be4ee117c7db867d97a67e29049ecd7e15f`.
The installed weights occupy 6,146,501,801 bytes. No Docker Ollama service was
started. Native setup/loading and effective placement will be checked by the
actual runner before extraction, separately from document timing.

At 14:44 UTC, the public exact-route catalog confirmed Gemini 3.5 Flash-Lite /
`google-ai-studio`, required parameters, route status 0, 1,048,576 context tokens
and a 65,536-token advertised output maximum. The experiment retains its
4,096-token output allowance. Standard text rates are $0.30/million input and
$2.50/million output, including internal reasoning where advertised; no fixed
request fee. No paid search, image/audio input, tools or plugins are enabled.
Every physical call reserves **$0.32481280** before settling reported cost.
The verified metadata/coverage is retained under
`results/setup/matrix-v1-baseline-20261022/` and
`results/provider-matrix-coverage-20261022.json`. The resolved baseline
configuration SHA-256 is
`bb5f59390d79095e195f589f026415577a56222b20873f472e02b868966981ee`.

The provider's 30 primaries would reserve $9.744384 if none settled before the
next call; the 120-call configured maximum has an unconstrained reservation
ceiling of $38.977536. These are **not expected bills**. Serial settlement and
the existing $3.90283400 remaining cumulative allowance constrain execution;
unknown charges retain their reservation and can cause an early stop. The
10-case screening cost $0.04512240 for this model, but scaling it to the full
corpus is only a rough indication because document sizes and failures differ.

### Phase-one schedule and commands

The offline plan selects exactly 60 primaries / at most 240 physical calls across
the two models. Each separate model invocation selects 30 / at most 120.
There are no gold-only filters and no v2 or alternate-sampling jobs.

Native inference authorized by the 7.2 implementation request uses the desktop
server, through this command from the repository root:

```sh
make hw01-run MODE=native ARGS='--stage matrix --model local --prompt v1 --sampling baseline --run-id matrix-native-v1-baseline-20261022-72'
```

The user separately approved this exact provider command and allowance before execution:

```sh
make hw01-run MODE=provider ARGS='--stage matrix --model provider --prompt v1 --sampling baseline --coverage results/provider-matrix-coverage-20261022.json --allow-server-context --allow-provider --run-id matrix-provider-v1-baseline-20261022-72'
```

The provider invocation may use the existing remaining $3.90283400 cumulative
allowance, including the matrix reserve; unknown Mistral charges remain held.
No additional phase is scheduled by either command. Both use the same frozen
baseline configuration. Run IDs are unique evidence identities, not replay
commands. After execution, record approval/status/outcomes below before any
continuation.

### Provider v1/baseline — completed

The separately approved provider run started at **14:51:56 UTC** on 22 October.
All 30 inputs were attempted once: **25 schema-valid outputs, five truncations,
zero untouched inputs**, no corrections/retries and no budget/dependency stop.
The manifest is `complete`; application exit 1 (Make error 2) accurately reports
failed extractions and does not mean the corpus run was interrupted.

Truncated inputs: S005, S014, S016, S019 and S040. Each retains the partial raw
response and `finish_reason: length`, with 4,079–4,080 reported output tokens.
No output allowance was increased and no partial JSON was repaired.

The 10 gold cases scored **163/406 = 40.15%** primary field accuracy, with
**0/10 exact documents**. Header matches were 51/70 and ordered-line matches
112/336. Extra rows add 64 wrong comparisons to the 342 expected gold field
units. This differs slightly from the earlier screening's 164/406 despite the
same controls; deterministic sampling settings do not establish byte-identical
provider outputs across separate requests.

Across all 30 inputs: validity **83.33%**, p50 **2.614 s**, p95 **9.588 s**,
30 physical calls and no unknown charges. Reported cost was **$0.15360260**;
all call reservations settled. Cumulative accounted spend is **$0.75076860**,
including unchanged historical unknown-charge holds of **$0.50135040**.
Remaining total allowance is **$3.74923140**; the unspent protected matrix
amount is **$3.34639740**. These are ledger amounts, not a claim that the
unknown historical charges were billed.

The [provider run bundle](../results/submission/matrix-provider-v1-baseline-20261022-72/)
contains all 30 records/checkpoints and hashes; its records revalidated in a
fresh offline container. The separate
[evaluation bundle](../results/submission/matrix-provider-v1-baseline-20261022-72-evaluation/)
contains the unchanged shared evaluator output and verified accounting summary.
Process/plan logs, configuration snapshot, evaluation and summary with checksums
are retained in `results/matrix-runs/matrix-provider-v1-baseline-20261022-72/`.
The native baseline subsequently completed; see its review and profile decision below.

The running native baseline's saved setup confirms a 32,768-token context,
Ollama 0.40.7 and GPU-resident memory (`size_vram` equals reported loaded
`size`: 3,234,773,072 bytes). This is the runtime's placement evidence, not
a claim that every operation is GPU-only. Initial loading took 17.467 seconds,
recorded separately from per-input durations. The tokenizer SHA-256 is
`42e3a238e10726346e996c7e3569fcfb2e8d47173944a3cd56826d8dc4d9a9fb`.

### Native v1/baseline — completed diagnostic, thinking enabled

`matrix-native-v1-baseline-20261022-72` completed all 30 inputs: **19 valid,
11 truncated, zero untouched**, 30 physical requests, no correction/retry and no
dependency/budget stop. Its gold score is **89/406 = 21.92%**, exact documents
0/10, p50/p95 60.325/158.297 seconds. Model setup/loading is separate. Native
API cost is zero; cumulative provider accounting is unchanged at $0.75076860.
Both baseline exports and evaluations are retained and independently verified.

The [baseline review](matrix-baseline-review.md) found thinking enabled in all
30 raw responses. Six inputs consumed all 4,096 tokens in thinking before
emitting any answer; the installed `/api/show` metadata confirms default=true
and supports false. The user accepted disabling thinking and rerunning only the
native baseline before v2; the new run is recorded below. The completed provider
baseline stays reusable. V2 and the remaining 180 required requests have not
started. The model residency expired during the review pause and was reloaded
for the newly authorized run. Preserve this completed thinking-enabled diagnostic.

### Thinking-disabled native rebaseline — authorized and started

The user accepted explicit thinking=false and a fresh 30-input native
v1/baseline, then renewed the instruction to continue after pausing before
execution. No generation occurred during that pause. The offline gate passed
**672 tests**, Ruff lint/format, strict mypy, gold validation and corpus preflight.
Both historical baseline exports still revalidate under the new optional fields.

The new run is `matrix-native-v1-baseline-nothink-20261022-72`:

```sh
make hw01-run MODE=native ARGS='--stage matrix --model local --prompt v1 --sampling baseline --run-id matrix-native-v1-baseline-nothink-20261022-72'
```

The only intended execution-profile change is explicit local thinking=false.
The same desktop Ollama runtime, model digest, 32,768 context, frozen v1/schema/
inputs, baseline sampling, 4,096 output allowance and execution/budget policy
remain. The configuration SHA-256 is
`b6d38d16fc8b6e0bf0f3f17bf449f604604bf6caf00200245d2d4ff1fc089a0f`.
Render-only admission, initial generation and any correction all send the same
thinking control. Setup/admission evidence records it; the request fingerprint
binds it. Aggregation separates differing thinking profiles.

The original thinking-enabled native run is retained as a separate diagnostic,
not a duplicate required matrix observation. The completed provider baseline is
reused unchanged. No extra provider call is included in this rebaseline. The
new local baseline must complete and be reviewed before v2 is created. Its raw
response envelopes will be checked for absent/empty thinking fields, rather than
assuming the requested control was honored.
