# Remaining exploratory matrix: checked preparation

Prepared on 25 October 2026 after the sampling diagnostics were committed as `4ece56e`. This preparation authorizes no inference. Original raw records, prompt/input/gold bytes and the provider ledger are unchanged.

## Accepted reuse

All ten observations from `native-v2-gold-t02-p090-20261025` are promoted, including their original outcomes. No observations were selected or omitted by score. The source ID `top-p-09-t02-16384` maps explicitly to required target `exploratory-16384` through `config/matrix-sampling-aliases.json`. Both specify temperature 0.2, top_p 0.9 and 16,384 output tokens.

Each reconstructed original request matches its saved admission fingerprint. A capture-only HTTP substitute exercised the real Ollama adapter for both source/target sampling IDs: all ten complete wire payloads were equal. This made no HTTP inference requests. Stored manifest/record hashes, input/schema/v2 hashes, execution policy, native 0.40.7/digest/tokenizer, context 49,152, thinking=false and loaded model placement match. Residency-expiry timestamps differ and are retained as provenance; they are not generation controls.

Re-evaluation under the explicit alias retains the same quality (197/2,214, 8.90%, one exact development-gold document, 234 extra rows). Source records are not renamed. Alias-aware verification rejects altered controls, conflicting mappings and overlapping logical observations. All other model/prompt/runtime/execution identities remain separate.

**Checked membership: 130/240 covered, 110 unexecuted.** These ten were formerly outside matrix membership; the original diagnostic reports and archives retain that historical population. The other sampling trials remain outside the required matrix.

## Remaining invocations

| Deployment | Prompt | New inputs | Maximum physical calls |
| --- | --- | ---: | ---: |
| native | v1 | 30 | 120 |
| native | v2 | 20 | 80 |
| provider | v1 | 30 | 120 |
| provider | v2 | 30 | 120 |

All four use unchanged `config/matrix.yaml` and `exploratory-16384` (temperature 0.2/top_p 0.9/16,384 output). Native thinking remains false and context remains 49,152. Provider default reasoning is unchanged. Fifty native initial requests passed current full render-only admission; actual correction requests must still pass admission with their real preceding response. Render-only checks may leave model residency; it was explicitly unloaded and empty residency confirmed.

The Gemma v2 command selects exactly the twenty non-gold inputs, disjoint from the ten promoted observations. Do not replace it with an all30 invocation or duplicate the reused gold10. No v1 observations are reused for exploratory sampling.

## Provider reservation and approval

The exact `google/gemini-3.5-flash` / `google-ai-studio` standard/default route was refreshed through public GET metadata at 2026-10-25T19:17:43.492171+00:00. The route was available and supported the required parameters/output allowance. Advertised input/output rates were $0.0000015 and $0.000009 per token. Full-context reservation uses 1,048,576 input tokens plus the full 16,384 output allowance: **$1.7203200 per physical call**, settling to reported actual cost. Unknown charges retain reservations.

The unchanged $10 ceiling has **$3.52909660 accounted** and **$6.47090340 remaining**. Earlier unknown-charge holds remain included; no ledger bytes changed. Each provider command needs separate approval of its concrete invocation and allowance. Its configured 120-call maximum is not a promise of funding: existing budget/dependency guards can stop earlier. Native execution also waits for a further execution request; this task prepares commands only.

Coverage is retained in the named results volume at `results/provider-matrix-exploratory-coverage-20261025.json`. The public preparation bundle also includes its exact snapshot. For a fresh execution environment, restore that snapshot to the named results volume and recheck current metadata; do not treat an old catalog snapshot as guaranteed future pricing or availability.

## Exact commands — prepared, not approved

Run from the repository root after the respective execution approval. These are four separate invocations; none was executed by this preparation.

### native v1 — 30 primaries

