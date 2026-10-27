# Reproduce the saved comparison

This workflow verifies the published matrix without a provider key, native
Ollama, model downloads, host Python or a private spending ledger. It never runs
inference or archived scripts. Required local software: Docker/Compose and Make.
Building the image may download its pinned base images and locked dependencies;
the verification container itself has no network.

## Provide the indexed public evidence

The bulk archive is deliberately excluded from Git. Obtain
`c3398a3c846488086ef52be9a4706b0eb9568ab94f56f42d3190610d96ad263b.tar.gz`
from the operator or the configured S3/Garage store. Its
[committed index](../../archive-index/c3398a3c846488086ef52be9a4706b0eb9568ab94f56f42d3190610d96ad263b.json)
pins its bytes, size, manifest and bundle inventories. Place it under
`hw-01/results/archives/`; it remains ignored.

For an existing configured Garage installation, the
[archive guide](archiving-results.md) describes storage credentials and retrieval:

```sh
make hw01-download-archive ARGS='--index archive-index/c3398a3c846488086ef52be9a4706b0eb9568ab94f56f42d3190610d96ad263b.json'
```

A recipient who receives the archive directly needs no storage account or
credentials. Do not invent public access to the private local Garage instance.
Garage and caches on one laptop remain a single-machine recovery arrangement.

## One offline reproduction command

From the repository root:

```sh
make hw01-reproduce-report
```

The command verifies the archive, restores it if absent, checks every restored
payload and exact bundle inventory, validates all 240 membership entries and
recomputes the eight variants through the shared evaluator. It checks the saved
evaluation, summary, token counts, processing durations, quality/operations/usage
and per-field tables in `REPORT.md`. Failures, extra/missing rows, unknown values,
source hashes and the explicit sampling-ID alias remain intact. A changed cache,
restore, bound manifest or numerical report claim causes failure.

The compact output is written to
`hw-01/results/reproductions/<archive-sha256>/verification.json`. Original exports,
the archive and compact index are read-only. The service has no named results
volume, model service dependencies, environment credential files or network.
An existing restore is checked rather than trusted or silently replaced.

Absent local Compose overrides, Make uses the harmless `.env.compose.example`.
The clean-checkout path does not need `.env`, `.env.compose` or `.env.archive`.

## Historical budget policies

The [public evaluation policy](../../config/evaluation-budget-policy.json) is a
reviewed, manifest-bound record of the original $4.50→$10 cap raise. It contains
the original audit reference/hash and the thirteen exact source manifest hashes,
not reservations, credentials or a synthetic ledger. It allows only read-only
grouping across that administrative cap change. Every other execution, model,
context and sampling identity remains part of the evaluator's grouping key.

For an explicit saved-run evaluation, `evaluate --budget-policy <file>` selects
this public policy. It is mutually exclusive with `--allow-budget-revision`,
which retains the original local-ledger audit behavior. The public policy never
changes live admission, spending limits, unknown-charge holds or inference
approval. Policy provenance is pinned in Git and the reproduction result; it is
not an independently signed provider billing statement.

## What is verified

This reproduces historical evidence and checks implementation. It does not
promise live model/route availability, current prices, a generalization score
or a new factual review of the twenty unlabeled inputs. No new model request is
needed to verify the report. To check code, frozen gold and corpus separately:

```sh
make hw01-check
```

New native inference explicitly uses the installed desktop runtime. Any future
provider invocation still needs the separately approved concrete command and
allowance. The obsolete Docker-only live-local portability assumption is not a
requirement to restart the removed Docker Ollama setup.
