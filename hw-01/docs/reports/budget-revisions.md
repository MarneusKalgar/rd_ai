# Audited experiment budget revisions

The user authorized increasing the cumulative experiment ceiling from $4.50
to **$10**. OpenRouter's key limit and this application's ledger policy are
separate controls. The original assignment's up-to-$5 allowance is retained
as history; the higher experiment budget is an explicit user extension.

## Explicit cap raise

`budget-raise` is an administrative operation with no model/network calls.
It requires the configured new cap, the expected previous cap and authorization
evidence. It locks the ledger, validates both policies, backs up the exact old
bytes under `results/budget-policy/<sha256>.json`, then atomically writes the
new cap and an appended revision. Opening spend, reservation IDs/request keys,
prices, charges, resolution states and the matrix reserve remain unchanged.

The real migration completed on **23 October 2026 at 06:59:10 UTC**:

- Old cap $4.50; new cap $10; matrix reserve still $3.50.
- All **105 reservations** preserved.
- Accounted spend unchanged at **$1.77332305**, including **$0.50135040** in
  earlier unresolved charges. The rounded provider dashboard is not sufficient
  evidence to release those holds.
- Conservative remaining allowance after migration: **$8.22667695**.
- Prior ledger SHA-256:
  `2b00d7f326781fe5a0bbeac49c41a6d4a8321d2bcc24c89e84caf41e724282fd`.

The already executed command is recorded below as history; replaying the
expected-old-cap operation is rejected:

```sh
make hw01-budget-raise ARGS='--config config/matrix.yaml --expected-budget 4.5 --evidence user-approved-USD10-experiment-budget-in-chat-20261022'
```

Do not reset or initialize the existing ledger. Missing/corrupt ledgers, cap
reductions, changed matrix reserves, inconsistent backups and stale expected
caps are rejected. If replacement fails before committing, the original ledger
and backup remain; a deliberate retry requires the same old cap and exact
matching backup. A successful raise adds one revision even under concurrent
attempts. The implementation accepts finite positive experiment caps up to $10.

## Revised configuration and historical evidence

Use **`config/matrix.yaml`** for the revised experiments and budget commands:

```sh
make hw01-budget-show ARGS='--config config/matrix.yaml'
```

It selects stronger Flash and native Gemma, both at 16,384 output tokens, with
baseline and exploratory sampling. Only v1 is registered there until revised
full-corpus baselines are reviewed and v2 is frozen. Historical configurations
retain their $4.50 policies; the existing main-file v2 draft/work remains intact.
A historical policy does not admit new calls against the $10 ledger by default.
Native matrix execution additionally requires `HW01_CONTEXT_LENGTH=49152`.

Read-only historical export verification continues to accept original records.
Default evaluation still separates differing budget policies. Explicit
`evaluate --allow-budget-revision` verifies the ledger's revision chain and
backup hashes, permits only caps in that audited chain, and normalizes only
the cumulative cap for grouping. It retains each source execution policy,
manifest hash and run/configuration identity in the report. Deadlines, retries,
matrix reserve, context, thinking, model, prompt and sampling are still matched;
duplicate input observations remain errors. No source manifest is rewritten.

```sh
make hw01-evaluate ARGS='source-run continuation-run --allow-budget-revision'
```

The complete offline gate passed **684 tests**, lint/format, strict types,
gold validation and preflight. Focused regressions cover retained unknown
charges and backup bytes, invalid policy rejection, failure recovery,
concurrent raises, real CLI administration, opt-in aggregation, duplicate
rejection, tampered backups, unchanged historical manifests and distinct
deadline profiles. Controlled native initial/correction requests additionally
verify 49,152 context, 16,384 output and thinking=false.

Verified real migration, membership and preparation evidence is exported in
`results/submission/matrix-revised-preparation-20261023/` with checksums.
Every paid invocation still requires separate human approval and cumulative
pre-call reservation. A cap raise is not permission to call a provider.
