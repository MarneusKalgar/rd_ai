# Docker setup verification — 20 October 2026

**Historical evidence from 20 October:** infrastructure implemented; the exhaustive
local check was blocked on the then-current Docker allocation/deadlines.
No provider inference was performed.
The later [21 October representative baseline](local-runtime-comparison.md)
passed at 10 GiB and is archived separately; the observations below remain
historical evidence for the earlier configuration.
This is section 6.5 setup evidence, not the three-document extraction smoke,
accuracy evaluation, measured matrix or final submission acceptance.

## Pinned identities and resources

| Item | Observed value |
| --- | --- |
| Host | User-specified MacBook Pro M2 Pro, 16 GB unified memory |
| Docker | Desktop engine 29.8.2, ARM64 (`aarch64`) |
| Docker VM memory | 8,214,585,344 bytes, approximately 7.65 GiB |
| Ollama | 0.40.6, exact server version checked |
| Image index | `sha256:265409e1d931028a8f7d5a32bcbafddd7bffbc6cc629d77efe9560adf692a5e7` |
| ARM64 manifest | `sha256:fa0d4a1e2961c6343d1dd8b2a7c6609d1ae61bfa3032eb85667f9062d109e661` |
| Selected tag | `gemma4:e4b-it-qat` |
| Model manifest | `ee665637121887cf3befff38abbb1be4ee117c7db867d97a67e29049ecd7e15f` |
| Installed model bytes | 6,146,501,801 (about 6.15 GB decimal) |
| Initial model initialization | 248.108 seconds, including download/verification; image pull/build excluded |
| Host free disk | About 271 GiB before setup; 255 GiB after images, builds and weights |

