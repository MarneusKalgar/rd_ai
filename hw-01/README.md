# HW-01: Structured Extraction Service

HW-01 consumes reviewed customer-neutral text inputs and compares a provider
model with a local model against the same extraction contract. Its v1
[`schema`](schemas/purchase-order-extraction.v1.schema.json) and
[`field rules`](docs/extraction-contract.md) are defined; model runners,
prompts, results, and the comparison report remain to be implemented.

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
