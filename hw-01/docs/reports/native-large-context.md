# Native Gemma: largest-input capacity diagnostic

**Evidence retrieval:** Bulk evidence is in the [submission-history archive](../../archive-index/31349837ab5acff7f512d02ef2ee56a93a7a2da63d01dd8a12ea85acd734288a.json). Follow the [restore instructions](../guides/archiving-results.md#historical-submission-evidence) before opening restored-file links. Original run IDs and export paths retain their historical meaning.

## Authorized scope

The user requested one run of S008, the largest recorded native v1 input, with
enough context and output capacity. This is a separate diagnostic, not a
replacement for the required matrix. Use unchanged v1, temperature 0, top_p 1,
thinking=false, 49,152 effective context and a 16,384-token output allowance.
S008 has **no approved gold**; report schema validity, runtime and row behavior,
not factual accuracy.

The earlier native v1/thinking-disabled admission counted 22,276 prompt tokens.
Adding 16,384 output tokens requires 38,660 tokens, exceeding the original
32,768 context. A 49,152 context gives headroom without loading the model's full
advertised 131,072 capacity. Actual requests and any correction still require
their own complete rendered-request admission.

The host has 17,179,869,184 bytes (16 GiB) of RAM. Metadata-only checks on
22 October 2026 confirmed native Ollama 0.40.7, the installed Gemma model's
131,072 context capability and support for thinking=false. The runner verifies
the pinned digest, loaded context and tokenizer before generation. Its saved
setup confirms effective 49,152 context and thinking disabled. Model-memory
values from `/api/ps` are residency observations, not peak whole-process memory.

Configuration: `config/gemma-large-context.yaml`. The working v2 draft and main
matrix settings remain unchanged. No provider calls or accounting changes are
part of this diagnostic. The implementation is the v1 runtime committed in
`e1ed2a3`; configuration and exact one-input scheduling were checked offline.

```sh
HW01_CONTEXT_LENGTH=49152 make hw01-run MODE=native ARGS='--config config/gemma-large-context.yaml --stage matrix --model local --prompt v1 --sampling baseline-16384 --input B02-S008-PO01 --run-id native-s008-49152-16384-20261022'
```

The override applies to this invocation; it does not edit desktop settings or
the main experiment file. The existing request timeout is 1,800 seconds, with
bounded transport retry/correction under the input deadline. Preserve any
truncation, timeout or invalid output rather than silently replaying the run.

Metadata and sampled residency are retained in the results volume at
`results/setup/native-s008-49152-16384-20261022/`. The operator retains the exact
plan, process log, configuration and outcome alongside the verified export.
Comparison to the earlier 32,768/4,096 run changes two controls and uses one
observation each; it cannot isolate the causal performance effect of context.

## Docker resource cleanup

While the native diagnostic ran, the user requested removal of obsolete Docker
Ollama resources. The stopped `rd-ai-hw01-ollama-1` container, the pinned
7.07 GB Ollama image and `rd-ai-hw01_ollama-models` volume (5.7 GB in Docker
Desktop) were removed. `rd-ai-hw01_results` and the native model directory were
preserved. The native diagnostic continues independently. These displayed
sizes do not establish how much host disk space Docker Desktop has reclaimed.

The optional Docker compatibility configuration remains in source; using its
explicit initialization command again would download the image and weights.
Native execution does not require these resources.

## Completed result — 22 October 2026

Run `native-s008-49152-16384-20261022` completed successfully on native
Ollama 0.40.7 with the pinned Gemma digest, effective context 49,152 and
thinking=false. One physical request, no correction/retry, no budget/dependency
stop and application exit 0. The raw response has no thinking content and finish
reason `stop`. Frozen schema validation passed; no partial JSON was repaired.

| Measurement | Earlier 32,768 context / 4,096 output | New 49,152 context / 16,384 output |
| --- | ---: | ---: |
| Result | Truncated | Schema-valid complete output |
| Input elapsed time | 182.903 s (3m 03s) | 519.550 s (8m 40s) |
| Reported output tokens | 4,096 | 15,592 |
| Complete returned lines | Not available | 207 |
| Approved gold | None | None |

The new admission bound was **22,276 prompt + 16,384 output = 38,660 tokens**,
within the loaded 49,152. The server reported 22,274 actual prompt tokens.
Its prompt evaluation took 56.517 seconds and generation 457.809 seconds,
about **34.1 generated tokens/second**. These timings are retained as server
measurements; model setup/load (5.966 seconds) is separate from input latency.
Do not interpret the two run times as isolated context-size overhead: both the
context and allowed/actual generated output changed.

Of the 207 returned rows, **13 have positive quantities and 194 have null
quantities**. This is an observable output property, not a new gold label or
factual accuracy score. It is consistent with the catalog-row selection concern
seen elsewhere in the v1 baselines and explains why complete JSON alone is
insufficient evidence of extraction quality. No approved expected output exists
for S008, so the shared evaluation correctly reports zero labeled cases and
no factual accuracy value.

The diagnostic demonstrates that native Gemma can admit this large complete
request and finish a long schema-conforming answer at the larger settings.
It does not establish that every corpus/correction request fits, that maximum
context is desirable, or that returning all these rows satisfies the task.
The working v2 draft and main configuration remain unchanged.

After completion, an empty `keep_alive: 0` unload request returned `unload`;
`/api/ps` confirmed no resident models. The desktop app and native weights remain
installed. No provider inference ran, and cumulative provider accounting remains
**$1.77332305**, including earlier unknown-charge holds.

The verified run and separate evaluation/comparison bundles are saved under
`results/submission/native-s008-49152-16384-20261022/` and
`results/submission/native-s008-49152-16384-20261022-evaluation/`.
The volume archive `results/matrix-runs/native-s008-49152-16384-20261022/`
retains configuration, plan/process logs, admission, setup/residency evidence,
evaluation and checksums. The post-run unload evidence is separately retained
under `results/setup/native-s008-49152-16384-20261022/unloaded.json`.
Fresh offline verification checks input/schema/prompt identities, controls,
admission and accounting; export payload hashes were independently checked.
