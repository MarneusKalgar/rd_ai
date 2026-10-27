# Extract headers and lines in independent native stages

This experiment uses one header stage and one line-item stage over the identical
scoped source representation. Neither stage receives the other's output. Each
request keeps frozen v2 as its prefix and adds only an explicit output-scope
directive; it does not trim rules, crop source, chunk rows or load examples.

Both stage schemas are derived from the authoritative PO schema. The header
projection retains its seven top-level header properties; the line projection
retains `lineItems`, including its existing item fields, formats and constraints.
The original schema and hash stay unchanged. No second handwritten PO model is
introduced. The derived schemas have their own hashes and are retained in evidence.

Each stage uses the shared coordinator and actual complete-request admission.
The coordinators share one availability-stop state for the native dependency.
The same transport retry and bounded schema-correction policy applies per stage.
With the current settings there are twenty primary stage jobs over ten documents,
at most eighty physical requests, 16,384 output tokens per call and a 7,205-second
input deadline per stage. Two primary calls therefore permit 32,768 output tokens;
the stage deadlines sum to 14,410 seconds, plus setup/assembly/persistence overhead.
There is no single shared aggregate deadline. These aggregate ceilings differ
from the one-call baseline and must accompany quality/latency comparisons.

The application composes the two actual outputs only by their disjoint field
ownership, then validates against the unchanged full PO schema. This is planned
composition, not choosing the best fields from competing answers. If either
stage fails, the final PO is unavailable; valid partial evidence remains in the
stage records. No baseline fallback, field repair, semantic correction or Gold
value may fill the failed stage. Gold is read only for offline evaluation.

## Run and inspect

The native-only command requires a complete exported scoped gold10 baseline with
the same plain prompt, model, runtime, context, tokenizer and thinking settings.
Original approved input hashes and exact gold10 membership are checked from
metadata. Generating stage requests does not read Gold answer or annotation files.
The baseline's predictions do not enter either stage prompt.

```sh
HW01_CONTEXT_LENGTH=49152 make hw01-run-split ARGS='--base-run-id gemma-scoped-roles-v2-gold-20261026-732 --run-id gemma-header-lines-gold-20261027-732'
make hw01-export-split ARGS='gemma-header-lines-gold-20261027-732'
make hw01-verify-split ARGS='gemma-header-lines-gold-20261027-732 --source submission'
make hw01-evaluate-split ARGS='gemma-header-lines-gold-20261027-732 --source submission'
```

Use a new run ID for separately authorized experiments; replay/overwrite is
disabled. Execution rejects provider and Docker adapters. The setup client is
application-owned and the adapter is borrowed. Finish experimental sessions with
the recorded driver unload/residency check; the CLI retains ordinary keep-alive.

`results/split/<run-id>/split-run.json` declares stage order, controls, the base
manifest/config/prompt identities and derived schemas. Cases retain both typed
stage records, actual raw responses and assembled outputs; checkpoints retain
admissions, attempts and exact stage jobs before dispatch. Verification re-derives
the schemas, checks request bindings/controls and recomputes assembly without
Gold. Public export scans credentials and hashes every declared payload.

Evaluation scores all ten assembled POs using the existing scorer. A failed
stage gives zero final-PO matches; stage validity, calls and timing remain
separately visible. Header/line accuracy in that report describes assembled PO
fields, not an optimistic score of successful partial stages. Compare extra/missing
rows, exact documents, present/null values, summed processing, per-stage time and
all request/token counts. Gold10 is development data and one pass does not prove
generalization. Historical runs and matrix membership are preserved.

The [measured gold10 report](../reports/gemma-header-lines.md) records the
completed output-scope comparison. It improved headers slightly but worsened
line and overall accuracy; the split is retained as a measured variant rather
than adopted as the default. Completion does not authorize another run.
