# Submission evidence retention

On 25 October 2026 the user authorized archival and Git cleanup after a
read-only audit of `hw-01/results/submission/` at the pre-migration revision
`d685f40d0449e386f463330b2c46e982d2eb9124`.

## Retained evidence

The comprehensive [submission-history index](../../archive-index/31349837ab5acff7f512d02ef2ee56a93a7a2da63d01dd8a12ea85acd734288a.json)
lists 42 bulk bundles, including 20 original run exports. It preserves the
earlier smoke/screening runs, interrupted/rate-limited runs, thinking/output-limit
diagnostics, revised v1 baselines and v2 runs with their preparation and detailed
evaluation evidence. Failed attempts and checkpoints are retained unchanged.

The archive was uploaded to the existing Garage bucket and a full GET matched
its size and SHA-256. An isolated restore was compared byte-for-byte with every
original payload. All 563 previously tracked bulk files are covered. See the
[verification record](../../archive-index/31349837ab5acff7f512d02ef2ee56a93a7a2da63d01dd8a12ea85acd734288a.verification.json)
and [retrieval instructions](../guides/archiving-results.md#historical-submission-evidence).
No model inference or gold-label changes were involved.

The five compact files retained under `results/submission/` are:

- `catalog-row-diagnostics-20261024/summary.json`
- `catalog-row-diagnostics-20261024/files.sha256.json`
- `v2-baseline-review-20261025/README.md`
- `v2-baseline-review-20261025/summary.json`
- `v2-baseline-review-20261025/evidence-index.json`

Archive indexes, receipts, the explicit selection, code, frozen prompts/data
and narrative reports remain in Git. Original exports and isolated restores
remain on disk under ignored `results/` paths. The private spending ledger and
policy backups remain separate; combined historical v1 budget-normalized
evaluation needs those original backups as documented in the retrieval guide.

## Git cleanup and recovery

Only the 563 audited bulk file paths are removed from tracking and targeted for
history filtering. Curated snapshots and their previous versions are preserved.
Across locally available branch and remote refs, all historical bulk blob
contents were represented by the current files; the only historical-only blobs
were two earlier versions of the curated v2 README. The audit did not establish
absence of additional evidence in unreachable objects or unknown clones.

Before cleanup, `origin/main` was refreshed and remained
`86fa7366b81c61da52b9bc4d9f685f3c1348143e`; the only published branch was `main`
and no tags were advertised. The local homework branch pointed to
`f22e07876966648b81b62a2777c8200f2c7e6233`. Rewriting occurs in a disposable clone
and is checked before replacing refs. Any publication uses an explicit lease
against the observed remote main, so an intervening update is refused.

The original complete Git history was saved with `git bundle create --all`
and verified using `git bundle verify`. Its local recovery copy is
`hw-01/results/recovery/20261025/before-cleanup.bundle`; rewriting maps and
verification are retained beside it. The bundle contains the original refs
and can be cloned into a separate recovery directory. It is intentionally
ignored and should not be pushed back into the cleaned repository.

Garage's persistent volume, the archive cache, original exports and recovery
bundle are all on this Mac. They provide local recovery, not protection against
loss of the machine. Retain or copy them off-device before pruning recovery
material. Old clones, reflogs and hosting retention may keep old objects after
refs change; a force push does not guarantee immediate physical erasure.

The entire pre-cleanup local Git object store was only 7.96 MiB. This migration
keeps generated experiment payloads out of source history; its logical payload
sizes do not represent guaranteed recovered disk space.
