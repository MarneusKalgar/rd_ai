# Repository guidance

## Project boundaries

- This repository contains independent AI homework projects. Each homework owns
  its dependencies, implementation, data, checks and deliverables.
- HW-01 lives in `hw-01/`. Read its README and relevant documents before editing.
- Start at `hw-01/docs/README.md` for guides, reference, plans, reports and quality
  documentation. Keep new documents in the group matching their primary purpose.
- Root Make targets route to homework commands. Keep private data preparation
  out of the reviewer-facing workflow.
- Work here does not automatically change AspectLoop or its AI-track scope.

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
  `hw-01/schemas/purchase-order-extraction.v1.schema.json`; field semantics are
  documented in `hw-01/docs/reference/extraction-contract.md`.
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
- Run `make hw01-check` from the repository root for Ruff lint/format checks,
  strict mypy checks, pytest and frozen gold validation.
- Use `make hw01-validate-gold` when only gold validation is needed.
- Dependencies are declared in `hw-01/pyproject.toml` and locked in
  `hw-01/uv.lock`. Update both together when changing dependencies; see
  `hw-01/docs/reference/runtime-validation.md` for the Docker lock-update command.
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
  Git or import it into the homework service.
- Never commit API keys or credentials. Keep actual secrets in ignored local
  configuration and include only harmless examples in `.env.example`.
- Keep changes scoped. Do not stage, commit, push, change branches or amend
  history unless the user requests the corresponding Git action.
