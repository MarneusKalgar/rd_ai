# Native Ollama with Python in Docker

Section 6.7 adds an explicit native mode to the existing extraction runner.
The Ollama desktop app serves the model; Python, dependencies, checks and
record/export handling stay in Docker. The ChatGPT/Ollama connection is
independent of the HW application's HTTP connection. HW-01 uses the local
Gemma model directly and does not use an Ollama cloud model or account credits.

## Runtime identity and admission

| Mode | Endpoint from Python container | Runtime policy | Model pin |
| --- | --- | --- | --- |
| `local` | `http://ollama:11434` | Docker Ollama 0.40.6 | `config/ollama-model.json` |
| `native` | `http://host.docker.internal:11434` | Stable 0.40.x, patch >= 7 | `config/ollama-native.json` |

Both configurations select `gemma4:e4b-it-qat` and the same exact model digest.
Docker keeps its exact server version and immutable image pin. Native mode uses
`server_version_policy: compatible_patch`: `server_version` is the minimum
reviewed patch in that major/minor series. Stable 0.40.7 and newer 0.40 patches
are admitted without editing code/configuration after each desktop auto-update.
Older patches, a different major/minor series and prerelease/build suffixes stop
before loading or generation and require compatibility review. There is no
automatic fallback to Docker and no replacement of the installed desktop app.

An allowed version still has to pass the installed metadata, model digest,
tokenizer, loaded context and per-request render-only checks below. A patch
number alone does not prove compatibility. Every run retains its observed
runtime version; request admission is bound to that exact composed identity.
Changing versions between runs can change measurements, so compare recorded
versions explicitly. Controlled tests simulate later patches; they are not live
measurements of unreleased versions. For a fixed native benchmark, change the
policy to `exact` and manage app updates for that measurement period.

