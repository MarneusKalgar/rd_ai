# Extraction smoke evidence — 21 October 2026

**Status: interrupted at the user's request.** This is a partial local smoke,
not a completed three-document acceptance or the full 30-document experiment.
Provider inference was not run. Section 6.6 remains partially accepted.

## Invocation and preserved output

```sh
make hw01-smoke ARGS='--model local --run-id local-smoke-20261021-66'
```

The runner selected S030, S026 and S008 in that order, using the unchanged v1
prompt/schema and baseline sampling: temperature 0, top_p 1, 4,096 output tokens.
Request/input timeouts were 1,800/7,205 seconds. An empty cold model load took
63.921 seconds before the input measurements below.

| Input | Result | Physical attempts completed | Input/output tokens | Input duration |
| --- | --- | --- | --- | --- |
| B02-S030-PO01 | Schema-valid output, one line | 1 | 1,163 / 723 | 117.836 s |
| B02-S026-PO01 | Schema-valid output, 14 lines | 1 | 2,005 / 3,493 | 442.022 s |
| B02-S008-PO01 | Interrupted during first generation | 0 completed; one in flight | Final usage unavailable | No final input record |

Schema validity is not factual accuracy. No scoring against gold labels or
full-corpus quality measurement was performed. Completed requests report zero
local API charge; machine/time costs are excluded. The unfinished request's
token usage and outcome are unknown, not zero or an invented extraction failure.

The application handled SIGTERM through its interruption boundary and exited
130; Make wrapped this as error 2. The manifest remains `interrupted`, declares
all three intended inputs and contains two final records plus three checkpoints.
S008's checkpoint retains its admission evidence and no fabricated response.
There is no completed batch summary. The model server's compute returned to idle
(observed approximately 0.02% CPU) after cancellation; weights were preserved.

The [exported bundle](../results/submission/local-smoke-20261021-66/) was reloaded
and byte-checked from a fresh network-disabled app container:

```sh
make hw01-export-run ARGS='local-smoke-20261021-66'
make hw01-verify-export ARGS='local-smoke-20261021-66'
```

Verification reported two records and `state: interrupted`. The export contains
the authoritative schema, resolved experiment, intended identities/hashes,
setup/context evidence, checkpoints, raw completed responses and file hashes.
It does not contain the budget ledger, credentials or server logs. It has not
been staged or committed automatically.

## Runtime and admission observations

- Ollama 0.40.6, `gemma4:e4b-it-qat`, Q4_0; digest
  `ee665637121887cf3befff38abbb1be4ee117c7db867d97a67e29049ecd7e15f`.
- Docker CPU runtime, `size_vram: 0`, effective context 32,768. The VM reported
  12 CPUs and 12,526,108,672 memory bytes; Ollama's limit was 10 GiB.
- Initial admission bounds were S030 **1,165**, S026 **2,007**, and S008 **22,278**,
  including two conservative boundary slots. Each reserved the full 4,096-token
  output allowance. The two completed prompt counts matched the tokenizer count
  before the two-slot allowance exactly.
- S008 reached generation but slowed substantially. A sampled late log window
  advanced from 1,380 to 1,383 tokens over roughly 30 seconds while using several
  CPU cores. The user stopped the run; the 30-minute timeout was not reached.
- Offline verification/builds overlapped this smoke. These timings are diagnostic
  observations, not an isolated benchmark or a CPU/native-GPU comparison.
- The archived container snapshot reported `oom_killed: true`. Its event timing
  is not established by that snapshot, and the retained run-window server log
  has no matching OOM message. This run does not establish a clean memory-fit
  or performance acceptance; attribute resource events before later comparisons.

Raw Make/Ollama logs, image identity and Docker resource snapshots remain locally
ignored under `results/smoke-runs/local-smoke-20261021-66/`, with checksums.
The executing app image was
`sha256:5f2e6d812b0464f1dc27096b62a81d659373b899a315201a4f1e3cb2e2f54b57`.
Subsequent provider-stop/exit-status and composition readability changes were
verified offline; the interrupted smoke is evidence for this archived image.

## Remaining acceptance

The application implementation passed the final Docker gate: Ruff lint/format,
strict mypy, **566 tests**, all 10 frozen gold validations and 30-input preflight.
Ordinary tests performed no model inference or external HTTP. Their controlled
all-30 workflow verifies scheduling/persistence, not a real 30-document run.

The local three-document smoke is incomplete. A later run must be explicit and
use a new run ID; no automatic continuation or additional local generation is
scheduled. Provider smoke additionally needs verified actual-request counting
and route/pricing evidence, declared cumulative prior spend, and human approval
of the concrete invocation/cost estimate. The offline provider plan correctly
reports unavailable cost/ledger values as null, not zero. See
[running extractions](running-extractions.md) for those gates and commands.
