# rd_ai

One repository for independent AI homework projects. Each homework owns its
implementation and deliverables. The root
entrypoint is reserved for the reviewer-facing HW run once that service exists.

| Area | Responsibility |
| --- | --- |
| [`hw-01/`](hw-01/README.md) | HW-01 contract, runtime validation and Docker checks; model execution and evaluation follow. |
| [`hw-01/data/`](hw-01/data/README.md) | Frozen neutral input texts, reviewed gold objects, and dataset provenance. |
| [`docs/coding-conventions.md`](docs/coding-conventions.md) | Shared coding conventions for contributors and agents. |
| [`docs/review-process.md`](docs/review-process.md) | Review scope, evidence, verification and reporting rules. |

Agent workflow guidance lives in [`AGENTS.md`](AGENTS.md); `CLAUDE.md` links to
the same file.

For code review, use the repository's
[`rd-ai-code-review`](.agents/skills/rd-ai-code-review/SKILL.md) skill. It checks
requirements, correctness and conventions, with Docker verification and
disposable reproductions where useful.

## Current status

HW-01 has **30 approved neutral inputs and 10 human-approved gold
objects** frozen under [`hw-01/data/`](hw-01/data/README.md). The minimum
dataset counts are met. Model execution and comparison remain to be implemented.

With Docker Desktop/Compose and Make installed, run `make hw01-check` for
contract tests, lint, type checks and gold validation entirely inside Docker.
Use `make hw01-preflight` to verify configuration, prompts and the complete
approved corpus offline.
No host Python or API key is required. This is a contract check, not yet the
final model-comparison command.

The dataset README describes its preparation, approval and evaluation limits.
Original workbooks, private review material and the one-off preparation tool
are excluded from Git. The HW service will consume the included text dataset
directly, without requiring source files or preparation tooling.
