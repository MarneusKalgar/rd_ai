# Native Gemma v2 sampling diagnostic

**Subsequent reuse decision:** the [checked continuation preparation](matrix-exploratory-preparation.md)
promotes only the compatible temperature-0.2/top_p-0.90 gold10 into the required
matrix through an explicit sampling-ID map. Original diagnostic exports, scores
and archive membership remain unchanged. Earlier statements below about matrix
coverage describe the state when those experiments were recorded.

## Scope and authorization — 25 October 2026

The user requested gold10 runs varying temperature first, then top_p. This
separate diagnostic uses frozen v2 and the existing native Gemma artifact. It
does not modify the required 240-observation matrix or approve provider work,
other prompts, remaining20 continuations, examples or behavioral correction.

| Profile | Temperature | top_p | Gold inputs | Source |
| --- | ---: | ---: | ---: | --- |
| Reference | 0 | 1 | 10 | Reuse `matrix-native-v2-gold-20261024-72` |
| Temperature 0.2 | 0.2 | 1 | 10 | `native-v2-gold-t02-p100-20261025` |
| Temperature 0.5 | 0.5 | 1 | 10 | `native-v2-gold-t05-p100-20261025` |
| top_p 0.95 | 0.2 | 0.95 | 10 | `native-v2-gold-t02-p095-20261025` |
| top_p 0.90 | 0.2 | 0.90 | 10 | `native-v2-gold-t02-p090-20261025` |

These are 40 new observations and ten reused reference observations. The
temperature-0.2/top_p-1 run is reused as the top_p sweep's reference. Fixing
temperature at 0.2 makes nucleus-sampling changes interpretable; changing top_p
only under greedy decoding would not be a useful diversity experiment.

## Frozen controls

- Instructions: `prompts/v2.txt`, SHA-256
  `6a03379937695a2e5b127d292fc6ddb2301c9048b730ca3f9982d6c6443d155b`.
- Existing `gemma4:e4b-it-qat` artifact, digest
  `ee665637121887cf3befff38abbb1be4ee117c7db867d97a67e29049ecd7e15f`.
- Native Ollama 0.40.7; Python, admission, evaluation and export in Docker.
- Context 49,152; output allowance 16,384; thinking=false.
- Same ten approved gold inputs, schema, input representation, tokenizer,
  deadlines and bounded retry/correction policy as the reference.
- Sequential profiles and documents. All initial full requests checked before
  execution; actual correction requests must still pass admission separately.
- No provider requests, paid reservations, model downloads or Docker Ollama.

The exact profiles are in `config/native-sampling-sweep.yaml`. The ordinary
matrix defaults and frozen prompt/data files are unchanged. Diagnostic IDs are
distinct from required matrix sampling IDs, even where numeric settings agree.

## Execution and interpretation

Execution was started after verifying the empty native residency, installed
digest, exact runtime and reference tokenizer identity. All 40 initial requests
passed render-only admission; no one-token generation probes were used.

Each setting receives one gold10 pass. Settings are executed in the declared
order, without repeated trials, counterbalancing or a fixed cross-backend seed.
Results can suggest sensitivity but cannot establish a statistically stable
optimum or separate sampling from all cache/order effects. Gold10 remains
development data, not held-out accuracy. Compare errors and supported/contradicted
rows alongside the aggregate score; do not select outputs individually by score.

## Verified results

All four new profiles completed gold10 and passed export/record checks. The
temperature-0/top_p-1 reference is reused, not regenerated. Failures remain in
their original records and score denominators.

| Temperature | top_p | Correct / comparisons | Gold accuracy | Final valid | Exact docs | Extra rows | Processing time |
| ---: | ---: | --- | ---: | --- | ---: | ---: | --- |
| 0 | 1 | 198/2766 | 7.16% | 10/10 | 1 | 303 | 14m 00s |
| 0.2 | 1 | 198/2614 | 7.57% | 10/10 | 1 | 284 | 13m 02s |
| 0.5 | 1 | 193/2366 | 8.16% | 10/10 | 1 | 253 | 10m 55s |
| 0.2 | 0.95 | 192/2958 | 6.49% | 10/10 | 1 | 327 | 13m 11s |
| 0.2 | 0.9 | 197/2214 | 8.90% | 10/10 | 1 | 234 | 11m 46s |

Processing times sum per-input measured durations and exclude setup/load time.
Output lengths and row counts differ, so these durations do not isolate sampler
overhead or a change in hardware throughput.
The primary denominator penalizes extra ordered rows: it is not fixed at the
342 gold field paths when predictions return extra rows. Compare the numerator,
extra rows and expected-present/null subsets before describing an improvement.

| Temperature | top_p | Expected-present correct | Expected-null correct | Supported rows | Contradicted rows | Unknown rows |
| ---: | ---: | --- | --- | ---: | ---: | ---: |
| 0 | 1 | 103/197 | 95/145 | 19 | 306 | 12 |
| 0.2 | 1 | 103/197 | 95/145 | 24 | 280 | 14 |
| 0.5 | 1 | 97/197 | 96/145 | 5 | 169 | 113 |
| 0.2 | 0.95 | 97/197 | 95/145 | 19 | 224 | 118 |
| 0.2 | 0.9 | 103/197 | 94/145 | 9 | 247 | 12 |

### Row-selection sensitivity by document

