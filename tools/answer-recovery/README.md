# E03 financial recovery entrypoint

Executed after separate paid approval on 2026-11-10: two physical calls,
$0.0111975 additional cost, $0.3655965 total pilot cost, no stop. Both responses
passed mechanical checks. Do not rerun it; the journal and paid-key guards
preserve the single approved invocation. See the
[pilot report](../../docs/reports/P03-rag-pilot.md).

This is a separately versioned operational addendum, not a second generation
implementation. It reuses the unchanged application `AnswerRunner`, admission,
adapter/client ownership, dependency policy and cumulative ledger. It lives
outside `src/` because E03-v1 froze that entire source inventory before calls.
Its own manifest binds the controller, tests, profile and Compose overlay.

R01 may select only Q38/BM25 and Q38/vector from the exact stopped pilot receipt.
Both were never sent. The original $0.354399 is counted in the revised **$2.10
total pilot exposure envelope**; it is not billed or reserved again. No model,
prompt, schema, evidence, reasoning, sampling, deadline, retry or correction
setting changes. No prior physical observation may be retried or overwritten.

The original stopped journal remains authoritative and the old continuation
command still rejects it. Recovery does not automatically unlock remaining28;
joint receipt review and a separate continuation invocation remain necessary.

```sh
make answer-recovery-check
make answer-recovery-freeze
make answer-recovery-plan
# Separate approval of this concrete paid invocation is required:
make answer-recover ARGS='--allow-provider --allow-server-context'
make answer-recovery-export
```

Offline commands have no network or provider credentials. Tests use an isolated
temporary ledger and fake adapter; they do not count as model observations.