The desktop version deliberately differs from the Docker baseline. The
[0.40.7 request definitions](https://github.com/ollama/ollama/blob/v0.40.7/api/types.go)
and [chat handler](https://github.com/ollama/ollama/blob/v0.40.7/server/routes.go)
provide the render-only flag and explicit truncate/shift controls. The handler
returns rendered evidence before completion. Installed metadata, completion
capability, exact weights, tokenizer and loaded context are checked at runtime.
Missing render-only evidence prevents the extraction request.

On 22 October 2026 the native compatibility baseline was updated to the installed
desktop server's 0.40.7 version, after checking those required API controls in
the release source. The model digest is unchanged. The recorded 21 October
smoke runs used 0.40.3 and remain evidence for that version; they are not
0.40.7 measurements.

Native composition reuses the borrowed HTTP client, adapter, coordinator,
full-request token admission, validation, deadlines and persistence. An actual
correction is admitted with its real invalid response and validation evidence.
The model cannot silently shorten the approved input to fit. Setup/load time,
effective context, loaded memory placement and tokenizer hash are retained in
the manifest; each attempt retains its native runtime version and model digest.
Docker initialization evidence is not reused as native installation evidence.

## Commands

Start the existing Ollama desktop app. Its version endpoint must be reachable
from the Python container. Override `HW01_NATIVE_OLLAMA_BASE_URL` in
`.env.compose` only when the app uses another address/port. No provider dotenv
file or credential is injected into the native service, and it has no Docker
Ollama dependency. Keep the HTTP service local; the Docker Desktop host route
was verified without changing the app's bind address.

From the repository root:

```sh
# Explicitly initialize missing pinned weights; no model generation.
make hw01-setup-native

# One approved short input through full admission, extraction and persistence.
make hw01-run MODE=native ARGS='--stage smoke --input B02-S030-PO01 --run-id native-short-20261021'

# Separate three-document acceptance invocation; creates a new run directory.
make hw01-smoke MODE=native ARGS='--run-id native-smoke-20261021'

# Export and revalidate saved records without executing a model.
make hw01-export-run ARGS='native-smoke-20261021'
make hw01-verify-export ARGS='native-smoke-20261021'
```

Run IDs above are examples and cannot be reused. Native initialization can pull
missing weights and verifies their resolved digest; extraction never pulls or
substitutes a model. Initialization writes `results/setup/native-installation.json`
in the existing results volume, leaving Docker's `installation.json` separate.
Neither setup nor native inference initializes or resets provider accounting.

Before a live native run, stop the Docker Ollama service to release its resident
model memory. Preserve the weights/results volumes. Run runtime comparisons
sequentially and preserve each run's complete identity, settings and outcomes.
Use the existing `MODE=local` commands for portable Docker execution.

## Comparison and acceptance

Compare the same approved documents, model bytes, prompt, sampling, full output
allowance and effective context. Keep CPU Docker and native measurements in
separate tables. Confirm actual placement from `/api/ps` or `ollama ps`; native
mode alone does not establish GPU use. A nonzero `size_vram` establishes GPU
or mixed placement, not necessarily that every operation executes on the GPU.
See the [official placement explanation](https://docs.ollama.com/faq#how-can-i-tell-if-my-model-was-loaded-onto-the-gpu).

Separate setup/model-load time from request latency. Raw response envelopes
retain available prompt/evaluation timings and token counts, enabling token-rate
calculations without another inference call. Disclose version, cache/warmth,
host load and other uncontrolled differences. Two completed Docker smoke inputs
provide two matched observations, not a full-corpus benchmark or an isolated
measurement of Docker overhead. The interrupted Docker third input remains
interrupted even if native execution later completes it.

The [testing strategy](../quality/testing-strategy.md#docker-native-ollama-and-ci-responsibilities)
keeps ordinary Docker checks model-free. Native controlled tests cover identity,
correction, initialization separation, absent weights, unsupported rendering and
context/version/digest mismatch rejection. Native live evidence and performance
claims require a recorded run; controlled HTTP tests do not establish them.
Section 6.7.3's optional small Docker model CI profile/job is deferred at the
user's request. It does not
replace full adapter acceptance or the required two-prompt/two-sampling matrix.

See [recorded native extraction evidence](../reports/native-runtime-verification.md) for the
completed short and three-document runs, the retained truncation and comparison limits.

## Explicit thinking profile — 7.2

The initial full-corpus native baseline used the model default: thinking was
true in installed metadata and all 30 saved response envelopes. Six requests
exhausted 4,096 tokens in thinking before returning any final answer. After
reviewing both baselines, the user accepted disabling thinking and rerunning
all 30 native v1/baseline inputs. Keep the original run as a separate diagnostic;
reuse the unchanged completed provider baseline.

The local model entry in `config/experiments.yaml` sets **`thinking: false`**.
This maps to top-level **`think: false`** on both render-only admission and every
Ollama generation/correction. It does not change the installed desktop app,
weights, input, schema, prompt, sampling or output allowance. Omitted/null
thinking retains runtime defaults for historical configurations. The option is
Ollama-specific and is rejected on provider model entries; it is not a shared
provider reasoning setting.

Before loading, composition verifies an explicit value against installed
`/api/show` thinking metadata. Unsupported or absent metadata stops before
loading/generation. Setup records requested/effective/default controls;
admission includes the control and binds it into the request fingerprint.
Aggregation keeps different thinking profiles separate. Historical exports
remain byte-identical and still reload with the optional field absent.

See [Ollama thinking controls](https://docs.ollama.com/capabilities/thinking)
and the pinned [0.40.6 request/show definitions](https://github.com/ollama/ollama/blob/v0.40.6/api/types.go).
Both the portable runtime's request schema and the installed native model's
metadata support the boolean control. No Docker Ollama service was started to
perform this check; actual thinking-disabled behavior is verified by the new
native run's raw envelopes. Controlled tests establish request/evidence plumbing,
not real model compliance or an extraction-quality improvement.
