# Bounded buyer identifier correction

This optional native-only experiment reuses one complete saved gold10 run as
its fixed primary outputs. It makes no new primary calls and never reads gold
answers or annotations during correction. It is separate from the required
matrix and from semantic acceptance of an entire PO.

For each starting output, the existing source-role checker identifies uniquely
matched buyer identifier contradictions. Unsupported/ambiguous evidence is an
abstention. No contradiction means no request. A contradiction permits exactly
one new request for that input, with no transport retry, schema retry or second
semantic correction. Provider and Docker inference are rejected.

The model receives the full unchanged source representation, frozen base
instructions, the previous complete PO and source-derived identifier findings.
It must return the complete PO using the same authoritative schema. The workflow
retains the actual returned object only if it is complete/schema-valid, resolves
every targeted identifier and changes no other field or row. Legitimate
identifiers and all dates, quantities, prices, names and row order are protected.
Comparison masking is used only to detect off-target edits; fields are never
merged into a repaired output.

On an invalid/incomplete response, timeout, admission failure, unresolved target
or off-target edit, the previous output is retained **for review**. It is not
certified correct. The candidate and failure remain available; no best-scoring
candidate or gold judgment participates in this decision. The checker supplies
the source-role resolutions, so resulting gains describe the source-guided
pipeline rather than independent model understanding of identifier ownership.

## Commands

Use a new run ID; automatic replay and overwrite are disabled. From the repository
root, with the reviewed scoped gold10 baseline exported/restored:

```sh
HW01_CONTEXT_LENGTH=49152 make hw01-correct-identifiers ARGS='--base-run-id gemma-scoped-roles-v2-gold-20261026-732 --run-id buyer-id-correction-20261026-732'
make hw01-export-correction ARGS='buyer-id-correction-20261026-732'
make hw01-verify-correction ARGS='buyer-id-correction-20261026-732 --source submission'
make hw01-evaluate-correction ARGS='buyer-id-correction-20261026-732 --source submission'
```

Only `evaluate` reads gold values. Verification recomputes source findings,
request/schema/admission bindings, candidate parsing, edit guards, selection and
retained values. It requires the original baseline bundle beside the correction
evidence. Public export includes exact byte hashes and credential checks.

The application owns native clients and their lifetime. The correction component
borrows an adapter and admission service. Finish experimental sessions with the
native unload/residency verification recorded by the experiment driver; the run
command itself retains the normal native keep-alive behavior.

## Evidence and timing

Evidence lives in `results/corrections/<run-id>` and public exports use
`results/submission/<run-id>`. `correction-run.json` distinguishes this evidence
bundle from ordinary extraction manifests. Per-case records preserve the
starting record hash, original source, instructions, actual request/admission,
raw response/failure, candidate, guard decision and retained output. Request
intents are checkpointed before dispatch. Original runs and budget accounting
remain unchanged.

Reports distinguish reused primary calls from newly executed correction calls.
The correction phase is measured now; adding its processing time to saved
primary time is a **reconstructed total**, not measured live end-to-end latency.
Quality includes every retained gold10 output, including rejected/no-call cases;
retained availability is not automatic semantic acceptance. Hardware/electricity
costs remain unmeasured even when native API cost is zero.

The [gold10 experiment report](../reports/identifier-correction.md) records the
completed replay, including rejected candidates and verified archival. Completion
does not authorize replaying it or extending the correction policy.
