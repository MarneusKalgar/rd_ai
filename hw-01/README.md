# HW-01: Structured Extraction Service

HW-01 consumes reviewed customer-neutral text inputs and compares a provider
model with a local model against the same extraction contract. Its v1
[`schema`](schemas/purchase-order-extraction.v1.schema.json),
[`field rules`](docs/extraction-contract.md) and
[`runtime validator`](docs/runtime-validation.md), strict configuration/settings,
attempt/run records, [offline preflight](docs/offline-preflight.md) and
[OpenRouter/Ollama adapters](docs/model-adapters.md), including client injection
and application-owned client scopes, are implemented. The shared
[execution coordinator](docs/execution-coordinator.md) adds bounded retries,
one correction, deadlines, dependency stops and a cumulative reservation ledger.
The initial v1 prompt/configuration exists for preflight. The
[Docker runtime setup](docs/docker-runtime.md) provides isolated checks, an app
image, pinned Ollama/Gemma initialization and persistent results storage.
`make hw01-local-ready` from the root checks six representative requests;
`make hw01-local-capacity` optionally checks all 60 prepared requests.
The [selected extraction runner](docs/running-extractions.md) adds actual-request
admission, incremental records/checkpoints, budget administration, CLI/Make
commands and checked exports. Live acceptance is tracked separately; provider
inference requires verified coverage and explicit human approval. Measured prompt
variants, the complete matrix and the final comparison report remain pending.

The [provider smoke evidence](docs/provider-runtime-verification.md) records the
approved Gemini 3.1 Flash-Lite run: two schema-valid outputs, one truncation,
verified export and $0.01518250 in billed cost. Together with native local
acceptance, this completes 6.6.6. Further paid execution needs separate approval.

[Provider screening](docs/provider-screening.md) prepares section 7.1 on the
10 approved gold cases, using the [offline evaluator](docs/evaluation.md).
The [approved screening run](docs/provider-screening-results.md) completed both
Gemini candidates; Mistral stopped on upstream rate limits in both the original\ninvocation and one separately approved retry. The user accepted completing 7.1
with the Gemini pair: Gemini 3.5 Flash-Lite is frozen as the main provider in
`config/experiments.yaml`; Mistral remains unranked. Further paid execution
needs the documented approval.
The [main matrix](docs/matrix-experiment.md) uses all 30 inputs for both prompts
and sampling settings, starting with unchanged v1/baseline on both models.

[Native Ollama mode](docs/native-ollama.md) uses the existing desktop app through
`MODE=native`, with Python still in Docker and an explicit patch compatibility policy.
It preserves Docker execution and uses the same admission/runner/record path.
Use `make hw01-setup-native` for explicit native weight initialization.

Reviews follow the repository's [shared process](../docs/review-process.md) and
the [HW-01 checklist](docs/review-checklist.md) for relevant domain concerns.
The [testing strategy](docs/testing-strategy.md) defines test levels, execution
boundaries and their implementation-plan points.

## Project layout

`hw-01/` is the independent homework project. Its importable Python package
lives in `src/extraction_service/`, with modules grouped by responsibility:
`configuration/`, `corpus/`, `extraction/`, `inference/`, `execution/`, `runtime/`
and application composition/persistence in `application/`.

Provider-specific adapters, response parsing, capabilities and metadata probes
live in `inference/openrouter/` and `inference/ollama/`. Shared HTTP clients and
their application-owned scopes live in `inference/transport/`. The coordinator
uses `execution/budget/` for the persistent ledger, verified pricing and spending
admission. Shared request/response types stay at the `inference/` level.

Inside the Docker image, `python -m extraction_service` invokes the CLI.
The root `make hw01-*` targets identify the homework and route to this project.

## Check the contract in Docker

Prerequisites: Docker Desktop with Compose, and Make. No host Python, uv,
model installation or API key is required for these offline checks. The first
build downloads the pinned images and locked Python dependencies.

From the repository root:

```sh
make hw01-check
```

This builds the HW image, runs Ruff lint/format checks, strict mypy checks and
pytest, then validates all 10 frozen gold objects and runs full offline preflight.
From this directory,
`make check` runs the same workflow. To validate only gold objects, use
`make hw01-validate-gold` from the root or `make validate-gold` here.

Make loads Compose controls from `.env.compose` when present, otherwise from
[`.env.compose.example`](.env.compose.example). Copy the example for machine-local
memory/context/deadline overrides. Provider credentials and application URLs stay
in the separate optional `.env`; neither file enters the image. See
[runtime configuration](docs/docker-runtime.md#configuration-and-deadlines).

The image uses Python 3.14.8 and uv 0.12.11 pinned by image digest, with
dependencies resolved in `uv.lock`. Checks run without a network, as a
non-root user, with a read-only image filesystem and writable temporary
storage. The build context contains only this HW's approved artifacts and
source; it excludes private preparation data and tooling.

These commands check the extraction boundary; they do not yet run the
provider/local comparison required for final submission.

## Verify the complete setup offline

Run `make hw01-preflight` from the root or `make preflight` here. It checks
configuration, prompt references, all 30 input hashes, the gold-manifest link,
10 gold objects, current annotation hashes and source/layout metadata. No
provider key, model runtime or model download is required. The JSON report
explicitly leaves model capabilities unverified. See
[offline preflight](docs/offline-preflight.md) for settings, records and limits.

## Dataset status

[`data/`](data/README.md) contains **30 approved neutral inputs**, including
**10 human-approved gold objects** (34 gold ordered lines), frozen after user
approval on 2026-10-17. `corpus-manifest.json` enumerates all model inputs;
`manifest.json` records the gold pairs. Both record approval and artifact
hashes. Draft labels for the other 20 inputs remain private.

Dataset preparation and review are described in [`data/README.md`](data/README.md).
Original workbooks, private mappings and the one-off preparation tool are
excluded from the submission. The eventual HW-01 launch command will consume
the included frozen text dataset directly. New gold objects require human
approval; repeatable generation alone is insufficient.
