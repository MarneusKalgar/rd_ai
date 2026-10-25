# V2 baseline review checkpoint

This directory contains the compact reviewed results of the completed v1/v2
baseline comparison. It is not a complete run export or an external archive.

- `summary.json` records both models' all30 operations, development gold10
  scores, selected execution controls, failures and cumulative accounting.
- `evidence-index.json` identifies the twelve new v2 source bundles retained
  locally, with hashes of their original inventories/manifests. Those hashes
  identify omitted evidence; they do not claim that its payloads are included
  in this checkout. Previously committed v1 evidence is unchanged.

The new raw responses, checkpoints, preparation reports, detailed evaluations
and membership snapshots remain untracked pending an archival workflow. No
Garage upload, portable archive or restore command is supplied by this commit.
The working copies have been retained without deletion or Git-history changes.

A fresh checkout can run the offline implementation tests and inspect this
summary, but cannot independently recompute the new v2 scores without the
original evidence. Restore and verify the original run bundles before using
the documented export/evaluation workflow. Rerunning model inference would
produce a different experiment and is not a substitute for restoration.

Gold10 informed prompt/model development. Its scores are not held-out accuracy;
the other20 have no factual accuracy labels. Native v2 retains S004's truncation.
See [results and limitations](../../../docs/v2-continuation-results.md).
