# Deterministic catalog-row diagnostic

`diagnose-rows` inspects saved model outputs against approved source text. It
does not call a model, change extraction status, filter rows, request correction
or change gold scores. The required v1/v2 pipeline remains unchanged.

## Implemented candidate

Check ID: **`catalog-order-evidence-v1`**. It recognizes three prepared order-form
structures using exact column positions and labels, independent of input IDs:

| Profile | Product description | Ordered quantity |
| --- | --- | --- |
| Hungarian | B: `Megnevezés` | C: `Rendelt mennyiség` |
| Dutch | C: `Omschrijving` | F: `Aantal` |
| Romanian | C: `Nume produs` | D: `Comanda` |

Each profile also requires its product-code column/label. Product description
and quantity must belong to the same source sheet and row as that product code.
Shared unit-header cells may belong to another row. Unsupported/mixed structures,
duplicate source row references and malformed relevant cells remain unknown.

For each output `lineItems` entry, match its product name exactly to the parsed
source descriptions. No fuzzy matching, case folding or inferred buyer-code
ownership is used. Then return:

- **Contradicted:** every possible source match has an explicit `[blank]`
  ordered-quantity cell. The candidate regards these as catalog entries under
  these recognized form conventions. All matching rows are retained as evidence;
  it does not invent a unique row reference for repeated descriptions.
- **Supported:** a unique source match has a positive ordered quantity, and the
  output does not reuse that product name for multiple rows. This supports only
  selection of the row, not its other fields or extraction completeness.
- **Unknown:** the layout, source match or order evidence is unclear. Mixed
  ordered/catalog matches, repeated ordered descriptions and repeated output
  descriptions are not resolved by guessing. Missing/null output names and
  paraphrases remain unknown. Missing, zero, negative, comma-decimal or otherwise
  unfamiliar quantities do not automatically prove catalog membership.

Unusable/truncated extractions receive a record-level unknown result with no
output-row findings. Row-count totals count inspected output rows, not documents;
check the record-level status as well. A record is contradicted if any row is
contradicted, otherwise unknown if any row is unknown, otherwise supported.

**This is a layout-specific diagnostic candidate, not a general semantic
validator.** A positive quantity is not a universal prerequisite for every
legitimate PO line. Unit/quantity value correctness, missing rows, output order,
date/party roles and total reconciliation are not implemented by this check.

## Run without inference

From the repository root, inspect exported evidence on the host:

This example uses the retained original exports. After a fresh checkout, follow
the [archive restore instructions](archiving-results.md#historical-submission-evidence),
which include a read-only diagnostic command for the isolated restore.

```sh
make -s hw01-diagnose-rows ARGS='matrix-native-v1-baseline-remaining-20261023-72'
```

Multiple run IDs are accepted and remain separate in the report. To inspect
terminal records in the named results volume instead, add `--source runs`.
The default is `--source submission`; Make mounts that host subtree read-only.
With `make -s`, stdout contains JSON and Docker build logs go to stderr, so the
report can be redirected to a local file.
The command runs in the network-disabled offline container and never starts
Ollama. A report containing contradictions still exits successfully: exit zero
means the diagnostic completed, not that extraction is correct. Invalid hashes,
inconsistent artifacts or unfinished runs return an application error.

The report includes:

- Check version, profile definitions and implementation file hashes.
- Original manifest/record/source hashes and original run/record status.
- Output JSON paths, source line numbers, sheet/row/cell references, quantity
  values and exact source text supporting each finding.
- Supported/contradicted/unknown output-row counts and per-record findings.

Source bytes and saved record/export hashes are checked before inspection.
Corpus/gold manifest metadata is read for approval, membership and schema hashes;
gold answers, annotation explanations and manifest gold line counts are not used
to decide which rows were ordered. No gold-answer or annotation file is needed.
Historical records, raw replies, prompts, frozen data and scoring are preserved.

## Verification and use

Focused tests cover all three source structures; package sizes and prices as
distractors; wrong sheet/row/column evidence; missing/zero/ambiguous quantities;
duplicate names and references; unsupported layouts; unusable outputs; tampered
source/record hashes; and a real CLI process that works without gold answers,
makes no additional HTTP requests and leaves saved results byte-for-byte intact.

Assess false positives and missed errors using reviewed examples before using
this candidate to reject output or trigger correction. Gold10 has already been
used during development; diagnostic flags on the other20 inputs are not new
human labels. Do not report precision/recall without reviewed check labels.
Future behavioral validation belongs to the separate workflow experiment in
[the semantic-validation sequence](../plans/matrix-experiment.md#semantic-validation-sequence-732).

## Saved v1 observations — 24 October 2026

The command inspected 60 saved observations: both revised 30-input v1 baselines,
including their reused source runs. All 128 original export payload hashes were
rechecked unchanged. No inference ran. The three recognized input layouts yield:

| Input | Model | Supported output rows | Contradicted output rows | Unknown output rows |
| --- | --- | ---: | ---: | ---: |
| S016 | Native Gemma | 1 | 66 | 0 |
| S032 | Native Gemma | 8 | 124 | 0 |
| S040 | Native Gemma | 11 | 146 | 0 |
| S016 | Flash | 1 | 0 | 0 |
| S032 | Flash | 13 | 0 | 0 |
| S040 | Flash | 11 | 0 | 0 |

Across all inspected outputs there are 45 supported, 336 contradicted and 1,048
unknown row findings. Other inputs, including the failed native S033 record,
remain record-level unknown under this first candidate. These are diagnostic
counts, not precision/recall or replacement accuracy scores. In particular,
S032's 124 source-evidence contradictions are not the gold scorer's 119 extra
rows: membership evidence and the difference between output/gold row counts
measure different things. Original gold scores and run statuses are unchanged.

The versioned [summary](../../results/submission/catalog-row-diagnostics-20261024/summary.json)
retains the check identity, source run IDs, counts and generated-report metadata.
Its `files.sha256.json` lists only the included summary. The full per-row report
is local at `results/diagnostics/catalog-row-diagnostics-20261024/diagnostic.json`,
covered by the existing Git ignore rule. Its SHA-256 and byte size are retained
under `generated_report` in the summary, not presented as an included submission
file. Original model outputs remain versioned; the verbose derived report can
be regenerated without inference.

From the repository root, reproduce the full 60-observation report with the same
diagnostic implementation and source exports:

```sh
mkdir -p hw-01/results/diagnostics/catalog-row-diagnostics-20261024
make -s hw01-diagnose-rows \
  ARGS='matrix-native-v1-baseline-remaining-20261023-72 native-s008-49152-16384-20261022 flash-v1-gold-16384-20261022 matrix-provider-v1-baseline-remaining-20261023-72' \
  > hw-01/results/diagnostics/catalog-row-diagnostics-20261024/diagnostic.json
```

Compare the generated file's hash with `generated_report.sha256`. Changed
implementation hashes or source artifacts require a new diagnostic identity or
snapshot rather than rewriting this historical summary.

The full offline gate passed
**722 tests**, including 38 new focused tests, plus lint/format, strict types,
gold validation and preflight. The real CLI fixtures delete gold-answer and
annotation files before diagnosis and verify no HTTP calls or result writes.

Subsequent test hardening expands the diagnostic suite to **48 tests** and
catches all five audited mutation probes: lost failed records, empty duplicate
findings, wrong quantity columns, unknown status hiding a contradiction, and an
incorrect aggregate implementation hash. The unmodified and restored suites
pass; the full offline gate passes **732 tests** plus lint/format, strict types,
gold validation and preflight. This test-only hardening does not change the
original saved report, check implementation identity or extraction scores. See the
[test strategy](../quality/testing-strategy.md#regression-hardening-after-the-test-audit).
