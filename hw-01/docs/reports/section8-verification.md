# Section 8: saved-evidence consolidation verification

Verified 27 October 2026. The [consolidated report](../../REPORT.md) was assembled
from saved terminal records and existing separately identified diagnostics.
No provider/native inference, new labels, application/scorer change or dependency
update was needed. The provider ledger remained byte-for-byte unchanged.

## Checks performed

- Checked the exact 240-entry model × prompt × sampling × input membership
  against original record/manifest hashes, approved input/schema identities and
  terminal checkpoints. All eight variants contain exactly the approved thirty
  inputs, ten labeled cases and no duplicates/missing gold cases.
- Recomputed the eight variants through the existing shared evaluator, retaining
  failure-inclusive scoring, exact representation and positional line matching.
  The reviewed sampling alias and audited administrative cap revision remain
  explicit; no model controls were normalized away.
- Checked report arithmetic against regenerated data: eight quality rows,
  eight operational rows, eight usage rows and fifteen per-field rows. Thirty
  attempted inputs/latency samples and zero corrections/retries/unknown costs
  were verified for each matrix variant. The four native truncations remain.
- Checked every selected bundle inventory and archived the full provenance union:
  **84 bundles, 1,594 payload files**, compressed size **15,353,160 bytes**.
- Uploaded to local Garage and verified a complete GET, then independently
  restored the archive. Every restored payload matched its original bytes.
  Recomputed `evaluation.json`, `summary.json` and `errors.json` from the isolated
  restored sources; each matched exactly. Rechecked the report tables and
  archived report snapshot after recomputation.

The existing implementation gate was **927 passing tests**, Ruff lint/format,
strict mypy over 203 source files, frozen gold validation and offline preflight.
It preceded these documentation/archival changes; it was not rerun as though
section 8 introduced application code. Section 8's new checks are the saved-data
recomputation, report arithmetic, inventory and restored reproduction above.

## Evidence and reproduction

Archive SHA-256:
`c3398a3c846488086ef52be9a4706b0eb9568ab94f56f42d3190610d96ad263b`.

- [Compact archive index](../../archive-index/c3398a3c846488086ef52be9a4706b0eb9568ab94f56f42d3190610d96ad263b.json).
- [Garage upload and full-download receipt](../../archive-index/c3398a3c846488086ef52be9a4706b0eb9568ab94f56f42d3190610d96ad263b.remote.json).
- [Restore and recomputation verification](../../archive-index/c3398a3c846488086ef52be9a4706b0eb9568ab94f56f42d3190610d96ad263b.verification.json).
- [Explicit bundle selection](../../archive-index/selections/section8-consolidated.json).

Follow the [retrieval guide](../guides/archiving-results.md) to fetch the archive
when its ignored cache is absent. From the repository root, restore it once:

```sh
make hw01-restore-results ARGS='--index archive-index/c3398a3c846488086ef52be9a4706b0eb9568ab94f56f42d3190610d96ad263b.json'
```

The restored `submission/section8-consolidated-20261027/` contains the collection,
report-check and restore-verification drivers, report snapshot, source-report
snapshots, full evaluation, compact summary, exact error examples and membership.
With the existing audited results volume, run verification entirely in Docker:

```sh
docker compose --env-file hw-01/.env.compose -f hw-01/compose.yaml run --rm --no-deps \
  --volume "${PWD}:/workspace" \
  --volume "${PWD}/hw-01/results/restored/c3398a3c846488086ef52be9a4706b0eb9568ab94f56f42d3190610d96ad263b/submission:/app/results/submission" \
  offline python /app/results/submission/section8-consolidated-20261027/restore-verification-driver.py
```

Use `.env.compose.example` instead if the local Compose controls file is absent.
There are no model dependencies or provider credentials on this offline service.
Verification rewrites deterministic files in the isolated restore and its compact
verification receipt; it does not overwrite original runs or the ledger.

## Boundaries and section 9 follow-up

This is a verified workspace/archive reproduction, not yet a completed clean-room
checkout exercise. The combined historical $4.50/$10 evaluation calls the shared
evaluator's audited-budget revision path, which reads the local ledger and its
revision backup. Neither private file is uploaded. Section 9 should establish
how a fresh reviewer reproduces the public comparison without the original
machine's private accounting state, while retaining original policy provenance.
It must not fabricate a spending ledger or silently merge arbitrary policies.

Garage, caches and repository are on the same laptop. Their checks demonstrate
payload integrity and local recovery, not off-device disaster recovery.
The twenty unlabeled inputs remain unlabeled. No generalization claims, new
provider/local runs or deferred 7.3 experiments follow from this verification.
