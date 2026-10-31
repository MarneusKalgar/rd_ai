# Qwen v1/v2 gold10 diagnostic

## Authorized scope and controls

On 26 October 2026 the user requested the optional 7.3.3 diagnostic with both
frozen prompts: the same gold10 once with v1, then once with v2. Twenty new
native observations are authorized. No remaining20, provider calls, examples,
behavioral semantic checks or automatic model replacement are included. The
completed 240-observation matrix remains unchanged.

The selected native artifact is `qwen3.5:9b-q4_K_M`, digest
`56671c2ab9385f9cfcb404638e32cd62d88e3501d44822208363c010179a3c90`.
Registry manifest SHA-256 and installed digest match. Downloaded artifacts total
6,550,825,550 bytes; this includes the projector even though the diagnostic uses
text only. Ollama remains 0.40.7. Model weights execute through the existing
native desktop server; application code and verification execute in Docker.

`config/qwen-gold.yaml` selects a separate model/pin identity. It retains
49,152 context, 16,384 output tokens, temperature 0, top_p 1, thinking=false,
the frozen schema/input representation/scorer and the matrix's existing bounded
retries, correction and deadlines. V1/v2 instruction hashes remain unchanged.

Qwen's artifact presets include presence_penalty=1.5 and top_k=20. The diagnostic
explicitly uses presence_penalty=0, frequency_penalty=0, repeat_penalty=1 and
top_k=40 for both prompts; these overrides accompany admission and generation,
enter request fingerprints and remain visible in evaluation identities. Saved
Gemma runs retain their original defaults and identities. Model-specific
tokenization, training and template behavior remain differences; this is not
a parameter-matched or perfectly controlled compute comparison.
These measurements describe this frozen diagnostic profile, not Qwen's best
achievable result with its own presets or further tuning.

## Non-generating preparation

