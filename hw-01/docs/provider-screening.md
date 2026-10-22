# Provider screening — plan 7.1

## Scope and current status

**7.1 is complete under the user-accepted Gemini-pair scope.** The
[recorded results](provider-screening-results.md) select Gemini 3.5 Flash-Lite
through `google-ai-studio` from the two completed candidates. Optional Mistral
remains unavailable/unranked after the original invocation and one approved
retry. Historical manifests, failed requests and accounting holds are preserved.
No further paid invocation is authorized.
The offline gate passed **653 tests**, Ruff lint/format, strict mypy, all 10
gold validations and the 30-input preflight. The 27 added regressions cover
scoring arithmetic/order/null penalties, saved evidence integrity, unknown cost,
three-candidate CLI execution/evaluation, stage/selection gates and reasoning
price drift. A real offline evaluation of the existing smoke reproduced its
$0.01518250 cost and reported no gold scores for its three unlabeled inputs.
No new inference was needed for these checks.
The user approved extending provider-enforced context to **screening only** on
22 October 2026. Coverage defaults remain smoke-only; the screening coverage
explicitly permits screening. Matrix/repetition stages remain rejected.

The same 10 approved gold inputs are selected automatically in corpus order,
with unchanged v1 and baseline (temperature 0, top_p 1, output allowance 4,096).
Explicit input overrides must name every gold input exactly once. The command
requires explicit provider model IDs; merely listing candidates in
`config/screening.yaml` does not schedule them. Its default selection remains
local. The screening configuration, v1 prompt and frozen data are unchanged. The main
`experiments.yaml` now selects Gemini 3.5 as its `provider` model, retaining
local as the safe default; see the recorded selection and coverage requirements.

This is **30 primary requests**, with at most **120 physical requests** under
the existing correction/retry bounds. Actual requests/costs, including failures,
remain in the shared ledger. No local model or full-corpus/v2 matrix is run.

## Metadata and reservation evidence

Public unauthenticated endpoint GETs on 22 October verified these exact
standard/default routes, their required sampling/structured-output parameters,
advertised context, output capacity and rates:

| Candidate / route | Context | USD per million input / output | Reservation per physical call |
| --- | ---: | ---: | ---: |
| [Gemini 3.1 Flash-Lite](https://openrouter.ai/api/v1/models/google/gemini-3.1-flash-lite/endpoints), `google-ai-studio` | 1,048,576 | $0.25 / $1.50 | $0.26828800 |
| [Gemini 3.5 Flash-Lite](https://openrouter.ai/api/v1/models/google/gemini-3.5-flash-lite/endpoints), `google-ai-studio` | 1,048,576 | $0.30 / $2.50 | $0.32481280 |
| [Mistral Small 4](https://openrouter.ai/api/v1/models/mistralai/mistral-small-2603/endpoints), `mistral/zdr` | 262,144 | $0.15 / $0.60 | $0.04177920 |

Each reservation covers full advertised input context plus 4,096 output tokens
and applicable fixed fees. Output pricing includes reasoning where applicable;
see [OpenRouter reasoning limits](https://openrouter.ai/docs/guides/best-practices/reasoning-tokens),
[Gemini output limits](https://ai.google.dev/gemini-api/docs/generate-content/thinking)
and [Mistral completion limits](https://docs.mistral.ai/api/endpoint/chat).
No reasoning override, tool or paid plugin is added. Context compression and
fallback are disabled and the default service tier is pinned. Catalog support
does not independently attest application of every parameter or acceptance of
every schema keyword; live failures must remain recorded.

The verified existing ledger accounts for **$0.01518250**, leaving
**$0.98481750** available for non-matrix work and **$3.50 protected for the
matrix**. It must not be reinitialized. The unconstrained reservation ceiling
for all 120 possible calls is **$25.395200**; the ledger's existing allowance
stops work earlier when needed. Reservations settle to reported charges after
each completed call, so the ceiling is not an expected bill. Unknown charges
retain their reservation. A budget stop leaves screening incomplete and does
not authorize a larger allowance or another invocation.

The ignored results volume retains dated metadata under
`results/setup/provider-screening-20261022/` and operator-verified coverage at
`results/provider-screening-coverage-20261022.json`. No extra API key is needed.

## Commands — original approved invocation executed once

From the repository root, plan without network or inference:

```sh
make hw01-plan-run ARGS='--config config/screening.yaml --stage screening --model provider --model provider-35 --model provider-mistral --prompt v1 --sampling baseline --coverage results/provider-screening-coverage-20261022.json --allow-server-context --run-id provider-screening-20261022-71'
```

After the offline gate and explicit approval, this invocation was executed:

```sh
make hw01-run MODE=provider ARGS='--config config/screening.yaml --stage screening --model provider --model provider-35 --model provider-mistral --prompt v1 --sampling baseline --coverage results/provider-screening-coverage-20261022.json --allow-server-context --allow-provider --run-id provider-screening-20261022-71'
```

Then evaluate saved records offline, export all outcomes and verify the export:

```sh
make hw01-evaluate ARGS='provider-screening-20261022-71'
make hw01-export-run ARGS='provider-screening-20261022-71'
make hw01-verify-export ARGS='provider-screening-20261022-71'
```

The original run is incomplete and accounted $0.33130830, comprising
$0.08063310 in reported charges plus $0.25067520 held for unknown Mistral
charges. The separately approved Mistral-only retry also stopped on HTTP 429,
adding $0.25067520 in unknown-charge holds. Current cumulative accounted spend
is $0.59716600, with $0.40283400 remaining outside the protected $3.50 reserve.
The preparation snapshot above is historical. Original and retry exports
passed independent verification. See the results document for both outcomes
and the accepted Gemini-pair selection; no further paid invocation is authorized.

Use the [shared evaluator](evaluation.md); no screening-specific scoring rules
or model calls are introduced by evaluation. Choose the main provider only
from candidates with comparable completed evidence on the same 10 cases. The
user accepted the completed Gemini pair; unavailable optional Mistral is unranked.
Prioritize primary field accuracy (including extra-row penalties), inspect
present/null and header/line results, then final validity, billed cost and
latency as tradeoffs/tie breakers. Disclose the cases used for selection.
Incomplete or unverified candidates remain unranked. Document the rationale
and freeze the chosen route before the full-corpus v1/baseline matrix phase;
selection does not automatically run that phase or create v2.
