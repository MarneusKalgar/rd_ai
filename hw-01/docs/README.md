# HW-01 documentation

Start with [running extractions](guides/running-extractions.md), the
[active experiment plan](plans/matrix-experiment.md), or the
[latest v2 baseline results](reports/v2-continuation-results.md).
The [project README](../README.md) provides the homework entrypoint and commands.

Documents are grouped by purpose. Guides explain operations; reference describes
contracts and implemented behavior; plans describe proposed work and approval
gates; reports retain measured evidence and its original conditions; quality
documents define verification and review. Historical report status is not an
instruction to rerun a completed experiment.

## Guides

- [Archive, upload and restore experiment evidence](guides/archiving-results.md).
- [Run and save extractions](guides/running-extractions.md).
- [Use native Ollama with Python in Docker](guides/native-ollama.md).
- [Configure Docker and persistent storage](guides/docker-runtime.md).
- [Inspect saved outputs with deterministic row diagnostics](guides/row-diagnostics.md).

## Reference

- [Purchase-order extraction contract](reference/extraction-contract.md).
- [Model adapters and client ownership](reference/model-adapters.md).
- [Execution coordinator, retries and budget accounting](reference/execution-coordinator.md).
- [Runtime JSON/schema validation](reference/runtime-validation.md).
- [Configuration, records and offline preflight](reference/offline-preflight.md).
- [Evaluation rules and metric populations](reference/evaluation.md).

## Plans

- [Required provider/local matrix and optional local exercises](plans/matrix-experiment.md).
- [Provider-screening protocol](plans/provider-screening.md).

These documents retain execution history alongside the protocol. Their current
status and linked reports identify completed work; proposed phases do not grant
permission for model inference or spending.

## Reports

| Evidence | Document |
| --- | --- |
| Checked archive, Garage upload and restored evaluation | [Archive workflow verification](reports/archive-workflow-verification.md) |
| Docker setup acceptance | [Docker setup verification](reports/docker-setup-verification.md) |
| Interrupted Docker extraction smoke | [Extraction smoke](reports/extraction-smoke.md) |
| Native smoke acceptance | [Native runtime verification](reports/native-runtime-verification.md) |
| Provider smoke preparation and approval | [Provider smoke preparation](reports/provider-smoke-preparation.md) |
| Provider smoke acceptance | [Provider runtime verification](reports/provider-runtime-verification.md) |
| Local runtime measurements and comparison method | [Local runtime comparison](reports/local-runtime-comparison.md) |
| Native output-allowance diagnostic | [Output allowance experiment](reports/output-allowance-experiment.md) |
| Native largest-input/context diagnostic | [Native large-context experiment](reports/native-large-context.md) |
| Provider selection | [Provider screening results](reports/provider-screening-results.md) |
| Stronger Flash and output-limit diagnostics | [Stronger-model experiment](reports/stronger-model-experiment.md) |
| Original v1 review and thinking decision | [Matrix baseline review](reports/matrix-baseline-review.md) |
| Revised v1 all30 baseline comparison | [Revised v1 baseline results](reports/revised-v1-baseline-results.md) |
| Native v2 gold10 | [Native v2 gold results](reports/native-v2-gold.md) |
| Completed v2 all30 baselines | [V2 continuation results](reports/v2-continuation-results.md) |
| Cumulative budget migration audit | [Budget revisions](reports/budget-revisions.md) |

Raw model evidence belongs under `results/`, separately from these narrative
reports. The [compact v2 checkpoint](../results/submission/v2-baseline-review-20261025/README.md)
explains which new evidence is locally retained and awaiting archival; a fresh
checkout does not contain those raw v2 bundles.

## Quality

- [Testing strategy and verification boundaries](quality/testing-strategy.md).
- [Review checklist](quality/review-checklist.md).

Shared repository conventions remain in the
[coding conventions](../../docs/coding-conventions.md) and
[review process](../../docs/review-process.md).
