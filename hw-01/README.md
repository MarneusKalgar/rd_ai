# HW-01: Structured Extraction Service

HW-01 consumes reviewed customer-neutral text inputs and compares a provider
model with a local model against the same extraction contract. Its v1
[`schema`](schemas/purchase-order-extraction.v1.schema.json),
[`field rules`](docs/extraction-contract.md) and
[`runtime validator`](docs/runtime-validation.md), strict configuration/settings,
attempt/run records and [offline preflight](docs/offline-preflight.md) are
implemented. The initial v1 prompt/configuration exists for preflight. Model
adapters, execution/retries, runtime budget enforcement, measured prompt
variants, saved experiment results and the comparison report remain pending.

Reviews follow the repository's [shared process](../docs/review-process.md) and
the [HW-01 checklist](docs/review-checklist.md) for relevant domain concerns.

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
