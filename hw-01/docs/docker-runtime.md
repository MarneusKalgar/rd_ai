# Docker runtime setup (plan 6.5)

Docker Desktop with Compose and Make are the only host prerequisites. Python,
uv and locked application dependencies run in containers. This setup introduces
no provider inference command. **Provider inference requires explicit human
approval** before the later section 6.6 smoke or experiment runs.

## Commands

Run from the repository root; omit `hw01-` inside `hw-01/`.

| Command | Effect |
| --- | --- |
| `make hw01-check` | Network-isolated Ruff, mypy, pytest, gold validation and preflight. No weights/key needed. |
| `make hw01-preflight` | Check all public configuration and approved artifacts offline. |
| `make hw01-setup-provider` | Build the app, validate provider selection/artifacts and test results storage. No HTTP, credentials, Ollama or downloads. |
| `make hw01-setup-local` | Start pinned Ollama, explicitly initialize pinned Gemma if absent, then load/context diagnostics. |
| `make hw01-local-ready` | Recheck prior installation, load and representative context probes. Never pulls a missing model. |
| `make hw01-local-capacity` | Optional slow diagnostic: check all prepared requests, with a one-hour overall deadline. |
| `make hw01-storage-check` | Verify non-root create/lock/read/atomic replacement; print persistent storage ID. |
| `make hw01-down` | Remove HW containers/network; retain both named volumes. |

Local setup/readiness exit **0** for the selected request checks, **2** for setup,
identity or protocol errors, and **3** for a recorded resource/capacity blocker.
After a capacity blocker, setup requests a bounded model unload to release memory
while retaining weights. If unloading fails, the report retains the original
blocker and asks for `make down`.
Make also fails on nonzero exit; its own shell status can be 2. JSON reports
identify the underlying blocker. A responding server or successful download alone
is not model readiness. Inspect `docker compose logs ollama` inside `hw-01/`
when setup fails. Resolve the failure and rerun the explicit command.

`make hw01-run`, the inference CLI, pricing/ledger initialization and three-document
extraction smoke remain section 6.6. Setup diagnostics are not experiment results.

## Images, selection and isolation

The `runtime` Docker target contains locked production dependencies and tracked
source/config/prompts/schema/data, runs as UID/GID **10001**, and defaults to offline
preflight. It omits test tools. The independent `checks` target includes them and
retains `network_mode: none`. Both use a read-only root with temporary `/tmp`;
only the runtime mounts results. The allowlist build context excludes host `.env`,
private preparation, original workbooks, weights and generated results.

The provider setup uses only `app --no-deps`. Ollama and its helpers have the
`local` profile. No Ollama port is published to the host. This prevents collisions
with a later native installation. Cloud features are disabled in the container.
Native Ollama is an optional, separate exercise: no host installation is automatic,
and its endpoint/runtime identity must remain `ollama-native` in measured runs.

The Compose image is pinned to an immutable multi-platform digest. ARM64 support
was verified. `config/ollama-model.json` pins the tag, full registry manifest digest
and server version. Setup verifies the experiment's explicit local selection
against that pin, checks installed bytes, completion capability and server version,
and records the image reference supplied by Compose. It refuses a changed digest,
version or image relative to `results/setup/installation.json`. Changes require
review of the pins/evidence; setup never substitutes a different model.