The installed Qwen vocabulary and merge sequence match the
[published Qwen3.5-9B tokenizer reference](https://huggingface.co/Qwen/Qwen3.5-9B/blob/main/tokenizer.json), SHA-256
`5f9e4d4901a92b997e463c1f46055088b6cca5ca61a6522d1b9f64c4bb81cb42`.
The application reconstructs Qwen's byte-level BPE from installed GGUF metadata,
using the Qwen3.5 split pattern and byte alphabet. It takes the larger raw/NFC
count and adds two boundary slots; it does not reuse Gemma counts. Unsupported
metadata fails closed. Every actual request, including any correction, must
pass its own admission check.

All twenty initial requests passed full render-only admission and were checked
against the reference counter without generating answers. Maximum prompt bound
was 16,127 tokens; minimum remaining headroom after the 16,384 output allowance
was 16,641 tokens. The selected 49,152 context was applied successfully. Ollama
reported 7,297,931,673 bytes for both loaded size and GPU allocation. That is
runtime-reported allocation at preparation, not measured peak system memory or
proof of identical hardware throughput. The model was unloaded after preparation.
The provider ledger remained byte-for-byte unchanged.

## Verified terminal results

Both authorized Qwen gold10 phases reached attempted terminal records. Required
matrix membership remains **240/240**; these twenty optional observations do not
replace Gemma or add required coverage. Comparators are the existing baseline
gold10 observations, not newly generated outputs or best exploratory settings.
Gold-only operations below are recomputed from the same ten inputs for every
model. Historical all30 latency/cost totals are not mixed into this table.

| Model | Prompt | Valid / 10 | Correct / comparisons | Field accuracy | Exact docs | Extra rows | Missing rows | Processing time |
| --- | --- | ---: | --- | ---: | ---: | ---: | ---: | --- |
| local | v1 | 10 | 164/3494 | 4.69% | 0 | 394 | 0 | 18m 41s |
| local | v2 | 10 | 198/2766 | 7.16% | 1 | 303 | 0 | 14m 00s |
| provider-flash | v1 | 10 | 278/342 | 81.29% | 1 | 0 | 0 | 2m 13s |
| provider-flash | v2 | 10 | 342/342 | 100.00% | 10 | 0 | 0 | 1m 18s |
| qwen | v1 | 8 | 103/406 | 25.37% | 0 | 8 | 24 | 26m 33s |
| qwen | v2 | 8 | 112/366 | 30.60% | 1 | 3 | 24 | 26m 19s |

For v1, Qwen's percentage is higher than Gemma's while matched fields fall from 164 to 103. This is not a net gain in matched gold fields. Extra-row penalties change the denominator, and truncated outputs lose their expected matches without becoming successful short extractions.

For v2, Qwen's percentage is higher than Gemma's while matched fields fall from 198 to 112. This is not a net gain in matched gold fields. Extra-row penalties change the denominator, and truncated outputs lose their expected matches without becoming successful short extractions.

Processing time sums input durations, including bounded correction/retries and
excluding setup/model loading. Host activity, caching and model-specific
tokenization differ; this is not a controlled hardware-throughput benchmark.
Extra rows add wrong comparisons to the score denominator. Review matched-field
counts, null/present accuracy and row errors together with headline percentages.

The original post-run helper compared serialized runtime capability lists by
order. It stopped after all ten v1 records were saved. The verifier was corrected
to compare the typed capability sets, preserving identical runtime/model identity;
v1 was verified/exported without replay and only the authorized v2 observations
were then generated. The original error and continuation evidence are archived.
No prompt, sampling, model option or scorer changed between phases.

### Qwen operations and field populations

| Prompt | First valid | Final valid | Calls | Corrected inputs | Present fields | Null fields | p50 seconds | p95 seconds |
| --- | ---: | ---: | ---: | ---: | --- | --- | ---: | ---: |
| v1 | 8 | 8 | 10 | 0 | 66/197 | 37/145 | 20.40 | 731.38 |
| v2 | 8 | 8 | 10 | 0 | 72/197 | 40/145 | 19.53 | 730.34 |

Retained Qwen failures:

- V1: S032 truncated after 12m11s; S040 after 11m41s.
- V2: S032 truncated after 12m10s; S040 after 11m42s.

Each failure used one physical request and reached 16,384 output tokens. No
valid extraction was claimed for the incomplete response. Raw responses and
precise timings remain in the archived records.

### Ordered-row cases and detection-only evidence

| Prompt | Input | Status | Returned rows | Gold rows |
| --- | --- | --- | ---: | ---: |
| v1 | B02-S016-PO01 | succeeded | 1 | 1 |
| v1 | B02-S032-PO01 | failed | — | 13 |
| v1 | B02-S040-PO01 | failed | — | 11 |
| v2 | B02-S016-PO01 | succeeded | 1 | 1 |
| v2 | B02-S032-PO01 | failed | — | 13 |
| v2 | B02-S040-PO01 | failed | — | 11 |

v1 detection-only row counts: `{"contradicted": 0, "supported": 1, "unknown": 17}`.

v2 detection-only row counts: `{"contradicted": 0, "supported": 1, "unknown": 12}`.

Diagnostics cover recognized source structures; unknown is not an error label.
They did not filter output, change scores or trigger corrections. Full regenerable
reports remain ignored; archived summaries retain their hashes and sizes.

## Evidence and review gate

The provider ledger remained byte-for-byte unchanged. No provider inference was
performed; native API cost is zero, excluding machine/electricity/time. Qwen was
unloaded and empty residency verified after execution.

The [archive index](../../archive-index/c5cd35ac80b99061f5ecd53112d889b3212c5eaf5e89508d6d4b27683cc90114.json),
[Garage receipt](../../archive-index/c5cd35ac80b99061f5ecd53112d889b3212c5eaf5e89508d6d4b27683cc90114.remote.json) and
[restore verification](../../archive-index/c5cd35ac80b99061f5ecd53112d889b3212c5eaf5e89508d6d4b27683cc90114.verification.json) retain the
original records, installed/reference tokenizer metadata, preparation, diagnostic
drivers and evaluations. Every source/restored payload matched. Both Qwen
evaluation reports reproduced exactly; all six gold-only comparison populations
reproduced field counts and operational metrics from restored records. Baseline
aggregation before archival used the existing audited budget-only revision
exception; original policies and hashes remain visible. Archive selection:
`qwen-gold-comparison`.

The implementation snapshot retains source hashes and contents where permitted
by archive checks. Two unchanged credential-handling source files remain in Git
and are identified by hash only; archive credential checks were not weakened.

Gold10 is development evidence, not a held-out reliability estimate. One pass
per prompt cannot establish stability or attribute every difference to model
weights alone. Review the full comparison before choosing another intervention.
No remaining20, further sampling, model substitution, behavioral harness or
JEV/provider calls are automatically authorized.
