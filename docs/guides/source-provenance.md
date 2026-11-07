# Inspect field provenance without inference

P02 adds a separate provenance report for thirty pinned native v2 baseline
records. It does not change extraction values, scores, prompts or inherited
support-check rules. The [implementation plan](../plans/milestones/P02-source-provenance.md)
and [execution report](../reports/P02-source-provenance.md) define scope and limits.

From the repository root, with the original archive restored:

```sh
make validate-provenance-protocol ARGS='--source results/restored/c3398a3c846488086ef52be9a4706b0eb9568ab94f56f42d3190610d96ad263b/submission'
make assess-provenance ARGS='--source results/restored/c3398a3c846488086ef52be9a4706b0eb9568ab94f56f42d3190610d96ad263b/submission'
make assess-provenance ARGS='--source results/restored/c3398a3c846488086ef52be9a4706b0eb9568ab94f56f42d3190610d96ad263b/submission --check-result results/submission/P02-E01-v3/report.json'
```

Both targets run Python in a network-disabled container with read-only source
evidence. Only assessment publication receives a writable submission directory.
They do not start Ollama, use provider credentials or mount the accounting
volume. The default protocol is `config/evaluation/P02-E01-v3.json`; explicit
older protocols retain their original identities and output directories.
Use the [archive guide](archiving-results.md) to restore missing evidence;
never regenerate missing model outputs.

Validation checks pinned metadata and the actual records. Assessment writes
`report.json`, the exact frozen `protocol.json` and `files.sha256.json` into a
new result directory. It refuses replacement. `--check-result` compares the
whole regenerated report, including implementation identity, without rewriting
it. Exit 0 means the assessment/check completed, not that the extraction is
correct. Invalid evidence, conflicting output or changed reports fail with
redacted application errors.

## Read a finding

The selected paths are `/purchaseOrderNumber`,
`/lineItems/*/buyerProductIdentifier` and `/lineItems/*/buyerDeliveryDate`.
All output rows remain selected, including extras. Other fields are outside
this declared scope; unusable outputs have record-level status and no invented
field paths.

- `location` records exact occurrence candidates, ambiguity, no exact occurrence
  or null. Spans are zero-based, half-open UTF-8 byte ranges into the original
  approved text. Quotation, byte boundaries and source hash must all match.
- `support_status` and `inherited_support` preserve the old role checker. A
  unique PO-number occurrence remains semantically unknown in this slice.
- `context` binds existing cells to exact source-record quotations. These are
  labelled context spans, not fabricated minimal value spans. Absence decisions
  retain a closed-source scope reference rather than an invented blank quote.
- `linkage` reports whether inherited evidence has resolvable context. Repeated
  source-cell identities remain unresolved. Location success never upgrades a
  semantic unknown, proves row membership or certifies the entire PO.

Null values have no literal value quotation. A normalized output date may have
no exact source occurrence. Neither case is itself a contradiction. Candidate
overflow retains at most 64 occurrences and explicitly reports ambiguity.
Source, output-row, payload and execution-time bounds fail explicitly.

`counts` separates field counts from occurrence/context references and failed
records. `semantic_accuracy` remains unavailable because this experiment adds
no reviewed source-support anchors. Synthetic controls are technical evidence,
not new gold labels, independent model validation or human review-time savings.

Full reports and process logs belong in ignored, archived results. Keep compact
indices and bounded summaries in Git; do not add bulky sidecars to the repository.
