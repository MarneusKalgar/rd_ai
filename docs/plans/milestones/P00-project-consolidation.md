# P00 — Project consolidation implementation plan

- Version: **1.4**.
- Created: **2026-10-31**.
- Status: S01–S08 concluded 2026-10-31; persistent and archive identities explicitly retained.
- Parent: [document-intelligence roadmap](../../roadmap.md#p00--project-consolidation-and-preserved-baseline).
- Completed consolidation evidence: [original execution record](../../reports/P00-consolidation.md).

## 1. Outcome and inherited work

Make `rd_ai` the root of one document-intelligence R&D application while
preserving existing behavior, data authority, accounting and evidence recovery.
This is a repository/governance migration, not a new extraction experiment.

The original root migration is complete. The additional **P00-S08** responds to
the later legacy-name review: remove unnecessary command/documentation names,
and assess runtime/storage names before any coordinated migration. The selected
low-risk cleanup has since retired aliases and repaired current instructions.
The follow-up requested on 2026-10-31 selects an atomic DI environment contract,
package metadata rename and disposable Compose project rename. Existing volume,
bucket and archive-format identities are retained. Original S01–S07 observations
and acceptance remain historical and valid.

Inherited evidence already exists:

- The historical matrix is **240/240**, including attempted failures: eight
  variants, thirty inputs each and ten development-gold cases per variant.
- The [consolidated report](../../../REPORT.md) and
  [sections 8–9 verification](../../reports/section9-verification.md)
  contain quality, row errors, time, cost and ledger-free reproduction.
- The recorded implementation gate is **938 tests**, Ruff lint/format, strict
  mypy, frozen gold validation and preflight at baseline `654be96`.
- Source support, examples, Qwen, sampling and split-stage experiments have
  concluded decisions. JEV/routing and further variants remain deferred.

Do not recreate these as new research deliverables. P00 checks that they still
reproduce after the physical move and that documentation describes their actual
status. Independent labels/new documents are not a P00 prerequisite.

## 2. Scope, exclusions and target

In scope: root guidance/navigation, the canonical roadmap, application/public
artifact locations, Docker context/Compose paths, Make routes, documentation and
test-fixture path references, ignored runtime paths and migration verification.

Excluded: model/prompt/schema/input/gold changes; new features, providers or
models; new dependencies or Python namespace renames; application architecture
refactoring; inference, capacity probes, downloads of models or paid calls;
Git-history rewriting; changes to AspectLoop; automatic commits or pushes.

S08 extends scope to coordinated legacy naming cleanup. Package metadata,
environment contracts and persistent-resource naming may change only through
the explicitly selected, tested migration paths in that slice. The follow-up selects DI_* settings, document-intelligence package metadata and
rd-ai Compose naming; persistent-data and archive-format renames are explicitly
not selected. An assessment may conclude retain or defer for those identities.

Proposed target layout:

```text
rd_ai/
├── src/extraction_service/
├── tests/
├── config/
├── prompts/
├── schemas/
├── data/                       # approved public data plus existing ignored private subtree
├── docs/
│   ├── roadmap.md
│   ├── plans/milestones/
│   ├── guides/
│   ├── reference/
│   ├── reports/
│   └── quality/
├── archive-index/
├── results/                    # ignored; original relative evidence paths retained
├── pyproject.toml
├── uv.lock
├── Dockerfile
├── .dockerignore
├── compose.yaml
├── Makefile
├── README.md
├── REPORT.md
├── AGENTS.md
└── CLAUDE.md -> AGENTS.md
```

Keep `docs/coding-conventions.md`, `docs/review-process.md`, the versioned review
skill and private one-off preparation boundaries. Merge the application docs
into these existing root docs; do not overwrite root governance. Do not create
empty packages for future milestones. The repository directory/name and Git
remote do not need to change.

## 3. Invariants and compatibility contract

| Surface | Required invariant |
| --- | --- |
| Data and contract | Exact approved input/gold/schema/prompt bytes and their manifest identities; no new approval or label claims |
| Historical evidence | Original run IDs, record/manifest/checkpoint bytes, archive SHA-256 values, membership and frozen policy/sampling-alias records |
| Archive storage | Existing bucket/object keys, including the validated `hw01/archives/sha256/…` namespace, and compact upload/restore receipts |
| Persistent resources | Compose project `rd-ai-hw01`, actual named results/ledger and Garage volumes, and non-root ownership; preserve identities explicitly |
| Accounting | Existing ledger/revision backup bytes and unresolved holds; never initialize an empty replacement ledger or reset opening spend |
| Runtime interface | Python namespace `extraction_service`, current CLI semantics, environment variable names and provider/native selection |
| Dependencies | Existing project metadata/name, pinned images and locked dependency bytes; metadata renaming is a separate future change |
| Commands | Canonical root commands and compatible `hw01-*` root aliases share one implementation; no added provider permission flags or implicit generation |
| Private material | Root `data/private/`, `.agents/` private inputs, ignored preparation tools/settings and archive credentials remain excluded from Git/images/public evidence |

These were the S01–S07 preservation rules. S08 may retire command aliases and
revise current descriptions. Any selected runtime/resource rename must preserve
data, accounting, permissions and old-evidence readability through an explicit
migration; it cannot be implemented by replacing every matching string.

Physical relocation changes the application base directory; serialized paths
such as `results/runs/…` and `results/submission/…` remain application-relative.
The name `submission` inside the legacy artifact format is retained. Archived
snapshots keep their original paths/commands as historical evidence. Current
guides receive a migration mapping rather than edits to archived bytes.

Do not create a blanket `hw-01 -> .` compatibility symlink: archive confinement
rejects symlinked evidence paths. Compatibility covers root Make aliases; old
explicit `cd hw-01` working-directory instructions receive documented root
equivalents. Preserve the existing relative `CLAUDE.md` guidance symlink.

## 4. Ordered implementation slices

Complete slices in order. Record each slice's actual result/evidence here or in
its linked migration report; planned acceptance is not a passed gate.

### P00-S01 — Inventory, checkpoint and baseline verification

1. Record the base commit, working-tree scope and candidate snapshot. Preserve
   unrelated changes. Use a disposable tracked-source export for rehearsal;
   excluded private material is never copied into it.
2. Inventory tracked/public locations, root collisions and ignored runtime
   storage. The root already contains `data/private/`; an application-directory
   move must not replace, copy into images, or relabel that private subtree.
3. Record real Compose project/volume identities, mount paths and ownership.
   Retain private ledger/revision-backup digests and selected accounting totals
   in ignored local evidence; never publish ledger contents or credentials.
4. Verify availability of the indexed section 8 public archive
   `c3398a3c846488086ef52be9a4706b0eb9568ab94f56f42d3190610d96ad263b`.
   Reuse the documented retrieval workflow if needed. Missing evidence keeps
   reproduction acceptance open; it does not authorize new inference.
5. Run the current baseline's offline reproduction/checks once if no matching
   verified source baseline is available. Retain results and failures.

**Accept S01:** a collision/storage inventory, recoverable file-move checkpoint
and exact baseline identities exist. No private data was promoted, storage was
recreated or model initialized. Commands below identify pre-migration behavior.

### P00-S02 — Align project authority and completion records

1. Update root `README.md`, `AGENTS.md` and coding/review guidance to describe
   one R&D application, using this roadmap as planning authority.
2. Identify inherited matrix/sections 8–9 work as concluded and keep local-trial
   decisions. Do not turn the old 120-observation description into a backlog.
3. Make `docs/README.md` a project documentation index using the existing guides,
   reference, plans, reports and quality groups. Preserve source/report dates.
4. Document live-inference permissions and native Ollama/Docker verification
   boundaries; retain private preparation and AspectLoop separation.

**Accept S02:** one current-state description and navigation path; no dependence
on ignored working specs; existing safeguards survive the wording change.
The roadmap and P00 plan created before execution are reused, not regenerated
as a new milestone accomplishment.

### P00-S03 — Move tracked application/public artifacts to the root

1. Move `src`, `tests`, `config`, `prompts`, `schemas`, approved public `data`,
   `pyproject.toml`, `uv.lock`, Docker files, environment examples, `REPORT.md`
   and `archive-index` from `hw-01/` into the root candidate.
2. Merge approved public data into root `data/` with an explicit file inventory.
   Leave `data/private/` and original workbooks untouched. Resolve differing
   existing destinations before replacing anything; do not pick by timestamp.
3. Merge documentation into root `docs/`, preserving its established grouping
   and the root coding/review documents. Update live relative links and fixture
   paths without rewriting archived reports/manifests or local historical inputs.
4. Keep the package name/namespace and dependency lock unchanged. Only genuine
   path references may change; no simultaneous module or dependency refactor.

**Accept S03:** every moved public artifact is present at its intended location;
frozen/dependency/archive bytes match the S01 inventory. A filesystem mapping
explains relocations. No source-schema drift or newly exposed private file.

### P00-S04 — Consolidate Make/Docker execution and isolation

1. Merge root dispatch and application targets into one authoritative root
   Makefile. Keep a safe help/default route and documented generic commands.
2. Add compatible `hw01-*` aliases that call those same targets and preserve
   `ARGS`, `MODE` and Compose-control overrides. Avoid duplicate recipes,
   recursive alias loops and changed error/exit behavior.
3. Keep Compose's explicit project/resource names and native default. Update
   build/bind/env-file paths for the new working directory. Offline/reproduction
   services retain no network, model dependencies or credential environment
   files; reproduction still has no named results volume.
4. Carry the explicit Docker context allowlist to the root. Verify private
   subtrees, ignored settings/tools, Git internals, raw results, archives and
   model weights cannot enter the image. Use inert canaries in a disposable
   export; do not test this with real credentials or workbooks.
5. Check the selected resource/volume mapping without starting Ollama, running
   setup/capacity probes or invoking generation. Keep existing UID/ownership
   expectations and pinned image references.

**Accept S04:** generic/legacy commands resolve to identical selected actions;
CLI/settings behavior and isolation are preserved. No image/weights download,
new provider grant or accidentally empty named volume is introduced. Native and
provider run commands are inspected with dry runs only.

### P00-S05 — Rehome ignored storage and private settings safely

1. Rehome host-side results caches/restores/exports/reproduction receipts and
   Garage configuration to the documented root paths, preserving original
   application-relative evidence paths and byte hashes. Use verified per-bundle
   merging if root destinations already exist; never overwrite differing data.
2. Keep the named volume holding original runs/accounting and the Garage data
   volume unchanged. Moving a bind-mount path must not silently regenerate
   Garage settings, storage identity or credentials.
3. Relocate operator settings only if needed and only within ignored paths.
   Preserve permissions; compare safely without printing values. Committed
   examples remain harmless. Report unresolved collisions rather than guessing.
4. Verify root ignore rules keep bulk/runtime/private material excluded while
   preserving the narrowly reviewed compact snapshots and archive metadata.
5. Retain a recoverable original or verified temporary copy until acceptance;
   remove duplicate obsolete paths only after preservation checks pass.

**Accept S05:** existing artifacts and the same private ledger/storage resources
are reachable at the new location, with unchanged identity/accounting. No source
evidence is deleted to make the new paths appear clean. No `down -v`, volume
pruning, archive rekeying, budget initialization or history rewriting is used.

### P00-S06 — Verify behavior and evidence at the new root

1. Run one full Docker implementation gate from the migrated candidate. Inspect
   any changed test population; the recorded 938 count is evidence, not an excuse
   to delete tests or a hard-coded future count requirement.
2. Run ledger-free reproduction using the same indexed public archive and
   public manifest-bound policy. Require exact regenerated evaluation and
   unchanged required matrix membership/metrics: 240 observations/eight variants.
3. Repeat the existing deliberately changed-report rejection through the real
   reproduction entrypoint. Retain the intended failure reason and nonzero exit.
4. Verify archive integrity/restoration and migrated relative-path behavior;
   use a separate restore destination or the existing verifier's refusal rules.
   Never overwrite originals to hide a mismatch.
5. Check alias resolution, help, provider/native dry runs, documentation links,
   Docker canary exclusions, ignore rules, and ledger/resource digests against S01.

**Accept S06:** full checks and positive/negative reproduction pass; original
failures/row errors/accounting remain intact; aliases and isolation work. This
gate requires no live runtime, current provider metadata or new inference.

### P00-S07 — Isolated export, evidence and milestone decision

1. Export only tracked/candidate public source plus the supplied public archive.
   Exclude private environment files, ledger/backups, original results, preexisting
   restores and workbooks; preserve legitimate tracked guidance symlinks.
2. Execute the documented root reproduction command and implementation gate.
   Record whether Docker caches/host were reused; do not call this a freshly
   provisioned machine test if only the filesystem export was isolated.
3. Retain migration inventory, commands, test/reproduction outcomes, negative
   controls and resource/hash comparisons in ignored public evidence bundles.
   Use the archive workflow and compact indexes/receipts for versioned references.
4. Write a migration report and update the roadmap's P00 status only after all
   gates pass. Record remaining compatibility limits and the next selected slice.
5. Leave stage/commit/push decisions explicit. This implementation plan does not
   request Git publication or automatically open P01/P02 model experiments.

**Accept S07:** an independently inspectable migration record links reproducible
evidence and a scoped completion decision, with no new billing or label claims.

### P00-S08 — Legacy-name cleanup and risk-gated migration review

**Status: selected runtime migration and retained-name review concluded.**
See the original [cleanup record](../../reports/legacy-name-cleanup.md) and the
[runtime migration record](../../reports/runtime-name-migration.md). The subsequent
request selects `DI_*`, `document-intelligence` and Compose project `rd-ai`.
External volumes retain their actual names; bucket, object keys and archive v1
formats are retained. Execute only selected naming changes. The default
disposition for unselected runtime/storage changes is retained or deferred,
with the reason recorded. Do not turn removal of Make aliases into an implicit
archive-format, storage or credential migration.

1. **Inventory and classify references.** Record each owning surface, consumers,
   target name if a rename is selected, risk and rollback. Separate current
   operating instructions from dated observations, serialized identifiers and
   immutable evidence. Check whether source bytes contribute to algorithm or
   artifact fingerprints before treating a source-text edit as cosmetic.

   | Surface | Disposition / risk control |
   | --- | --- |
   | Make aliases, `.PHONY` entries and compatibility help | Low-risk cleanup: canonical targets already exist; remove alias routing without changing canonical recipes or execution permissions. |
   | Current README/AGENTS, guides/reference, quality guidance and report reproduction instructions | Replace current command examples with canonical targets; preserve dated execution observations and original archived commands. |
   | Generic headings/docstrings, scratch-directory prefixes and synthetic test bucket names | Rename where they are descriptive/disposable; verify no identity calculation or fixture contract depends on their bytes. |
   | `hw01-structured-extraction` package metadata | Selected: rename to `document-intelligence`; update metadata and let uv regenerate the lockfile inside Docker; dependency versions must not drift. Keep the Python namespace unchanged. |
   | `HW01_`, `HW01_SETUP_`, `HW01_ARCHIVE_` | Selected atomic `DI_*` migration across settings, Compose, generators, local files, examples and tests; avoid ignored overrides and fallback to defaults. |
   | Compose project and generated container/image/network names | Selected `rd-ai` project with original explicit external volume names; missing storage must fail, not initialize an empty replacement. |
   | Named results/Garage volumes and real bucket `hw01-evidence` | Retain exact identities: no data-copy cutover or bucket rename. Capture recoverable copies and verify original contents, permissions and ledger identity. |
   | `hw01-archive-*-v1`, object keys, indexes, receipts and archived payloads | Preserve existing evidence; any future writer format/namespace change needs versioned compatibility and a separate decision. |

2. **Perform the selected low-risk cleanup as one bounded change.** Retire the
   `hw01-*` Make aliases and their current compatibility claims, retaining all
   canonical targets, flags and safe defaults. Update current instructions and
   examples, including the stale `hw-01` dependency-build context/bind mount,
   old working-directory directions and malformed empty-directory wording in
   the Docker guide. Preserve historical report commands, P00's original alias
   verification and archived snapshots as observations of what actually ran.
   Add a dated follow-up instead of rewriting those observations. Check new
   scratch/test labels with focused tests where relevant; no new feature work.

3. **Assess environment/package renames separately.** If selected, choose the
   target names once and specify either a tested dual-name transition or an
   atomic migration of all consumers/private overrides. Reject conflicting old
   and new settings without exposing values. Exercise every affected loader,
   Compose substitution and generated settings file; never regenerate existing
   storage credentials merely to rename their variables. A package rename uses
   uv in Docker, with a lockfile diff limited to intended project metadata.
   If not selected, retain the old names explicitly rather than reporting the
   namespace fully removed.

4. **Review persistent-resource risk before changing any names.** Capture actual
   volume, mount, ownership, bucket/key and safe accounting fingerprints and a
   recoverable rollback copy. A renamed Compose project must explicitly reuse
   the original volumes, or use a verified copy-and-switch migration; a newly
   empty volume is a failed gate. A real bucket move needs verified objects,
   permissions, consumer configuration and successful restore before cutover.
   Preserve old locations until verification succeeds. If the change has no
   practical benefit, record retain/defer; no reset, pruning or `down -v`.

5. **Preserve historical format compatibility.** Existing indexes, receipts,
   manifests, logs, archive objects and P00 proof retain their original bytes,
   version strings and locations. Keep old readers/validation paths working.
   A selected new format or key namespace applies to future writes through a
   versioned design, with both old and new fixtures and an explicit lookup
   policy. Never weaken checksum/key checks or rewrite old evidence to make
   a global naming replacement pass. The default is to retain v1 identifiers.

6. **Verify proportionately without model calls.** For alias/documentation
   cleanup, check canonical Make help/dry runs, selected CLI behavior, current
   links and remaining-match classification. If Python settings, dependency
   metadata, archive readers or storage behavior change, run the affected tests
   and appropriate full gate; reproduce/restore the existing pinned archive
   whenever those paths are affected. Controlled tests must detect conflicting
   settings, wrong/empty resources and incompatible old formats. Verify ledger
   and stored-object identity/permission preservation for selected migrations.
   Do not rerun the full suite solely for wording or harmless scratch labels.

7. **Record the disposition and rollback.** Publish a scoped follow-up with
   removed, migrated, retained and deferred groups, actual commands/checks,
   compatibility breaks and residual risks. Reuse the archive workflow for any
   new proof without replacing S01–S07 evidence. Retire aliases only in current
   instructions; their presence in historical records remains legitimate.
   No provider/native inference, model downloads or Git publication is implied.

**Accept S08:** selected low-risk cleanup is complete; current commands and
instructions work; every remaining legacy-name group has an explicit disposition.
Any selected environment/package/resource migration has independent preservation,
compatibility and rollback evidence. Unselected sensitive changes remain named
and deferred. Original ledger, frozen outcomes and archived evidence are intact;
no silent default fallback, empty storage substitution or history rewrite occurs.

## 5. Verification commands and expected outcomes

Run these through Make/Docker. The first table retains pre-migration commands; generic root
commands in the second table are now implemented and verified.
The actual migration report records exact invocations and artifact locations.
Alias checks below describe the completed S01–S07 migration. S08 supersedes the
alias-retention requirement only after its selected cleanup is implemented;
retain these original checks as historical evidence. Its verification uses the
canonical commands and the conditional checks specified in S08.6.

| Before migration, repository root | Expected result |
| --- | --- |
| `git status --short` and `git diff --check` | Scope recorded; no unrelated changes consumed |
| `make hw01-check` | Current full offline gate and frozen data validation; no model calls |
| `make hw01-reproduce-report` | Indexed saved matrix and report tables reproduce without private ledger/credentials |
| `make hw01-verify-archive ARGS='--index archive-index/c3398a3c846488086ef52be9a4706b0eb9568ab94f56f42d3190610d96ad263b.json'` | Public evidence bytes and inventories verify |

| After migration, repository root | Expected result |
| --- | --- |
| `make help` | Canonical commands, compatibility aliases and non-inference defaults documented |
| `make check` | Ruff lint/format, strict mypy, pytest, gold validation and preflight pass |
| `make reproduce-report` | Same 240-observation evaluation and numerical report tables, without private ledger/model |
| `make verify-archive ARGS='--index archive-index/c3398a3c846488086ef52be9a4706b0eb9568ab94f56f42d3190610d96ad263b.json'` | Same archive identity and verified contents |
| `make -n hw01-check` and `make -n hw01-reproduce-report` | Resolve to their canonical targets; no second implementation or recursive loop |
| `make -n run MODE=native ARGS='--help'` and `make -n run MODE=provider ARGS='--help'` | Correct service/flags; no execution, Docker Ollama startup or automatic provider grant |
| `git diff --check` | No whitespace errors; review actual moves/edits separately |

Use Docker scripts/helpers for hashes, JSON comparison, source exports and bulk
file operations. Do not add tests that mirror comments, folder spelling or static
configuration. Add focused regression tests only for changed behavioral risks
such as base-path resolution, isolation or compatibility dispatch. Once the
appropriate checks pass, avoid redundant unchanged full-suite reruns.

## 6. Topic mapping and required evidence

Source editions/revision and coverage semantics are defined in the
[roadmap](../../roadmap.md#4-sources-and-meaning-of-topic-coverage).

| AI Engineer topics | P00 slices | Evidence / qualification |
| --- | --- | --- |
| Choosing the Right Model; Impact on Product Development; Roles and Responsibilities | S01–S02 | Reuse inherited findings to define project scope; no new model experiment |
| LLM Evaluations; Deterministic Evals; Evaluation Metrics; Regression Testing | S01, S06–S07 | Exact saved-record reproduction and a real rejected changed-report control |
| Cost/latency monitoring | S01, S05–S07 | Preserved historical populations/accounting and unchanged private ledger identity |
| Security and Privacy Concerns; Constraining outputs and inputs | S03–S07 | Build-context canaries, private exclusions and model-free verification |

Planned S08 extends regression/identity and private-setting preservation checks
for the selected naming changes; it claims no new live-model topic coverage.

| OWASP 2025 topic | P00 slices | Evidence / limit |
| --- | --- | --- |
| LLM02 Sensitive Information Disclosure | S01, S03–S05, S07 | Private/material exclusion with inert canaries and scoped fixture triage; no broad disclosure-resistance claim |
| LLM03 Supply Chain | S01, S03–S07 | Frozen bytes, pinned dependencies/images, archive identity and changed-evidence rejection; no claim to audit every upstream dependency |
| LLM09 Misinformation | S02, S06–S07 | Honest development-set and unknown-support claims; unchanged measurement arithmetic, not new factual validation |
| LLM10 Unbounded Consumption | S04–S07 | No model/paid execution and preserved hard resource/accounting boundaries; no new live DoS experiment |

P00 does not claim new coverage of prompt injection, poisoning, tool agency,
prompt leakage or embedding attacks. Those exercises remain mapped to later
milestones, even when P00 preserves supporting architectural boundaries.

## 7. Final acceptance and rollback

The following S01–S07 acceptance record is concluded and remains historical:

- [x] Root layout and authoritative guidance describe one R&D application;
  roadmap, implementation plan, reference and measured history are discoverable.
- [x] Frozen/public/dependency/evidence bytes and the same named accounting and
  Garage resources are preserved; root private data is untouched and excluded.
- [x] Generic Make commands work; documented `hw01-*` aliases route correctly;
  environment names, CLI behavior, pinned images and safe defaults remain stable.
- [x] Full offline checks, positive reproduction, intended negative control,
  archive restoration, build/ignore isolation and scoped link checks pass.
- [x] An isolated public-source export reproduces the same eight variants and
  240 outcomes without private settings, ledger, host Python or a model runtime.
- [x] Migration evidence and limits are archived/referenced; no new inference,
  paid spend, labels, data/schema/prompt revisions or history rewriting occurred.
- [x] P00's decision and remaining limitations are recorded. No later milestone
  execution, staging, commit or push is implied by completion.

Additional follow-up gate:

- [x] S08's follow-up environment/package/Compose migration passes its independent
  preservation, compatibility and rollback gates; remaining persistent/archive
  names have explicit retain dispositions.

Stop a slice if a destination differs unexpectedly, a resource resolves to new
empty storage, frozen hashes/metrics change, private data enters a candidate
image/export, or reproduction is unavailable. Preserve evidence and resolve the
specific cause; do not weaken validation or regenerate identities to proceed.

Rollback reverses only the scoped candidate file moves/edits using the S01
checkpoint. Protect unrelated working changes and retain verified ignored data
and settings at their documented recoverable locations. Existing named volumes,
archive objects and ledger histories are never deleted or reset. Avoid blanket
Git resets, force pushes and destructive Docker cleanup as rollback mechanisms.

## 8. Revision history

| Version | Date | Change |
| --- | --- | --- |
| 1.0 | 2026-10-31 | Initial ordered P00 plan, rooted in the completed baseline, with migration invariants, topic mapping, acceptance gates and rollback. |
| 1.1 | 2026-10-31 | P00 executed; all acceptance gates passed. See the migration report for evidence and limits. |
| 1.2 | 2026-10-31 | Add planned S08: low-risk legacy-name cleanup, risk-gated runtime/storage decisions and immutable historical-format preservation; original S01–S07 acceptance retained. |
| 1.3 | 2026-10-31 | Execute selected low-risk cleanup; retain/defer runtime, package, storage and historical-format names. |
| 1.4 | 2026-10-31 | Select and verify atomic DI settings, package metadata and Compose project migration; retain explicit external storage and immutable evidence identities. |
