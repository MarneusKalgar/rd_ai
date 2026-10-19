# HW-01 review checklist

Use the repository's [shared review process](../../docs/review-process.md) for
scope, evidence, verification boundaries and reporting. This document adds the
HW-01 surfaces to inspect; the [HW README](../README.md) describes implementation
status and verification commands.

Read only the rows relevant to the diff. Use the current contract and feature
documents for exact behavior. Planned configuration, adapters and evaluation
are review surfaces when implemented or changed, not missing requirements in
a deliberately partial slice.

| Surface | Review concerns |
| --- | --- |
| PO contract and validation | Single authoritative JSON Schema; required versus nullable fields; date/decimal/identifier representations; ordered lines; metadata outside PO objects; strict parsing; raw response and error preservation; copies that protect the shared validator. See [field rules](extraction-contract.md) and [runtime validation](runtime-validation.md). |
| Dataset and evaluation | Approved schema/input/gold hashes and provenance; distinction between agent annotations and human approval; source/layout grouping; prompt-tuning leakage; failed attempts retained in denominators. Schema-valid gold does not establish factual correctness or model accuracy. See [dataset documentation](../data/README.md). |
| Configuration and model adapters, when present | Strict configuration and typed envelopes without a second PO schema; provider-neutral acceptance; explicit fallback behavior; model/runtime identity; bounded transport retries and correction attempts; timeout, token and cost accounting, including unavailable values. |
| Docker and dependencies | Documented Docker-only workflow, locked dependencies and pinned images; Python syntax/runtime compatibility; build-context isolation; no dependency on private prep material or host packages. |
| Documentation and mechanical output | Commands match current code; claims and counts match evidence; generated changes trace to their inputs. A comments-only or refactoring claim needs inspection: Python docstrings can be runtime data, including CLI help. |

## Verification

Use the commands under [Check the contract in Docker](../README.md#check-the-contract-in-docker).
That baseline verifies the current contract implementation and approved gold
compatibility. It does not run model adapters or establish extraction accuracy.
Use the [testing strategy](testing-strategy.md) to distinguish component,
integration, CLI/system and live-model evidence for the affected plan points.
Follow the shared review process for any focused reproduction or mutation.
