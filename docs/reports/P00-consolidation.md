# P00 — Root consolidation verification

Completed 2026-10-31 against base `654be96`, preserving the previously uncommitted
roadmap/navigation changes. No commit, push, model initialization or inference ran.

The Python application, approved public data, schemas, prompts, configuration,
dependency files, Docker definition, report and archive metadata now live at the
repository root. Application docs were merged into root `docs/`; its coding and
review governance was preserved. The prior application README is retained as a
historical reference. `AGENTS.md` describes one R&D application; `CLAUDE.md` keeps
its original relative symlink. `hw-01/` is no longer an application directory.

## Verification

| Gate | Result |
| --- | --- |
| Recoverable checkpoint | Public tracked source and explicit roadmap candidate saved before the move; private inputs/settings excluded from rehearsal |
| Frozen artifacts | 359 original implementation/data/configuration/dependency/archive files matched exactly in the candidate and after application; the subsequent P00 archive-selection entry is the sole deliberate addition to archive routing metadata |
| Full offline gate | 938 tests passed in 300.57s, Ruff lint/format, strict mypy over 206 source files, gold validation and preflight |
| Isolated reproduction | Eight variants / 240 observations reproduced from the supplied public archive without private settings, ledger or prior restores |
| Root reproduction | Repeated successfully after applying the migration and rehoming the original results cache |
| Negative control | Real CLI rejected a copied report changing Flash v2 baseline accuracy from 100% to 99%, with exit 2 |
| Docker exclusions | Inert `data/private/` and raw-results canaries absent from the application image; Git internals absent |
| Compatibility | `hw01-*` aliases share root recipes; native/provider dry runs select the original services and add no provider permission |
| Private data | Existing root `data/private/` untouched; no canary or private source copied into public data |
| Persistent storage | Same `rd-ai-hw01_results` and `rd-ai-hw01_garage-data` volumes; same project, settings names, archive keys and UID expectations |
| Ledger | SHA-256 remains `0b32995521b2fa0b6c2dae43187ac49d65dbd740bbe9c08447edc963b9554bf4`; no reset or new spending |
| History | Original run/manifest/checkpoint/archive bytes retained; live documentation links/working-directory instructions repaired |

The single full gate ran on the isolated migrated root candidate. Application,
tests and frozen artifacts were then copied byte-for-byte; the same full suite
was not redundantly rerun on the working tree. Docker's existing engine/cache
and host were reused. This was an isolated filesystem rehearsal, not a freshly
provisioned machine or new live-model availability test.

## Commands and storage

Use `make check`, `make preflight`, `make reproduce-report` and
`make verify-archive` from the root. Existing `make hw01-*` aliases still work.
Old `cd hw-01` directions in historical records describe their original context;
no blanket directory symlink was introduced. Environment names, package name,
namespace and pinned images remain unchanged.

Ignored results and operator settings were physically relocated, preserving
contents/permissions. The obsolete ignored Ruff cache was retained outside the
repository with the migration checkpoint. Named volumes and Garage data were
neither recreated nor pruned. Private ledger contents are not published.

Migration proof, original frozen-file inventory, commands and logs are retained
under ignored `results/submission/P00-consolidation-20261031/`, selected by
`P00-consolidation`. Compact archive/upload/restore records are retained under
`archive-index/`. The source report still reproduces from its original pinned
section 8 archive; the migration proof does not rewrite that archive identity.

## Disposition and limits

P00 is concluded for repository consolidation. Its AI Engineer and OWASP topic
exercises are limited to inherited evaluation/identity preservation, offline
resource boundaries and private-material exclusion. This is not a new claim of
prompt-injection, tool-agency or generalization robustness. No labels, source
semantics, model outcomes or deferred local experiments changed.

The ten gold cases remain development data. Garage and caches on this laptop
remain single-machine storage. Existing unknown billing holds remain unresolved.
P01 and later model-dependent work require their own selected scope and approval;
no next experiment is automatically started.

Proof archive: [index](../../archive-index/452342d818f7539c24da7b1a01bd560496cbdb4df36c02a280ea75d336e16b77.json),
[Garage receipt](../../archive-index/452342d818f7539c24da7b1a01bd560496cbdb4df36c02a280ea75d336e16b77.remote.json),
[restore verification](../../archive-index/452342d818f7539c24da7b1a01bd560496cbdb4df36c02a280ea75d336e16b77.verification.json).
All 528 payload files across 14 bundles matched after restoration.
