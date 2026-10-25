# V2 baseline review checkpoint

The [archival workflow](../../../docs/guides/archiving-results.md) was implemented
after this checkpoint; its [verification report](../../../docs/reports/archive-workflow-verification.md)
records the subsequent local Garage copy and restored evaluation. Availability
fields below and in the original JSON are checkpoint-time observations, not a
live catalog of later archive receipts.

This directory contains the compact reviewed results of the completed v1/v2
baseline comparison. It is not a complete run export or an external archive.

- `summary.json` records both models' all30 operations, development gold10
  scores, selected execution controls, failures and cumulative accounting.
- `evidence-index.json` identifies the twelve new v2 source bundles retained
  locally, with hashes of their original inventories/manifests. Those hashes
  identify omitted evidence; they do not claim that its payloads are included
  in this checkout. The subsequent retention migration archived previously committed v1 evidence as well; see the [retention report](../../../docs/reports/submission-retention.md).

The new raw responses, checkpoints, preparation reports, detailed evaluations
and membership snapshots remain locally retained, ignored and untracked. Their
subsequent verified archive is recorded in the report linked above; the raw
payloads are not embedded in this compact checkpoint. Working copies remain locally retained. The later [retention report](../../../docs/reports/submission-retention.md) documents removal of bulk evidence from Git tracking and history.

A fresh checkout can run the offline implementation tests and inspect this
summary, but cannot independently recompute the new v2 scores without the
original evidence. Restore and verify the original run bundles before using
the documented export/evaluation workflow. Rerunning model inference would
produce a different experiment and is not a substitute for restoration.

Gold10 informed prompt/model development. Its scores are not held-out accuracy;
the other20 have no factual accuracy labels. Native v2 retains S004's truncation.
See [results and limitations](../../../docs/reports/v2-continuation-results.md).
