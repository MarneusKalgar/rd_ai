# Runtime naming migration

P00-S08 changes live names without moving stored evidence. Current commands run
from the repository root. Historical commands in reports describe the names
used at the time and are not current setup instructions.

| Surface | Current name / policy |
| --- | --- |
| Python project metadata | `document-intelligence`; import namespace remains `extraction_service` |
| App, setup and archive settings | `DI_*`, `DI_SETUP_*`, `DI_ARCHIVE_*` |
| Provider credential | `OPENROUTER_API_KEY`, unchanged |
| Compose project / generated images and network | `rd-ai` |
| Persistent results and Garage data | Explicit external `rd-ai-hw01_results` and `rd-ai-hw01_garage-data` |
| Optional Docker model volume | External `rd-ai-hw01_ollama-models`; native remains the default |
| Existing bucket, keys and archive formats | Retained verbatim, including `hw01-evidence` and `hw01/archives/sha256/…` |

## Settings compatibility

This is an atomic migration, not a dual-name transition. Replace the `HW01_`
prefix with `DI_` in shell overrides and local `.env`, `.env.compose` and
`.env.archive` files. Preserve every value, file permission and credential.
`GARAGE_*`, `OLLAMA_*` server variables and `OPENROUTER_API_KEY` are unchanged.
Current `.env.*.example` files show the new contract. Never regenerate Garage
credentials or initialize a new budget ledger to perform this migration.

The three Python settings loaders reject old process/dotenv names even when
new names are present. Make rejects old shell/command-line overrides and old
names in its selected Compose controls file before Compose can use defaults.
Use Make for the guarded entrypoint; direct Compose invocation bypasses Make's
controls-file check. A stale settings file must be migrated, not worked around
by accepting defaults or supplying both names.

## Persistent resources

The project name controls disposable container/image/network names. It does not
control the three explicitly named external volumes. Missing external storage
fails rather than creating a fresh empty volume. Existing initialized storage
is required for the operational configuration; this is not a first-install
storage provisioning workflow.

The Docker Ollama volume was previously removed. It is deliberately not
recreated during S08; native Ollama remains available independently. An explicit
future Docker-local setup needs deliberate volume provisioning first.

Never run old and new Garage containers simultaneously against the shared data
volume. The old `rd-ai-hw01-garage-1` is retained stopped as a rollback aid. Use
`make archive-store-up` and `make archive-store-down` for the current project.
No volume pruning, `down -v`, bucket rekeying or evidence rewriting is needed.

## Local rollback

Before cutover, ignored `results/recovery/S08-20261031/` captured both volumes as
tar files, per-file hashes/owners/modes, the original private settings and a
source inventory. These contain private accounting/settings: keep the entire
directory ignored and do not include it in public archives. The recovery copy
is on the same laptop and is not an off-device backup.

For a naming-only rollback, stop the new Garage container, restore the public
source/configuration from commit `dc6b5ed`, and restore the three private settings
from the checkpoint with their original permissions. Reuse the original volumes
and start the old project's Garage. Do not restore a volume snapshot over newer
records: the migration did not move data, and doing so could discard subsequent
accounting or archives. Volume restoration is an offline recovery operation
requiring a separate inspection of changes since the checkpoint.

The [execution record](../reports/runtime-name-migration.md) records actual
verification and retained identifiers.
