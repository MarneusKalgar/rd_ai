# Native extraction evidence — 21 October 2026

For the separately approved 8,192-token follow-up on the large input, see the
[22 October output-allowance experiment](output-allowance-experiment.md).

**Native local smoke completed:** two schema-valid outputs and one explicitly
truncated output, all persisted and exported. Native mode/admission/application
handling are verified for the recorded configuration. Field accuracy and the
full experiment matrix are unmeasured. Provider live acceptance remains pending.

The current native configuration allows stable 0.40 patches starting at 0.40.7
following the desktop update on 22 October. These retained runs used 0.40.3;
their recorded identities and timing measurements are unchanged. See
[native runtime compatibility](native-ollama.md#runtime-identity-and-admission).

## Runtime and invocation

- Apple M2 Pro, 17,179,869,184 physical memory bytes (16 GiB), macOS 14.8.7.
- Existing Ollama desktop app **0.40.3**; it was not replaced or upgraded.
  Python ran in Docker and reached `http://host.docker.internal:11434`.
- `gemma4:e4b-it-qat`, Q4_0, same model digest as Docker:
  `ee665637121887cf3befff38abbb1be4ee117c7db867d97a67e29049ecd7e15f`.
- `/api/ps` confirmed 32,768 context, `llamacpp` runner and equal reported
  `size`/`size_vram`. A later snapshot reported both as 5,535,338,330 bytes;
  the initial empty-load manifest snapshot reported 3,223,228,250 bytes.
  These are reported model-memory observations, not total host memory use.
- Docker Ollama was stopped before native extraction; its weights and results
  volumes were preserved. The desktop app and its ChatGPT connection were retained.

```sh
make hw01-setup-native
make hw01-run MODE=native ARGS='--stage smoke --input B02-S030-PO01 --run-id native-short-20261021-67'
make hw01-smoke MODE=native ARGS='--run-id native-smoke-20261021-67'
```

Initialization pulled the missing local weights and verified their digest:
6,146,501,801 installed bytes, no inference or budget initialization. No cloud
model, provider inference, API-key usage or paid request was involved.

The short run succeeded in 26.400 seconds, one attempt, 1,163 input / 723 output
tokens. Its separate empty-load/setup step took 8.428 seconds. The three-document
run's empty-load/setup step took 5.238 seconds, outside the input durations below.
The same v1 prompt, schema, temperature 0, top_p 1, 4,096 output allowance and
1,800/7,205-second request/input bounds were used as in the earlier Docker run.

## Completed three-document run

| Input | Outcome | Attempts | Input / output tokens | Input duration | Prompt evaluation | Output evaluation |
| --- | --- | --- | --- | --- | --- | --- |
| B02-S030-PO01 | Schema-valid, one line | 1 | 1,163 / 723 | 26.283 s | 2.081 s | 15.891 s |
| B02-S026-PO01 | Schema-valid, 14 lines | 1 | 2,005 / 2,972 | 70.116 s | 2.467 s | 67.525 s |
| B02-S008-PO01 | Truncated at the configured output limit | 1 | 22,276 / 4,096 | 169.006 s | 56.415 s | 112.336 s |

Available output-evaluation rates were approximately 45.5, 44.0 and 36.5
tokens/second respectively. These measure output evaluation from the raw Ollama
timings, not end-to-end throughput. Reported prompt-cache counts were 0, 650
and 650 tokens. Input durations also include actual-request admission and other
coordinator work, so they exceed the model's response timings.

S008 finished with `done_reason: length` and outcome/reason `truncated`. Its
partial raw response and actual token/timing evidence are retained. The existing
policy does not correct truncated responses; no extra attempt, shortened input
or increased output allowance was introduced. Its failed extraction remains in
the denominator. Increasing the output allowance is a future explicitly scoped
experiment requiring a fresh context/budget check, not a repair of this result.

The manifest is `complete`: succeeded 2, failed 1, not_attempted 0,
`comparison_complete: true`, no dependency or budget stops. The application
returned extraction-failure status **1**, which Make wrapped as error 2. This
means all selected work completed with one extraction failure. It does not mean
all three extractions were valid or factually correct.

## Matched Docker observations

| Input | Earlier Docker CPU duration | Native duration | Observed duration ratio |
| --- | --- | --- | --- |
| S030 | 117.836 s | 26.283 s | About 4.48× |
| S026 | 442.022 s | 70.116 s | About 6.30× |
| S008 | Interrupted; no final record | 169.006 s, truncated | Unavailable |

The [earlier Docker run](extraction-smoke.md) used Ollama **0.40.6**, CPU
placement, a 10 GiB container ceiling and a Docker VM with about 11.67 GiB
available memory. Native used **0.40.3** and observed GPU placement. Model bytes,
schema, inputs, v1/baseline controls and context match, but this is not an
isolated measurement of Docker overhead or a general speedup guarantee:

- The Docker run overlapped offline checks and had documented resource pressure.
- Version, cache/warmth and processor placement differ. Native S026 also emitted
  fewer tokens (2,972 versus 3,493), so its latency ratio includes different work.
- There is one completed matched observation per input, no repetition or p95
  estimate, and no completed Docker S008 observation.
- Schema validity is not factual accuracy; no scoring or production model choice
  is established by these timings.

The observations support using the verified native option for subsequent Mac
experiments, with the local runtime selected explicitly. Keep Docker compatibility
checks and CPU measurements separate; do not merge their timings into one matrix.

## Durable and independently checked evidence

Both exported bundles were reloaded and byte/inventory-checked from fresh
network-disabled containers:

```sh
make hw01-export-run ARGS='native-short-20261021-67'
make hw01-verify-export ARGS='native-short-20261021-67'
make hw01-export-run ARGS='native-smoke-20261021-67'
make hw01-verify-export ARGS='native-smoke-20261021-67'
```

The [short export](../results/submission/native-short-20261021-67/) contains one
record; the [three-document export](../results/submission/native-smoke-20261021-67/)
contains all three, including the truncated result. Each includes its manifest,
schema, checkpoints, raw responses and file hashes. The interrupted Docker export
was preserved unchanged. Raw logs/configuration and sensitivity-check evidence
remain ignored under `results/smoke-runs/native-smoke-20261021-67/` with checksums.
Both native builds used configuration digest
`sha256:75bbdfc0ce7525e40d7376dde0f877d0d72c6860db465762bea824ee01c39573`.
The smoke image index digest was
`sha256:e65d2de5d7a5a841285b23046707ff67244d8ae933cc2aa9ac35234764fbacf1`.
Later local-setup readability cleanup and an extra mode-rejection test were
verified offline rather than rerunning these model requests.

Sections 6.7.1–6.7.2's native wiring and local comparison are exercised.
Section 6.7.3 (small Docker model smoke profile/CI jobs) is deferred at the
user's request. The complete 30-input
matrix, additional prompts/sampling, scoring/reporting and provider live smoke
are separate pending work; no further model invocation is scheduled.
