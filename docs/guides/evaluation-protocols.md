# Evaluate a frozen experiment without inference

P01 adds `validate-evaluation-protocol` and `evaluate-experiment`. Both use
network-disabled Docker services without provider settings, model dependencies
or a named accounting volume. They cannot grant generation permission.

The current record is `config/evaluation/P01-E01-v4.json` (protocol format v3).
Earlier files retain the inventory/rubric/control freeze history; they are not
instructions to rerun old model experiments. V4 preserves the first analysis
and writes the verified result into a different directory. It does not change
the declared comparison, thresholds or zero-inference limits.

## Provide public evidence

Use the [archive guide](archiving-results.md) to obtain the pinned section 8
archive. From the repository root:

```sh
make download-archive ARGS='--index archive-index/c3398a3c846488086ef52be9a4706b0eb9568ab94f56f42d3190610d96ad263b.json'
make reproduce-report
```

The first command uses explicitly configured local S3 credentials and performs
no model requests. Reproduction verifies/restores the public archive without a
private spending ledger. It checks an existing restore rather than replacing it.

## Validate, evaluate and check

```sh
make validate-evaluation-protocol ARGS='--source results/restored/c3398a3c846488086ef52be9a4706b0eb9568ab94f56f42d3190610d96ad263b/submission'
make evaluate-experiment ARGS='--source results/restored/c3398a3c846488086ef52be9a4706b0eb9568ab94f56f42d3190610d96ad263b/submission'
```

Use `--protocol config/evaluation/P01-E01-v4.json` explicitly when desired.
Validation checks the protocol, artifact hashes, corpus/exposure/label identity,
rubric policy, selected archive bundles, terminal records and original execution
policies. Analysis also requires the actual side identities to match the frozen
declarations. Only the existing public manifest-bound budget-cap normalization
is applied. Other settings are not normalized to force a comparison.

The result is published as a new ignored directory containing `report.json`,
the exact `protocol.json` and `files.sha256.json`. Existing output is refused.
To check a result again without replacing it:

```sh
make evaluate-experiment ARGS='--source results/restored/c3398a3c846488086ef52be9a4706b0eb9568ab94f56f42d3190610d96ad263b/submission --check-result results/submission/P01-E01-verified/report.json'
```

Changed results or evidence produce exit 2. Error output is redacted to exception
type. Analysis is capped at the protocol's deadline, at most 300 seconds;
validation at most 900 seconds. Failures are not automatically retried.

## Read the result

Both side aggregates reuse the original scorer and operational metrics. Thirty
inputs remain in operational populations. Only the same ten approved gold cases
receive factual scores. Failed and terminal not-attempted records stay selected;
a missing record is a provenance/population failure, not a dropped case.

Primary accuracy retains extra-row penalties and its original denominator on
each side. Gold-only transition counts have a different, fixed population of
342 expected field paths. They retain positional matching and cannot replace
the primary metric. Extra rows, missing rows, present/null paths, mechanical
tags and exclusive gold outcome counts remain separate.

Review metrics keep synthetic anchors separate from human-reviewed judgments.
P01-E01 supplies no new human semantic anchors, so acceptance rates are
unavailable. Source support is not correctness, and evaluation does not grant
permission to apply changes. Model refusals/invalid output are not successful
abstentions. Semantic error causes remain unreviewed.

The report records protocol/exposure/rubric/control/policy and implementation
hashes. Synthetic challenge results establish finite technical boundaries only;
they do not measure live model attack susceptibility. See the
[P01 execution report](../reports/P01-evaluation-protocols.md).
