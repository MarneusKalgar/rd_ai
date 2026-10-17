# rd_ai

One repository for independent AI homework projects. Each homework owns its
implementation and deliverables. The root
entrypoint is reserved for the reviewer-facing HW run once that service exists.

| Area | Responsibility |
| --- | --- |
| [`hw-01/`](hw-01/README.md) | HW-01 extraction contract and, later, model runners, prompts, measurements, and report. |
| [`hw-01/data/`](hw-01/data/README.md) | Frozen neutral input texts, reviewed gold objects, and dataset provenance. |

## Current status

HW-01 has **30 approved neutral inputs and 10 human-approved gold
objects** frozen under [`hw-01/data/`](hw-01/data/README.md). The minimum
dataset counts are met. Model execution and comparison remain to be implemented.

The dataset README describes its preparation, approval and evaluation limits.
Original workbooks, private review material and the one-off preparation tool
are excluded from Git. The HW service will consume the included text dataset
directly, without requiring source files or preparation tooling.