The app records the configured image reference; host Docker image inspection is
its provenance check, rather than remote attestation of arbitrary HTTP servers.
Ollama's Docker container uses CPU here; GPU/native results must be recorded
separately. See [Ollama Docker instructions](https://docs.ollama.com/docker).

## Configuration and deadlines

| Source | Scope |
| --- | --- |
| `config/experiments.yaml` | Explicit candidate models, prompts, common sampling, execution policy. Listing a model never starts it. |
| `config/ollama-model.json` | Reviewed local model digest and server version. |
| `compose.yaml` | Immutable image, internal endpoint, profiles, volumes and server resources. |
| `.env.compose` / `.env.compose.example` | Compose interpolation controls for resource allocation and setup deadlines. Make prefers the local file, falling back to the tracked example. |
| `HW01_CONTEXT_LENGTH` | Compose substitution, default **32768**. Passed to the server and setup verifier; independent of common sampling. |
| `HW01_OLLAMA_MEMORY_LIMIT` | Compose memory ceiling, default **7g**; the Docker VM must have additional memory for the app/engine. The recorded local override uses **10g**. |
| `HW01_SETUP_*` in the setup container | Compose forwards only allowlisted wait/pull/load/measurement controls to validated settings. No helper dotenv file. |
| `ApplicationSettings` | Service URLs and optional secret from process environment or an explicitly present HW `.env`; unchanged by setup. |

For a fresh checkout, copy `hw-01/.env.compose.example` to `hw-01/.env.compose`
and edit the resource/deadline values for the machine. The local file is ignored
by Git and excluded from images. Make passes the selected file through Compose's
`--env-file`; override its path with `make COMPOSE_ENV_FILE=path/to/file <target>`
inside `hw-01/` (or pass the variable to a root `hw01-*` target). Shell variables
take precedence, so `HW01_CONTEXT_LENGTH=32768 make hw01-setup-local` still works.
Relative override paths are resolved from `hw-01/`, including root Make invocations.
See [Compose interpolation and precedence](https://docs.docker.com/compose/how-tos/environment-variables/variable-interpolation/).

Keep Compose controls separate from the application's strict `.env` file.
The runtime image does not copy or mount either file. Only `app` reads `.env`
through Compose's optional `env_file`
as runtime environment values; a missing file is allowed. Checks and local
helpers receive no provider key. Provider setup does not require a key and does
not invoke a model even when a key is present. The existing `.env.example`
describes application settings; it does not authorize inference or initialize
budget state. See [Compose environment-file semantics](https://docs.docker.com/compose/how-tos/environment-variables/set-environment-variables/).

File roles differ: `--env-file .env.compose` supplies values for `${...}` in
`compose.yaml`; `app.env_file: .env` supplies application environment variables
inside that one container. Loading a Compose file does not forward all its keys
to every service. Model/image pins and sequential-execution settings remain in
versioned configuration. API paths belong to adapters, not env files.

When invoking Compose directly inside `hw-01/`, include
`docker compose --env-file .env.compose ...` (or `.env.compose.example` when no
local override exists). After changing server memory/context, apply the new
configuration with:

```sh
docker compose --env-file .env.compose --profile local up -d --wait --wait-timeout 120 ollama
```

Compose recreates the service if needed, preserving named volumes. Updating the
file alone does not change an existing container. The Docker Desktop VM memory
allocation is a separate host setting.

Defaults: HTTP request 5 s, overall HTTP-ready wait 60 s (poll 1 s), pull 1800 s,
empty model load 300 s, representative diagnostics 900 s overall / 600 s per request.
The optional `local-capacity` target sets the overall diagnostic deadline to 3600 s;
this is a limit, not a promise that all checks finish in an hour. Override setup
bounds explicitly with `docker compose run -e HW01_SETUP_...` when necessary.
Compose startup has its own 120 s wait. Server load timeout is 5 minutes,
parallelism and loaded-model count are both one, and keep-alive is 10 minutes.
A repeated initialization checks the verified installation without re-pulling.
Concurrent setup fails with an explicit lock error rather than waiting forever.

## Persistent results and weights

Compose project `rd-ai-hw01` owns these Docker named volumes:

- **`rd-ai-hw01_ollama-models`** → Ollama `/root/.ollama` (weights/manifests).
- **`rd-ai-hw01_results`** → app `/app/results` (all results and accounting).

The image provisions `/app/results` for UID 10001; Docker initializes an empty
named volume with that ownership. Model selections, stages and future invocations
all mount the same results directory. It includes `budget-ledger.json`, its
separate `.lock` and the directory needed for atomic replacement. Setup only
writes within `results/setup/`; it never initializes, truncates, reconciles or
resets real budget state. Missing/corrupt ledgers still block paid work under the
existing budget policy. Unresolved reservations remain accounted.

`storage-check` creates a persistent UUID, obtains a nonblocking setup lock, and
exercises file creation, atomic replacement, fsync and reading as the app user.
Running it in two fresh containers must return the same UUID and `reused: true`
on the second invocation. This checks storage; it is not a budget initialization.

For example, inspect setup evidence without running any model:

```sh
cd hw-01
docker compose run --rm --no-deps app cat results/setup/installation.json
docker compose run --rm --no-deps app cat results/setup/readiness.json
docker compose run --rm --no-deps app cat results/setup/capacity-exhaustive.json
```

The default shutdown preserves volumes. **Do not use `down -v`** for ordinary
shutdown: it destroys weights and accounting. A Docker Desktop factory reset can
also destroy them; export required results/accounting before that operation.
Named volumes live in Docker's VM, not in the repository or app image.

## What readiness proves

1. Public corpus/configuration/contract preflight passes.
2. The exact pinned model is installed and matches prior initialization evidence.
3. An empty `/api/generate` loads it at explicit `num_ctx`. `/api/ps` must report
   the same name/digest and effective context. `size`/`size_vram` show model
   allocation/placement; they are not whole-process peak resident memory.
4. Local one-token `/api/chat` diagnostics measure complete initial requests and
   correction fixtures for **three representative inputs per prompt/sampling
   variant**: smallest, middle and largest initial messages by UTF-8 bytes, with
   input ID breaking ties. Selected documents retain corpus order; small corpora
   are deduplicated. The current configuration selects **6 of 60 requests**.
   Each includes full instructions, schema and source; correction fixtures add
   invalid output `{}` plus all actual validator issues. Nothing is shortened.
5. The pinned server accepts `truncate: false` and `shift: false`. The runtime's
   actual `prompt_eval_count` plus the experiment's **full output allowance** must
   fit the effective context. No bytes/characters-to-token estimate establishes fit.
   Input overflow, missing counts, protocol errors or deadlines fail closed.

Byte size selects a spread of examples; it does not establish token fit for
unmeasured requests. A successful sample has `scope: representative`,
`selected_request_count: 6`, `prepared_request_count: 60`, and
`all_prepared_requests_verified: false`. `token_capacity_verified` covers only
the selected requests. On the first selected-request failure, readiness stays
blocked. This is a setup check, not a corpus-wide admission certificate.

Use `make hw01-local-capacity` for the optional exhaustive pass. It checks all
prepared requests instead of assuming the largest byte string has the most
tokens. Both commands preserve partial measurements on a blocker. The exhaustive
report goes to `results/setup/capacity-exhaustive.json`, leaving the representative
`readiness.json` separate. Do not run both simultaneously: setup holds a shared
lock. This change does not alter an already running diagnostic container.

**Correction coverage is finite.** The `{}` fixture is not a worst-case bound for
an arbitrary future invalid response or its validation messages. Section 6.6 must
admit **every actual initial and correction request** against context with full evidence and output
allowance, using a non-generating tokenizer/admission method; it must not
silently truncate. Do not insert these one-token setup probes as hidden extra
requests inside the coordinator's generation/correction/deadline bounds.
A `ready` setup report covers only the enumerated selected
requests, not all possible corrections, output accuracy or the extraction matrix.

These one-token calls and cold loads are local setup diagnostics, never provider
requests, extraction smoke outputs, prompt-quality scores or latency samples.
Initial download, cold load and context-check duration remain separate from later
per-document measurements. Memory evidence must also identify Docker's VM limit,
container limit and actual cgroup/process memory at the applied context.

Protocol reference: the pinned
[Ollama 0.40.6 request types](https://github.com/ollama/ollama/blob/v0.40.6/api/types.go)
define truncation/shift controls. See the
[loaded-model API](https://docs.ollama.com/api/ps) and
[context configuration](https://docs.ollama.com/context-length) for server evidence.

## Live verification

The dated setup evidence and any remaining blocker are recorded separately in
[Docker setup verification](docker-setup-verification.md).
The passing representative baseline and evidence-retention/comparison rules are
recorded in [local runtime comparison](local-runtime-comparison.md).
Ordinary pytest uses
controlled transports, temporary storage and fake clocks; it does not download
weights or contact a live runtime. Live setup is an explicitly selected Make
operation. No live pytest marker/test has been introduced.
