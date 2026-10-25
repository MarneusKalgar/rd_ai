# Provider smoke preparation — 6.6.6

**Evidence retrieval:** Bulk evidence is in the [submission-history archive](../../archive-index/31349837ab5acff7f512d02ef2ee56a93a7a2da63d01dd8a12ea85acd734288a.json). Follow the [restore instructions](../guides/archiving-results.md#historical-submission-evidence) before opening restored-file links. Original run IDs and export paths retain their historical meaning.

## Status on 22 October 2026

Native and provider live acceptance are recorded in the
[provider execution evidence](provider-runtime-verification.md). The approved
smoke spent $0.01518250 and retained two valid outputs plus one truncation;
all three exported records passed verification. Preparation below precedes
that invocation and does not authorize another run. The active provider is
`google/gemini-3.1-flash-lite` through `google-ai-studio`. Gemini 3.8 remains a
historical integration reference, not the active smoke candidate. This smoke
does not select the final provider for the section 7 matrix.

The intended selection is S030, S026 and S008 (`B02-S030-PO01`,
`B02-S026-PO01`, `B02-S008-PO01`), unchanged v1/baseline settings, temperature 0,
top_p 1 and a 4,096-token output allowance. No v2 prompt or additional output
increase is part of this acceptance.

## Accounting and route preparation

The user declared no prior HW-01 provider spend. An authenticated OpenRouter
metadata GET independently reported key usage zero. Offline initialization
created the existing cumulative ledger with opening spend $0, budget $4.50,
matrix reserve $3.50 and zero reservations. Initialization did not execute a
model. Future commands must reopen this ledger rather than reset it.

The [Google AI Studio endpoint catalog](https://openrouter.ai/api/v1/models/google/gemini-3.1-flash-lite/endpoints)
advertises the required sampling/structured-output parameters, context
1,048,576 and output limit 65,536. Standard text pricing is $0.25 input and
$1.50 output per million tokens. Route and billing evidence must be refreshed
before an approved paid invocation.

## Tokenizer research

Google's official SDK maps `gemini-3.1-flash-lite` to the public
`google/gemma-4-E4B-it` tokenizer:

- [Mapping source](https://github.com/googleapis/python-genai/blob/main/google/genai/_local_tokenizer_loader.py)
  snapshot SHA-256: `eff7d8520c4656655cd42d3a7e981093fbd9cee8017db255c58df5112174df3c`.
- Tokenizer revision: `ee0ef6023621cff504d758262d4e04895a5af4a2`.
- Tokenizer JSON SHA-256: `cc8d3a0ce36466ccc1278bf987df5f71db1719b9ca6b4118264f45cb627bfe0f`.
- The download used public GET requests in Docker; no Google or Hugging Face
  credential, host Python package or inference was required.

| Input | Message text tokens, including embedded schema | Separate schema JSON tokens |
| --- | ---: | ---: |
| S030 | 1,148 | 878 |
| S026 | 1,990 | 878 |
| S008 | 22,261 | 878 |

These are actual local tokenizer counts of those strings. They exclude unknown
upstream framing/transformations and are **not full-request admission
certificates**. No live coverage file was fabricated from them. The private
results-volume directory `results/setup/provider-tokenizer-20261022/` retains
the source snapshot, tokenizer and diagnostic report. The current exact-request
certificate path therefore still rejects these requests without certificates.

## Approved context policy

On 22 October the user explicitly approved delegating context-limit rejection
to the provider for this smoke. The implemented alternative disables prompt
compression, retains the full request, pins the standard/default service tier
and records that no locally verified complete-request bound is available.
The counted path remains the default; there is no automatic fallback. Selecting
this policy requires coverage `context_enforcement: "provider"`, smoke stage
and `--allow-server-context`, in addition to eventual paid-run approval.

The current catalog context must match coverage, and input pricing must cover
that entire context. Both initial and actual correction requests reserve before
generation. Checkpoints identify provider enforcement with null counter/token
bound. Existing counted checkpoints remain reloadable.

Protocol references: [compression disabled means context overflow is an error](https://openrouter.ai/docs/guides/features/message-transforms),
[default tier pins standard pricing](https://openrouter.ai/docs/guides/features/service-tiers),
and [Gemini output limits include thinking tokens](https://ai.google.dev/gemini-api/docs/generate-content/thinking).

This alternative would reserve the full advertised context at the current
input rate, plus the configured output allowance and request fee:

`1,048,576 × $0.00000025 + 4,096 × $0.0000015 = $0.268288` per physical call.

Three primary calls would reserve up to $0.804864 in total before considering
settlement. The configured retry/correction maximum is 12 physical calls, whose
unconstrained reservation total would be $3.219456; the existing $1 non-matrix
allowance would stop work earlier when needed. Unknown billed cost must retain
its reservation. This is a conservative allowance, not an expected bill or a
claim that every allowed retry fits the smoke budget.

The user subsequently approved the concrete paid invocation below. That
approval was consumed by the recorded smoke; future paid runs require their
own approval. A paid probe is not a token counter.

## Approved invocation — executed once

`make hw01-check` passed on 22 October: **626 tests**, Ruff lint/format,
strict mypy, all 10 frozen gold objects and the 30-input preflight. The 12 new
controlled tests cover correction/full-input preservation, exact routing and
compression controls, opt-in/stage gates, full-context pricing coverage,
catalog drift, unknown-cost reserve protection, offline planning, retained HTTP
failure and compatibility with historical counted evidence. No frozen inputs,
schema, gold labels, prompt or dependency declarations changed.

Metadata-only GETs at `2026-10-22T10:40:00Z` verified the exact 3.1 Flash-Lite
route, required parameters, context, output limit and rates above. The key still
reported zero usage; the cumulative ledger still held $0 and no reservations.
The ignored persistent results volume now contains:

- `results/setup/provider-readiness-31-20261022.json`: metadata/accounting snapshot.
- `results/provider-coverage-31-20261022.json`: validated provider policy and
  full-context pricing evidence, without fabricated request certificates.

After successful offline verification and explicit human approval, the following
command was executed from the repository root:

```sh
make hw01-smoke MODE=provider ARGS='--model provider --prompt v1 --sampling baseline --input B02-S030-PO01 --input B02-S026-PO01 --input B02-S008-PO01 --coverage results/provider-coverage-31-20261022.json --allow-server-context --allow-provider --run-id provider-smoke-31-20261022'
```

The invocation uses the existing $1 smoke pool and preserves the $3.50 matrix
reserve. It permits at most one correction per input and one transport retry
per attempt, with reservation before every physical call. A missing charge
keeps its $0.268288 allowance accounted. Saved run IDs cannot be replayed or
overwritten automatically. Preparation made no generation call; the separately
approved invocation produced the [recorded live results](provider-runtime-verification.md).
