# Local runtime evidence and later comparisons

Preserve each selected setup run before another run replaces
`results/setup/readiness.json` in Docker's results volume. Keep raw logs and
machine-specific snapshots under the ignored host directory
`hw-01/results/setup-runs/<run-id>/`; keep concise results and their limitations
in this document. The host copy also survives ordinary container/volume cleanup.
It remains a local copy, not an off-machine backup.

## Recorded baseline — 21 October 2026

Run ID: `2026-10-21T081542Z-docker-cpu-10g-representative`.
The report's observation timestamp is the workflow start:
**11:15:42 Europe/Kiev** (`08:15:42 UTC`).

| Setting or observation | Value |
| --- | --- |
| Host | User-reported M2 Pro MacBook Pro, 16 GB unified memory |
| Runtime | Docker CPU, 12 CPUs available; Docker engine 29.9.1, ARM64 |
| Docker VM memory | 12,526,108,672 bytes, about 11.67 GiB |
| Ollama memory ceiling | 10,737,418,240 bytes, 10 GiB |
| Ollama version | 0.40.6 |
| Model | `gemma4:e4b-it-qat`; pinned digests in the report and `ollama-model.json` snapshot |
| Context | 32,768 tokens |
| Sampling | `v1` / `baseline`, temperature 0, top-p 1; full output allowance 4,096 tokens |
| Probe generation | One output token per diagnostic; truncation/context shifting disabled |
| Deadlines | 600 seconds per diagnostic; 900 seconds overall |
| Outcome | `ready`, command exit 0; six representative requests passed |
| Coverage | Three inputs × initial/correction fixture; 6 of 60 prepared requests |
| Model load | 61.538 seconds |
| Context diagnostics | 733.949 seconds, about 12 min 14 sec |
| Largest measured request | 22,725 prompt tokens + 4,096 allowance = 26,821 tokens |
| Memory peak | 10 GiB; reached the container ceiling |
| Memory events | `max: 2499`, `oom: 0`, `oom_kill: 0`; Docker `OOMKilled: false` |
| Installation/results | Existing weights reused; no download, prior storage identity retained |
| Provider inference | None |

Selected measurements:

| Input | Initial prompt tokens | Correction fixture tokens | Largest required context, including output |
| --- | ---: | ---: | ---: |
| B02-S008-PO01 | 22,276 | 22,725 | 26,821 |
| B02-S026-PO01 | 2,005 | 2,454 | 6,550 |
| B02-S030-PO01 | 1,163 | 1,612 | 5,708 |

The Ollama container was recreated immediately before this run. Weights were
already on disk; OS/file caches were not cleared. Later probes could reuse
prompt caches. The large initial prompt's logged processing time was 307.019 s;
its HTTP request took about 366 s. These are distinct observations, not
interchangeable latency measurements.

The source worktree was uncommitted at this run. Its base HEAD was
`068900c285bfee8ca6b076d0e760d17d8864c9c9`; HEAD alone does not identify the code
used. The exact runtime image ID and SHA-256 hashes of runtime source, config,
prompts and schemas are retained in the archive. The readiness report identifies
the selected inputs by SHA-256. Later changes must be compared with those hashes.

## Archive contents

The run directory contains:

- `make.log`: complete build/command output and the reported outcome.
- `ollama.log`: timestamped server logs from the recreated container, including
  individual request timing, prompt processing and cache behavior.
- `readiness.json` and `installation.json`: exported persistent setup evidence.
- `observations.json`: command, exit code, host/VM/container limits, exact image
  identity, source revision/dirty state, deadlines and post-run memory counters.
- `experiments.yaml` and `ollama-model.json`: public configuration snapshots.
- `runtime-artifact-hashes.json`: hashes of the files actually inside the app image.
- `SHA256SUMS`: checksums for the eight evidence files above.

Checksums verify accidental changes to the saved files; they are not signed
attestation. Exporting this run compared the volume's report with the original
command output and rejected a mismatch. Raw snapshots are ignored by Git;
this summary is the reviewer-facing record. No keys, host environment dumps,
original workbooks or private preparation mappings belong in the archive.

Current setup commands still replace the latest report. The dated export above
was explicit; automatic per-run archival is not yet implemented. Export and
label subsequent runs before starting another one if their evidence is needed.

## How to compare later runs

1. Keep the model digest/quantization, schema, prompt, input hashes, context,
   sampling, output allowance and selected request sequence identical. Record
   Ollama version and whether the execution backend changes.
2. Compare matching per-request measurements. A six-probe sample and a sixty-probe
   exhaustive pass have different scopes; their aggregate durations cannot
   establish a speedup. Earlier deadline failures are useful operational history,
   not complete latency samples.
3. Separate model load, prompt processing, output generation and total request
   duration. Match cold/warm and prompt-cache conditions where practical, and
   label conditions that were not controlled. Record competing host workloads
   and memory pressure; these were not fully controlled in this baseline.
4. For a speed claim, repeat the same workload and report a median and range.
   For Docker CPU versus native GPU, describe it as a comparison of execution
   setups: both hardware acceleration and runtime placement change.
5. Evaluate full extraction results against the same frozen gold labels to compare
   quality. One-token readiness does not measure extraction accuracy, full output
   latency or sustained throughput. Actual initial/correction request admission
   remains part of section 6.6.

This baseline establishes sampled runtime/context readiness under 10 GiB.
Memory pressure persists, and no measured 9-to-10 GiB speedup is established.
See the [historical setup evidence](docker-setup-verification.md) for earlier
failures and [runtime setup](docker-runtime.md) for commands and report scope.
