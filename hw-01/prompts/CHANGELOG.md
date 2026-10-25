# Prompt changelog

## v1

Created before model experiments as the configuration/preflight baseline: schema-conforming JSON, explicit
missing values, no invention, identifier/date/decimal representation and ordered
line selection. Its bytes remain unchanged after the completed full-corpus
provider/native baseline runs. See the recorded matrix baseline review.

## v2 draft — 22 October 2026

Created only after reviewing the completed 30-input provider baseline and the
user-approved 30-input thinking-disabled native rebaseline. The earlier
thinking-enabled native run remains a separate diagnostic. This original draft
was prepared for the historical 4,096-output-token profile, with native
thinking=false and unchanged frozen data/schema/gold and shared scoring.
Its SHA-256 was `c2c6c61dcdd3fe9c93fcaf9b40d6f811a30fb9351e6918fcaa899459021e5ba0`.
It was not executed or frozen as a measured variant.

- Select explicit positive ordered quantities first; exclude blank/zero catalog
  rows and preserve order/repeated products. S003/S012/S021 and truncated
  catalog-form outputs motivated this clarification.
- Distinguish cell/row provenance from printed PO/line identifiers and require
  explicit buyer ownership for product IDs. Reviewed cases include S002/S032.
- Require line-linked dates, conservative parties/currency/total roles, source
  address components joined with '; ', and source precision in decimal strings.
- Clarify language-dependent unit categories and OTHER versus UNKNOWN; inspect
  S002/S032/S044 without embedding their PO identifiers or product values.
- Request compact complete JSON to reduce formatting overhead within the same
  allowance; never rescue partial JSON or change the scorer.

All 10 approved gold cases were inspected for errors and are tuning/development
data, not an independent held-out evaluation. Unlabeled corpus outputs informed
only qualitative failure/row-selection observations. These benchmark-specific
positive-quantity and representation rules do not establish universal business
semantics for every PO layout. No case-specific answer objects, identifiers or
product values were included in the draft. Its quality was not measured.

## v2 — 24 October 2026, instruction-only revision

Re-reviewed against the revised stronger Flash/native Gemma v1 baselines and
the detection-only source-row findings. Retain the draft's creation history;
this revision is the first v2 selected for execution.

- Bind the order quantity, description and unit to the same logical product
  entry, including documents with adjacent table panels.
- Scope blank/missing/zero quantity exclusion to catalog/order-entry evidence.
  Preserve an otherwise explicitly ordered item with null quantity when the
  source gives item-specific order evidence; presence on a form is insufficient.
- Retain conservative buyer-code roles, line-date linkage, source-order ship-to
  components joined with '; ', precision and unit interpretation.
- Add no synthetic worked examples, benchmark answers, skill resources or new
  model workflow stages. Semantic diagnostics remain detection-only after runs.

Use the same frozen instructions for native Gemma and stronger Gemini 3.5 Flash
in `config/matrix.yaml`, with 16,384 output tokens, temperature 0 and top_p 1.
Native context is 49,152 and thinking=false; preserve the provider's v1 reasoning
settings when its separately approved phase is prepared. These supersede the
draft's historical 4,096-token assumptions.

The user requested native Gemma gold10 only. Native remaining20 require result
review and separate approval; no provider invocation is authorized. If the prompt
changes after gold10, assign a new revision/hash and rerun gold10 before pooling
with its remaining20. Gold10 remains development data, not held-out evaluation.

Frozen prompt SHA-256 for this gold10 invocation:
`6a03379937695a2e5b127d292fc6ddb2301c9048b730ca3f9982d6c6443d155b`.

The subsequently approved native remaining20 and both stronger Flash v2 phases
used these same frozen bytes. Both all30 baseline variants are verified; see
[v2 continuation results](../docs/reports/v2-continuation-results.md) and the
[compact review checkpoint](../results/submission/v2-baseline-review-20261025/README.md).
New raw evidence remains locally retained and unversioned pending archival.
