# Repository guidance

## Project boundaries

- This repository contains one document-intelligence R&D application.
- Read `docs/roadmap.md` and the applicable milestone plan before new work.
- Start at `docs/README.md` for guides, reference, plans, reports and quality
  documentation. Keep new documents in the group matching their primary purpose.
- Root Make targets own application commands; use canonical unprefixed targets.
- Keep milestone flow diagrams synchronized with the scoped implementation and
  execution status. Update affected diagrams when a stage, boundary, comparator
  or failure path changes, and check them before milestone closeout. Distinguish
  planned from executed flows. Preserve hash-bound plan snapshots and historical
  diagrams; put current executed flows in the linked report when the plan is frozen.
- Keep private data preparation
  out of the reviewer-facing workflow.
- Work here does not automatically change AspectLoop or its AI-track scope.

## Living AI/ML glossary

- Maintain `docs/reference/ai-ml-glossary.md` during relevant AI/ML work,
  experiment review and interview preparation. Update affected definitions,
  evidence/status and distinctions as part of the scoped documentation handoff.
- Preserve stable term IDs, historical measurements and observed/planned/
  hypothetical distinctions. Verify changing industry claims with primary sources.
- Keep proprietary reference locators in ignored local notes; do not copy source,
  prompts, business payloads or credentials from Elemica into public documentation.
- The glossary does not authorize new model runs or changes in another project.

## Coding conventions

Read and follow [coding conventions](docs/coding-conventions.md) before writing
or modifying code. That document is the authoritative source for readability,
typing, docstrings, constants, module organization and test layout.

`CLAUDE.md` is a relative symlink to this file. Edit `AGENTS.md` to update shared
agent guidance; preserve the symlink rather than maintaining another copy.

## Reviews

Use the repository's `rd-ai-code-review` skill for review requests. Follow
[the review process](docs/review-process.md) for scope, evidence, Docker
verification and reporting. Keep repository files unchanged during review;
put any focused mutation or reproduction in a disposable copy.

## Contracts and approved data

- The authoritative PO extraction contract is
  `schemas/purchase-order-extraction.v1.schema.json`; field semantics are
  documented in `docs/reference/extraction-contract.md`.
- Do not introduce a second handwritten Pydantic PO model. Pydantic validates
  configuration, settings, attempt records and run records.
- Keep operational metadata outside PO output objects. Preserve raw responses
  and explicit validation failures; do not silently repair or coerce outputs.
- The approved inputs, gold answers and schema are frozen. Do not change them
  to make a model or test pass. Contract/data changes require versioning and
  review of the affected labels and approval/hash records.
- Annotation explanations are distinct from human-approved gold labels. Do not
  claim new human review for agent-written documentation.
- Preserve source/layout grouping when splitting evaluation data. Report
  measurements honestly and disclose examples used to tune prompts.

## Runtime and verification

- Run Python, dependency resolution, lint, type checks and tests in Docker.
  Do not install Python packages or model runtimes on the host without an
  explicit user request. Make is the host entrypoint.
- Run substantial scripting in Docker regardless of language. This includes
  JSON processing, checksum generation/verification, artifact aggregation and
  scripted bulk edits. Do not use host Ruby, Python, Node or another interpreter
  to bypass this boundary, even when it is already installed.
- Limit host work to Make/Docker/Git orchestration, direct file edits, simple
  shell commands and basic filesystem/text utilities such as `rg`, `cat`,
  `tail`, `cp` and `cmp`. Move shell pipelines or embedded scripts that perform
  substantial data processing into Docker as well.
- Native Ollama is the explicitly selected exception for local model inference;
  its use does not authorize other application or scripting work on the host.
- P03-S08 additionally permits the installed, subscription-authenticated Codex
  CLI for isolated judge execution and its simple shell orchestration. Bundle
  preparation, JSON processing, validation, tests and aggregation stay in Docker.
  Use the frozen S08 profile; no automatic API/credit/model fallback or unrelated
  host runtime work follows from this exception.
- Run `make check` from the repository root for Ruff lint/format checks,
  strict mypy checks, pytest and frozen gold validation.
- Use `make validate-gold` when only gold validation is needed.
- Dependencies are declared in `pyproject.toml` and locked in
  `uv.lock`. Update both together when changing dependencies; see
  `docs/reference/runtime-validation.md` for the Docker lock-update command.
- Keep base images pinned by digest. Verify model tags, provider capabilities
  and prices before selecting them for measured runs.
- Test meaningful behavior and regression risks. Do not add tests for spacing,
  comments or static configuration. After sufficient verification, stop.

## Private material and Git

- Keep original workbooks, source mappings and private review outputs out of
  Git, image build contexts and provider requests. Only approved neutral
  artifacts belong in the submission dataset.
- `.agents/` contains local inputs and planning/history material; `data/private/`
  contains private preparation outputs. These are not reviewer prerequisites.
- `.agents/skills/` contains versioned repository workflows.
- `tools/po-data-prep/` is an ignored, one-off local utility. Do not add it to
  Git or import it into the application.
- Never commit API keys or credentials. Keep actual secrets in ignored local
  configuration and include only harmless examples in `.env.example`.
- Keep changes scoped. Do not stage, commit, push, change branches or amend
  history unless the user requests the corresponding Git action.
