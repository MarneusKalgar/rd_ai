# Document intelligence R&D

One Python application for measured purchase-order extraction, source support
and human-reviewed correction research. The [roadmap](docs/roadmap.md) defines
P00–P05; [the documentation index](docs/README.md) links guides, contracts,
plans, reports and verification evidence.

The existing extraction baseline contains thirty approved neutral text inputs,
ten human-approved development-gold objects and 240 attempted matrix observations.
Provider v2 matched the development labels; assisted local trials retained
substantial whole-document errors. See [REPORT.md](REPORT.md) for populations,
costs, failures and generalization limits. Retrieval, review tools and an API
remain future milestones; repository consolidation does not implement them.

## Verify without models

Prerequisites: Docker Desktop/Compose and Make. No host Python, provider key or
Ollama installation is required for offline verification.

```sh
make help
make check
make preflight
```

With the separately supplied indexed public archive in `results/archives/`:

```sh
make reproduce-report
```

The [reproduction guide](docs/guides/reproducing-results.md) explains retrieval,
identity checks and the public manifest-bound historical budget policy. It
reproduces eight variants and 240 outcomes without a private spending ledger,
credentials or archived script execution. Bulk evidence remains ignored; compact
archive indexes and receipts are versioned under `archive-index/`.

## Runtime and compatibility

Python, dependencies and substantial scripting run in Docker. Native Ollama is
the selected local inference runtime; its use is explicit. Provider inference
requires the separately approved concrete invocation and allowance. Offline
checks never start model services. Docker Ollama compatibility commands remain
explicit and may download removed resources; they are not the default workflow.

Current commands run from this repository root. Legacy `hw01-*` Make aliases
were retired; use canonical targets such as `make check` and
`make reproduce-report`. Historical `cd hw-01` directions describe the old layout.
The package is `document-intelligence`; settings use `DI_*` and Compose uses
project `rd-ai`. The Python namespace remains `extraction_service`. Explicit
external volume names retain the original storage and ledger; the bucket and
historical `hw01/` archive namespace remain unchanged. See the
[runtime naming migration](docs/guides/runtime-name-migration.md) for compatibility
and rollback instructions.

Local `.env`, `.env.compose` and `.env.archive` files remain ignored. Make falls
back to `.env.compose.example` when no local controls file exists. Never reset
the cumulative ledger because the project layout changed.

## Repository boundaries

| Area | Responsibility |
| --- | --- |
| `src/extraction_service/`, `tests/` | Application responsibilities and controlled verification |
| `schemas/`, `data/`, `prompts/`, `config/` | Frozen approved artifacts and versioned experiment/runtime configuration |
| `docs/` | Roadmap, milestone plans, guides, reference and measured history |
| `archive-index/` | Compact public evidence inventories and verified storage receipts |
| `results/` | Ignored local runtime outputs, exports, caches, restores and proofs |

Original workbooks, root `data/private/`, private mappings, local settings and
one-off preparation tools stay outside Git, image contexts and provider requests.
The [dataset provenance](data/README.md) retains original approval and exposure
limits. Saved experiments remain immutable and are not automatically rerun.

Contributor guidance lives in [AGENTS.md](AGENTS.md), with `CLAUDE.md` as its
relative symlink. Follow [coding conventions](docs/coding-conventions.md) and
the [review process](docs/review-process.md). AspectLoop remains a separate
product and repository; this project does not change its scope or milestones.
