# Provider extraction evidence — 22 October 2026

**Plan 6.6.6 is accepted for both adapters.** The approved provider smoke
completed all three inputs and its export passed verification in a fresh offline
container. Together with the [native local smoke](native-runtime-verification.md),
this verifies the integration path. Each run retains two schema-valid outputs
and one truncation. Field accuracy and the complete matrix remain sections 7–8.

## Approved scope and execution

- Run: `provider-smoke-31-20261022`, created at `2026-10-22T10:45:22Z`
  (13:45:22 Europe/Kiev).
- Model: `google/gemini-3.1-flash-lite`, exact route `google-ai-studio`.
  Responses reported that model and serving provider `Google AI Studio`.
- Same S030/S026/S008 inputs, frozen schema, v1 prompt and baseline sampling
  as native acceptance. No private workbook or gold label entered requests.
- Explicit request settings: temperature 0, top_p 1, max_tokens 4,096,
  non-streaming JSON Schema, default service tier, no route fallback and context
  compression disabled. Catalog support was checked at setup; responses do not
  independently attest every sampling parameter's application.
- User-approved provider-enforced context policy, advertised context 1,048,576
  and full-context cost reservation. Checkpoints record null verified prompt
  bound/counter identity. This is not a local proof of complete-request fit;
  see [policy and preparation](provider-smoke-preparation.md).
- Human approval covered this one invocation with the existing $1 smoke pool
  and protected $3.50 matrix reserve. No other provider run was scheduled.

```sh
make hw01-smoke MODE=provider ARGS='--model provider --prompt v1 --sampling baseline --input B02-S030-PO01 --input B02-S026-PO01 --input B02-S008-PO01 --coverage results/provider-coverage-31-20261022.json --allow-server-context --allow-provider --run-id provider-smoke-31-20261022'
```

This is the execution record. Its run ID already exists; automatic overwrite
or replay is refused. A new paid invocation requires separate approval.

## Saved outcomes

| Input | Outcome | Attempts | Input / output tokens | Input duration | Billed USD |
| --- | --- | ---: | ---: | ---: | ---: |
| B02-S030-PO01 | Schema-valid, one line | 1 | 1,149 / 196 | 2.195 s | $0.00058125 |
| B02-S026-PO01 | Schema-valid, 14 lines | 1 | 1,991 / 1,612 | 3.698 s | $0.00291575 |
| B02-S008-PO01 | Truncated | 1 | 22,262 / 4,080 | 8.907 s | $0.01168550 |

Input durations include coordinator admission/accounting/checkpoint work,
excluding image build and setup. Physical HTTP durations were 2.175, 3.678 and
8.887 seconds. All responses reported zero reasoning tokens. No correction or
transport retry was used. No prompt, corpus, schema or dependency change was made.

S008 returned `finish_reason: length`, native reason `MAX_TOKENS`. The configured
allowance was 4,096; reported output usage was 4,080. Preserve both observations
without inventing missing usage. The partial response and truncation issue are
saved. The shared policy treats truncation as terminal; it did not increase the
allowance, shorten the source or issue a correction.

The manifest is `complete`: succeeded 2, failed 1, not_attempted 0,
`comparison_complete: true`, with no budget or dependency stop. Application exit
**1** reports the retained failed extraction; Make wrapped it as error 2.
Completed selected work does not establish perfect extraction quality.

## Accounting and durable evidence

Each physical request reserved **$0.268288** before generation. All three
reservations settled to the reported response charges; none remains unresolved.
The cumulative ledger now accounts for **$0.01518250** (about **1.52 US cents**),
including truncation. With opening spend $0, this leaves $0.98481750 in the
smoke pool and $4.48481750 in the overall $4.50 budget. The **$3.50 matrix reserve
is intact**. These are reported charges reconciled locally, not an independent
audit of the provider invoice.

Before paid execution, the offline gate passed **626 tests**, Ruff lint/format,
strict mypy, all 10 gold validations and the 30-input preflight. Export and
independent reload succeeded afterward:

```sh
make hw01-export-run ARGS='provider-smoke-31-20261022'
make hw01-verify-export ARGS='provider-smoke-31-20261022'
```

The [exported bundle](../../results/submission/provider-smoke-31-20261022/)
contains all three records/checkpoints, raw returned bodies, frozen schema,
resolved experiment/setup metadata, manifest and byte hashes. Raw operational
logs, offline plan and a verified accounting/outcome summary with checksums are
retained in the ignored Docker results volume under
`results/smoke-runs/provider-smoke-31-20261022/`. Pricing/readiness evidence and
the tokenizer diagnostic remain under `results/setup/` and the separate ignored
coverage file. The cumulative ledger is preserved and excluded from exports.

No full-corpus provider/local run, prompt v2, screening, scoring or increased
provider output allowance follows automatically. The interrupted Docker smoke
keeps its status; native and provider evidence complete 6.6.6 without rewriting
that run. Optional section 6.7.3 remains deferred.