```sh
HW01_CONTEXT_LENGTH=49152 make hw01-run MODE=native ARGS='--config config/matrix.yaml --stage matrix --model local --prompt v1 --sampling exploratory-16384 --run-id matrix-native-v1-exploratory-20261025-72'
```

### native v2 — 20 primaries

```sh
HW01_CONTEXT_LENGTH=49152 make hw01-run MODE=native ARGS='--config config/matrix.yaml --stage matrix --model local --prompt v2 --sampling exploratory-16384 --input B02-S004-PO01 --input B02-S005-PO01 --input B02-S006-PO01 --input B02-S008-PO01 --input B02-S009-PO01 --input B02-S013-PO01 --input B02-S014-PO01 --input B02-S015-PO01 --input B02-S017-PO01 --input B02-S018-PO01 --input B02-S019-PO01 --input B02-S022-PO01 --input B02-S025-PO01 --input B02-S026-PO01 --input B02-S028-PO01 --input B02-S029-PO01 --input B02-S036-PO01 --input B02-S007-PO01 --input B02-S030-PO01 --input B02-S033-PO01 --run-id matrix-native-v2-exploratory-20261025-72'
```

### provider v1 — 30 primaries

```sh
make hw01-run MODE=provider ARGS='--config config/matrix.yaml --stage matrix --model provider-flash --prompt v1 --sampling exploratory-16384 --coverage results/provider-matrix-exploratory-coverage-20261025.json --allow-server-context --allow-provider --run-id matrix-provider-v1-exploratory-20261025-72'
```

### provider v2 — 30 primaries

```sh
make hw01-run MODE=provider ARGS='--config config/matrix.yaml --stage matrix --model provider-flash --prompt v2 --sampling exploratory-16384 --coverage results/provider-matrix-exploratory-coverage-20261025.json --allow-server-context --allow-provider --run-id matrix-provider-v2-exploratory-20261025-72'
```

## Offline aggregation and evidence

When the native v2 continuation is complete, evaluate its twenty records with the original ten-record source and `--sampling-aliases config/matrix-sampling-aliases.json`. Retain the source run name and IDs. The evaluator reports canonical grouping alongside original source sampling; duplicate gold observations remain errors.

```sh
make hw01-evaluate ARGS='native-v2-gold-t02-p090-20261025 matrix-native-v2-exploratory-20261025-72 --sampling-aliases config/matrix-sampling-aliases.json'
```

The named-volume originals are available on this workstation. Fresh checkouts must restore the diagnostic archive first and use `hw01-evaluate-restored --source-dir ...` with the same alias file; continuation and source records must reside in one isolated evaluation tree. Do not overwrite original exports or relabel source records.

Preparation checks include original-source byte preservation, exact adapter payload equality, membership source hashes, unchanged quality, local render admission, public provider route/rates, unchanged accounting and empty final native residency. Full implementation verification passed 777 tests, lint/format, strict types, frozen-gold validation and preflight; the expanded alias/archiving suite passed 39 focused tests, including ambiguity/target-control rejection and real CLI grouping/overlap cases. No extraction, paid reservation or model download occurred.

The preparation bundle contains the full 240-slot membership, reuse evidence, local admission records, public provider catalog/coverage and literal command file. It is retained under `results/submission/matrix-exploratory-20261025-preparation/` and selected by `exploratory-preparation` for archival. Compact archive indexes/receipts belong in Git; raw preparation files remain ignored.


The [verified preparation archive](../../archive-index/e41f816c5f1933d951b15b95dc871c12c56ee4c6e6d3837b75291cf0746407e5.json), [Garage receipt](../../archive-index/e41f816c5f1933d951b15b95dc871c12c56ee4c6e6d3837b75291cf0746407e5.remote.json) and [restore verification](../../archive-index/e41f816c5f1933d951b15b95dc871c12c56ee4c6e6d3837b75291cf0746407e5.verification.json) preserve the checked membership and original source evidence. Every restored payload matched its source, and the alias-aware evaluation reproduced exactly.