| Temperature | top_p | S016 rows (gold 1) | S032 rows (gold 13) | S040 rows (gold 11) | S044 rows (gold 3) |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 0 | 1 | 67 | 101 | 157 | 3 |
| 0.2 | 1 | 67 | 82 | 157 | 3 |
| 0.5 | 1 | 67 | 76 | 31 | 104 |
| 0.2 | 0.95 | 7 | 79 | 157 | 109 |
| 0.2 | 0.9 | 67 | 100 | 89 | 3 |

At top_p=1, raising temperature from 0.2 to 0.5 reduces S040 from 157 returned
rows to 31, but increases S044 from three to 104. The higher primary score at
0.5 therefore does not establish more reliable selection across documents.
Its correct-field count falls from 198 to 193. Sampling sensitivity is visible;
a reliable production improvement is not established by this single-pass sweep.

### Retained evidence and boundaries

The [verified archive](../../archive-index/23d281f7e575e52faa44c4bb7318e0dc199613c42c2693c7ca8df5d92a9df561.json) preserves all five
source run exports, preparation/control evidence and the combined evaluations.
Its [Garage receipt](../../archive-index/23d281f7e575e52faa44c4bb7318e0dc199613c42c2693c7ca8df5d92a9df561.remote.json) records a full
GET verification. Detailed [comparison and per-document outcomes](../../results/restored/23d281f7e575e52faa44c4bb7318e0dc199613c42c2693c7ca8df5d92a9df561/submission/native-sampling-20261025-evaluation/summary.json)
are available after the [standard retrieval workflow](../guides/archiving-results.md).
Use selection `native-sampling-gold` for original-source packaging; the archive
contains 50 diagnostic observations, comprising 40 new and ten reused outcomes.
The separate required matrix still has 120/240 observations covered.

The provider ledger remained byte-for-byte unchanged. No paid or provider
inference was performed. Native Gemma was unloaded and empty residency verified
after the sequence. Each profile has one measured pass; this is not a claim of
repeatability, statistical significance, unseen-document accuracy or an optimal
sampling policy. The same frozen prompt/gold/scorer was used throughout.

## Interaction follow-up — 25 October 2026

After reviewing the initial sweep, the user explicitly authorized one additional
gold10 pass at temperature 0.5/top_p 0.90. It uses
`config/native-sampling-interaction.yaml` and run ID
`native-v2-gold-t05-p090-20261025`, with all other frozen controls unchanged.
The existing 0.2/1, 0.5/1 and 0.2/0.9 observations are reused, not rerun. This
completes a two-temperature/two-top_p comparison with ten new and thirty reused
diagnostic observations. It adds no required matrix membership or provider spend.

Follow-up status: complete and verified. Every setting below uses the same
ten development gold inputs, frozen v2 and the same execution controls. The first
three rows reuse saved runs; only the last row is new.

| Temperature | top_p | Correct / comparisons | Gold accuracy | Final valid | Exact docs | Extra rows | Processing time |
| ---: | ---: | --- | ---: | --- | ---: | ---: | --- |
| 0.2 | 1 | 198/2614 | 7.57% | 10/10 | 1 | 284 | 13m 02s |
| 0.5 | 1 | 193/2366 | 8.16% | 10/10 | 1 | 253 | 10m 55s |
| 0.2 | 0.9 | 197/2214 | 8.90% | 10/10 | 1 | 234 | 11m 46s |
| 0.5 | 0.9 | 132/2366 | 5.58% | 9/10 | 1 | 253 | 18m 14s |

| Temperature | top_p | S016 rows (gold 1) | S032 rows (gold 13) | S040 rows (gold 11) | S044 rows (gold 3) |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 0.2 | 1 | 67 | 82 | 157 | 3 |
| 0.5 | 1 | 67 | 76 | 31 | 104 |
| 0.2 | 0.9 | 67 | 100 | 89 | 3 |
| 0.5 | 0.9 | 67 | failed | 89 | 109 |

Retained failures in the new profile:

- `B02-S032-PO01`: truncated; 16384 output tokens; 1 physical attempt(s). The failed output receives zero gold matches.

A failed output contributes its expected gold fields to the denominator, but has no valid predicted extra rows to penalize. Earlier schema-valid catalog over-selections incurred those extra-row penalties. A higher headline percentage after a failure therefore does not establish better extraction; inspect validity and correct expected fields separately.

The follow-up used 10 physical requests;
its expected-present/null field counts are
84/197
and 48/145.
Extra-row penalties remain part of the primary score. A higher percentage alone
does not establish that more expected fields are correct or that selection is
reliable across documents. Single-pass differences may include sampling noise;
this completes the small grid, not a repeated-trial interaction estimate.

The separate [interaction archive](../../archive-index/9ebc3c9de8f21b61ff57cfcf7e039f7534ebcf3fb66e1485447e8608a65d6a63.json) retains
all four source runs, preparation and comparison evidence. The [Garage receipt](../../archive-index/9ebc3c9de8f21b61ff57cfcf7e039f7534ebcf3fb66e1485447e8608a65d6a63.remote.json)
and [restore verification](../../archive-index/9ebc3c9de8f21b61ff57cfcf7e039f7534ebcf3fb66e1485447e8608a65d6a63.verification.json)
record exact preservation. The [full comparison](../../results/restored/9ebc3c9de8f21b61ff57cfcf7e039f7534ebcf3fb66e1485447e8608a65d6a63/submission/native-interaction-20261025-evaluation/summary.json)
is available after restoration. No original sweep archive was replaced. Provider
accounting is unchanged; Gemma was unloaded with empty residency verified.
No further inference or extension is authorized.