The image was inspected with `docker buildx imagetools inspect`. The model pin
was checked against the SHA-256 of the public
[Ollama registry manifest](https://registry.ollama.ai/v2/library/gemma4/manifests/e4b-it-qat).
Installed/server identities then matched via actual Ollama metadata. Downloads
are additional to the image/build disk requirements; 6.15 GB is not the complete
setup disk footprint.

## Live model checks and actual blocker

Both empty model loads succeeded. `/api/ps` confirmed exact model/digest,
`size_vram: 0` and the requested context; placement was **CPU**.

| Context | Load evidence | Capacity evidence |
| --- | --- | --- |
| 16,384 | First load 21.917 s; later cold load 14.994 s. Reported loaded size 6,120,852,683 bytes. | Runtime rejected a 17,925-token input with HTTP 400: it exceeds 16,384 before adding the configured 4,096-token output allowance. |
| 32,768 | Cold load 18.481 s. Reported loaded size 6,154,407,115 bytes. Existing weights reused (`pulled: false`). | Four complete initial/correction fixture requests measured successfully. `B02-S004-PO01` initial request then exceeded the 120 s diagnostic request deadline. Full corpus capacity is **unverified**. |

The 32,768-context successful measurements were:

| Input | Request | Actual prompt tokens | Prompt + output allowance |
| --- | --- | ---: | ---: |
| B02-S002-PO01 | Initial | 1,194 | 5,290 |
| B02-S002-PO01 | Correction fixture | 1,643 | 5,739 |
| B02-S003-PO01 | Initial | 1,434 | 5,530 |
| B02-S003-PO01 | Correction fixture | 1,883 | 5,979 |

All requests included full instructions/schema/source. Correction fixtures used
invalid output `{}` plus every actual validator issue. Truncation and context
shifting were disabled. These were one-token local setup probes, not accepted
extractions. The largest prepared request **by bytes**, B02-S008-PO01's correction
fixture, is 56,189 UTF-8 message bytes; its token fit was not established.

At 32,768 context, Ollama's cgroup reported:

- `memory.max`: **7,516,192,768 bytes (7 GiB)**.
- `memory.peak`: **7,516,192,768 bytes**, reaching that ceiling.
- `memory.events max`: **1,316**, showing attempts to exceed the memory ceiling.
- `oom` / `oom_kill`: **0 / 0** at observation time.
- Current memory observations: 7,421,894,656 then 7,257,595,904 bytes.

These cgroup measurements include charged file cache and process memory. They
are distinct from `/api/ps` model allocation estimates and total host memory.
The evidence establishes memory pressure and a request timeout; it does not
establish that Gemma cannot run on this Mac or that memory was the sole cause of
the timeout. The model was explicitly unloaded after collecting the evidence.

The default context is now **32,768** because 16,384 is demonstrably insufficient.
That default is **not a claim of full readiness**. The original run checked all
prepared requests. The current `make hw01-local-ready` checks a representative
sample; `make hw01-local-capacity` runs the optional exhaustive diagnostic.
Neither replacement command was live-accepted by the historical evidence here.

To continue:

1. Adjust Docker Desktop's VM memory and the container memory ceiling together,
   leaving enough memory for the host and other containers. Increasing only the VM
   allocation leaves the container's 7 GiB ceiling in place.
2. Rebuild and run representative readiness. Current defaults allow 600 s per
   diagnostic and 900 s overall; the optional exhaustive command allows 3600 s
   overall. These setup deadlines do not change experiment execution deadlines,
   sampling, approved text or model selection.
3. Retain the report's actual coverage. Section 6.6 must admit each actual initial
   and correction request separately. Neither a representative sample nor an
   exhaustive finite fixture proves fit of arbitrary future correction evidence.

On 21 October, read-only observations of the user's longer exhaustive run showed
the previously timed-out 17,925-token prompt completing without truncation in
216.474 s of prompt processing; subsequent requests also progressed. This
establishes that the old 120 s diagnostic deadline was insufficient for that
request. It does not establish a complete passing run or eliminate memory pressure.
The representative path was subsequently run successfully at 10 GiB; its scope,
timings and memory pressure are recorded in the
[local runtime comparison record](local-runtime-comparison.md).

A different model or native GPU runtime requires its own explicit selection and
evidence. No fallback, model substitution or source shortening was used here.
Provider inference remains subject to explicit human approval.

## Isolation and durable storage acceptance

The runtime app completed full offline preflight over **30 inputs / 10 gold
objects**. It ran as UID 10001, with read-only root and a writable results volume.
Provider-only setup succeeded after `make hw01-down`, with no provider key/model
call, no Ollama startup and no model pull. `docker compose ps --all --services`
was empty after the one-shot provider containers exited.

Fresh app containers retained the same results UUID before/after Docker restart
and normal Compose shutdown. A **disposable test ledger**, located below
`results/setup/container-acceptance-fixture/`, retained:

- Declared fixture opening spend **0.25**, plus an unresolved reservation **0.10**.
- Accounted fixture total **0.35**, the same reservation ID and separate lock inode.
- Writable create/read/lock/fsync/atomic-replacement behavior as UID 10001.

The real `/app/results/budget-ledger.json` remained absent: no actual homework
spending was initialized or reset. The fixture values describe a storage test,
not provider charges. Weights remained installed across restart/shutdown, and
subsequent explicit model initialization reported `pulled: false`.

## Reproduction and evidence locations

See [Docker runtime setup](docker-runtime.md) for matching root/project commands,
volumes, pins, deadlines and exit codes. Runtime identity/readiness reports live
in the persistent results volume under `results/setup/`. The first download
report is preserved there as `initial-download.json`; `readiness.json` contains
the latest live probe. Reports have observed scope; they do not prove readiness
after future configuration/resource changes.

The final offline gate passed **506 tests**, Ruff lint/format, strict mypy,
validation of 10 gold objects and preflight over all 30 approved inputs.

Local session logs, not reviewer prerequisites:

- `/tmp/rd-ai-65-final-check.log` — final offline Docker gate.
- `/tmp/rd-ai-65-live-ready.log` — 16,384-context rejection.
- `/tmp/rd-ai-65-live-32768.log` — 32,768-context partial measurements/timeout.
- `/tmp/rd-ai-65-runtime-preflight.json` — runtime image's offline preflight.

The blocked live run preceded the addition of automatic bounded unloading after
capacity failure. That cleanup path and failure-preservation behavior are covered
by controlled tests; it does not change the recorded token/memory observations.
No live pytest test, native installation or provider inference was introduced.
