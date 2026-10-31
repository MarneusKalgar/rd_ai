# P00-S08 — Runtime naming migration

Completed 2026-10-31, following the explicitly requested remainder of S08.
Source baseline: `dc6b5ed`. No inference, model download, provider spend, new
labels, bucket migration, volume recreation or Git publication was performed.

## Dispositions

| Surface | Implemented disposition |
| --- | --- |
| Package metadata | `hw01-structured-extraction` → `document-intelligence`; pinned uv regenerated `uv.lock` inside Docker. Parsed lock/project comparison confirmed no dependency, version, artifact hash or tool configuration drift. |
| Environment contracts | Atomic `HW01_*` → `DI_*` across app/setup/archive loaders, Compose substitution, generators, current examples/instructions, tests and all three existing private settings files. Values and file owners/modes were verified unchanged. `OPENROUTER_API_KEY`, `GARAGE_*` and server `OLLAMA_*` remain unchanged. |
| Stale settings | All three Python settings loaders reject retired process/dotenv names, including old/new conflicts, without printing values. Make rejects old shell/CLI overrides and old names in its selected Compose controls file. |
| Disposable resources | Compose project `rd-ai`; generated containers/images/network use the new name. Garage is healthy as `rd-ai-garage-1`. The old Garage container is stopped and retained for rollback. |
| Persistent volumes | Explicit external names retain `rd-ai-hw01_results`, `rd-ai-hw01_garage-data` and the optional Docker model volume identity. Missing external storage fails rather than initializing a replacement. No data-copy cutover. |
| Bucket and archive identities | Retain `hw01-evidence`, its credentials, object keys and `hw01-archive-*-v1` readers/writers. Renaming these has no operational benefit sufficient to justify moving/rekeying evidence. |
| Python imports and historical evidence | Retain `extraction_service`, original run IDs, historical observations/commands and all existing index/receipt/payload bytes. |

## Verification

- Before stopping the old Garage instance, recorded its actual project/resource
  mapping. After stopping it, captured recoverable tar copies of both volumes,
  inventories of hashes/owners/modes and the original private settings under
  ignored `results/recovery/S08-20261031/`.
- Before cutover, **1,684 results entries** and **268 Garage entries** matched
  the checkpoint exactly, including ownership/modes. All **132 frozen/public
  data, prompt, schema and existing archive-index files** matched source baseline.
- `make check`: **956 tests passed in 308.37s**, Ruff lint/format, strict mypy
  on 208 source files, frozen gold validation and offline preflight passed.
  The 18 new cases exercise process/dotenv loading for all three settings
  families, old-only rejection and conflicting old/new rejection without values.
- Both native/provider command dry runs preserve service selection and approval
  flags. Old command-line controls and the actual old Compose controls copy
  fail before execution. No native or provider command was executed.
- Through the renamed project's default UID 10001 container, all original
  results/accounting bytes, paths and owners/modes still match. The checkpoint
  comparator rejects empty/different inventories. These are migration controls,
  not a permanent monitor for arbitrary future manual Compose edits.
- A separate Compose negative control reports the intended error, external
  volume not found; its application process never starts.
- `make download-archive` retrieved the existing section 8 archive through the
  migrated DI credentials and new Garage service, with full byte/hash validation.
  The existing reader restored it into fresh `/tmp/s08-isolated-restore/`.
- `make reproduce-report`: **240 observations, eight variants, 84 bundles,
  1,594 payload files**; regenerated evaluation/report tables match, without
  private ledger or inference. Prior P00 proof and original indexes remain intact.

## Evidence and limits

Public execution logs and preservation outcomes are collected under ignored
`results/submission/S08-runtime-naming-20261031/`, with compact archive references
recorded below. Membership in that bundle is copied from the saved 240-observation
matrix solely to bind inherited evidence; it does not claim new inference.
Private settings, ledger inventories and volume backups are excluded from the
public bundle. Recovery copies remain on this laptop, not off-device.

The [migration guide](../guides/runtime-name-migration.md) documents the atomic
settings compatibility break, retained resources, first-install limitation and
rollback. Current Docker Ollama storage was absent before this slice and was
not recreated. Direct Compose calls bypass Make's controls-file guard; current
operating instructions use Make. Original archive v1 identifiers are retained
deliberately, not an unfinished namespace-wide replacement.

All S08 groups now have an implemented or retained disposition. No persistent
bucket/data/format rename remains selected for execution.

Public proof archive:
[`dade2a33…`](../../archive-index/dade2a336183f53ea7a552c491ef5064ce1527b41135930192a00183f549700a.json),
with [verified remote receipt](../../archive-index/dade2a336183f53ea7a552c491ef5064ce1527b41135930192a00183f549700a.remote.json).
The 14-bundle archive passed local verification and Garage upload/full-GET
verification. Existing public indexes and original proof archives were not replaced.
