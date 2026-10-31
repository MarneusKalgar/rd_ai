# Archive workflow verification — 25 October 2026

The copy-only archive workflow was exercised against the saved final baselines
and a fresh local Garage v2.4.1 bucket. No model inference, provider spending,
source deletion, Git untracking or history rewriting was performed.

## Verified archive

- [Compact index](../../archive-index/7fef8dad92fec7dfb26baf984b906a098de87674517399eebe114d015691708a.json).
- [Verified-upload receipt](../../archive-index/7fef8dad92fec7dfb26baf984b906a098de87674517399eebe114d015691708a.remote.json).
- [Verification summary](../../archive-index/7fef8dad92fec7dfb26baf984b906a098de87674517399eebe114d015691708a.verification.json).

Selection `final-baselines` contains **16 bundles**, including **8 original run
exports**, **311 payload files** and the membership snapshot for **120 covered
observations**. Expanded payload size is **10,484,232 bytes**; the compressed
archive is **1,786,839 bytes**. Other historical experiments are not silently
included in this selection.

Archive SHA-256:
`7fef8dad92fec7dfb26baf984b906a098de87674517399eebe114d015691708a`.
The ignored cache is `results/archives/<sha256>.tar.gz`; the ignored isolated
restore is `results/restored/<sha256>/submission/`.

## Observed behavior

1. Selection checked source manifest/record hashes and complete bundle inventories.
   Packaging completed a temporary restore before publishing its index.
2. The local Garage upload completed and a full GET reproduced the expected
   size and SHA-256. Repeating upload returned `uploaded: false`, reusing the
   existing verified object. The original object was not uploaded over.
3. The download command checked both outer identity and inner evidence before
   publishing a cache copy. Restore installed into its isolated directory.
4. Every original selected payload matched its restored SHA-256.
5. `hw01-evaluate-restored` evaluated both v2 model variants with their disjoint
   gold10/remaining20 sources. The complete resulting evaluation objects equal
   the original saved reports: native **29/30 schema-valid, 198/2,766 gold fields**;
   provider **30/30 schema-valid, 342/342 gold fields**. This checks restoration,
   not a new model run or new accuracy sample.

The final Docker gate passed **767 tests**, Ruff lint/format, strict mypy,
frozen gold validation and corpus preflight. The **35 archive/storage cases**
cover deterministic creation, byte-preserving restore, independently evaluated
restored evidence after fixture originals are removed, historical membership
compatibility, provenance/hash mismatches, links/traversal/duplicate tar entries,
corrupt transfers, upload failures, conflicting-object refusal and private
first-use credentials. S3 contract tests use a stubbed SDK; the separate real
Garage round trip verifies the actual service/SDK integration.

## Retention boundary

Original tracked and untracked evidence remains in place. New indexes and receipts
are reviewable Git metadata; raw evidence has not been added to Git by the workflow.
The original v2 review checkpoint's availability fields describe its earlier
checkpoint state; this report records the subsequent verified local archive.

Garage uses a persistent single-node volume on this machine. This is not an
off-device backup or a reviewer-accessible storage endpoint. Back up separately
before authorizing removal of original evidence. See the
[archival guide](../guides/archiving-results.md) for commands and limitations.
