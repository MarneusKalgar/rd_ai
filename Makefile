.PHONY: check validate-gold preflight setup-provider setup-local local-ready local-capacity storage-check down
.DEFAULT_GOAL := help

.PHONY: answer-continuation-freeze answer-continuation-plan answer-continuation-export answer-continuation-check answer-continue
answer-continuation-freeze answer-continuation-plan answer-continuation-export:
	$(COMPOSE) -f compose.yaml -f compose.e03.yaml -f compose.e03-recovery.yaml -f compose.e03-continuation.yaml run --build --rm --no-deps answer-continuation-offline python tools/answer-continuation/continue_run.py $(patsubst answer-continuation-%,%,$@) $(ARGS)

answer-continuation-check:
	$(COMPOSE) -f compose.yaml -f compose.e03.yaml -f compose.e03-recovery.yaml -f compose.e03-continuation.yaml run --build --rm --no-deps answer-continuation-checks sh -c 'ruff check --no-cache tools/answer-continuation && ruff format --check --no-cache tools/answer-continuation && mypy --cache-dir=/tmp/mypy-continuation src tools/answer-recovery tools/answer-continuation && pytest tools/answer-continuation/test_continue.py tools/answer-recovery/test_recover.py'

answer-continue:
	$(COMPOSE) -f compose.yaml -f compose.e03.yaml -f compose.e03-recovery.yaml -f compose.e03-continuation.yaml run --build --rm --no-deps answer-continuation-provider python tools/answer-continuation/continue_run.py run $(ARGS)

.PHONY: answer-recovery-freeze answer-recovery-plan answer-recovery-check answer-recover answer-recovery-export
answer-recovery-freeze answer-recovery-plan answer-recovery-export:
	$(COMPOSE) -f compose.yaml -f compose.e03.yaml -f compose.e03-recovery.yaml run --build --rm --no-deps answer-recovery-offline python tools/answer-recovery/recover.py $(patsubst answer-recovery-%,%,$@) $(ARGS)

answer-recovery-check:
	$(COMPOSE) -f compose.yaml -f compose.e03.yaml -f compose.e03-recovery.yaml run --build --rm --no-deps answer-recovery-checks sh -c 'ruff check --no-cache tools/answer-recovery && ruff format --check --no-cache tools/answer-recovery && mypy --cache-dir=/tmp/mypy-recovery src tools/answer-recovery && pytest tools/answer-recovery/test_recover.py'

answer-recover:
	$(COMPOSE) -f compose.yaml -f compose.e03.yaml -f compose.e03-recovery.yaml run --build --rm --no-deps answer-recovery-provider python tools/answer-recovery/recover.py run $(ARGS)

.PHONY: answer-freeze answer-plan answer-metadata answer-run answer-check answer-export
answer-freeze answer-plan:
	$(COMPOSE) -f compose.yaml -f compose.e03.yaml run --build --rm --no-deps answer-offline python -m extraction_service.answering.cli $(patsubst answer-%,%,$@) $(ARGS)

answer-check:
	$(COMPOSE) -f compose.yaml -f compose.e03.yaml run --build --rm --no-deps answer-offline sh -c 'ruff check --no-cache . && ruff format --check --no-cache . && mypy --cache-dir=/tmp/mypy-cache && pytest tests/application/test_answers.py'

# Metadata is public catalog GET only. run requires both explicit paid/context flags.
answer-metadata answer-run:
	$(COMPOSE) -f compose.yaml -f compose.e03.yaml run --build --rm --no-deps answer-provider python -m extraction_service.answering.cli $(patsubst answer-%,%,$@) $(ARGS)

answer-export:
	mkdir -p results/submission/P03-E03-v1
	$(COMPOSE) -f compose.yaml -f compose.e03.yaml run --build --rm --no-deps answer-review python -m extraction_service.answering.cli export $(ARGS)

.PHONY: integration-trial integration-check integration-reproduce
integration-trial:
	mkdir -p results/submission/P03-I01-v1
	$(COMPOSE) -f compose.yaml -f compose.i01.yaml run --build --rm --no-deps integration-i01 python -m extraction_service.retrieval.integration_cli $(ARGS)

integration-check:
	$(COMPOSE) -f compose.yaml -f compose.i01.yaml run --build --rm --no-deps integration-i01 sh -c 'ruff check --no-cache . && ruff format --check --no-cache . && mypy --cache-dir=/tmp/mypy-cache && pytest tests/application/test_integration.py'

# Independent verification runs without any network or database/model mount.
integration-reproduce:
	$(COMPOSE) -f compose.yaml -f compose.i01.yaml build integration-i01
	docker run --rm --network none --read-only --tmpfs /tmp --cap-drop ALL --security-opt no-new-privileges:true --memory 2g --cpus 2 --volume "$(CURDIR)/compose.yaml:/app/compose.yaml:ro" --volume "$(CURDIR)/compose.i01.yaml:/app/compose.i01.yaml:ro" --volume "$(CURDIR)/Dockerfile:/app/Dockerfile:ro" --volume "$(CURDIR)/results/submission/P03-E01-v3:/app/results/submission/P03-E01-v3:ro" --volume "$(CURDIR)/results/submission/P03-E02-v1:/app/results/submission/P03-E02-v1:ro" --volume "$(CURDIR)/results/submission/P03-I01-v1:/app/results/submission/P03-I01-v1:ro" rd-ai-integration-i01:latest python -m extraction_service.retrieval.integration_reproduce $(ARGS)

# ARGS carries explicit model/input/run selections; native avoids implicit downloads.
# MODE=provider selects the credentialed app and never starts Ollama.
# MODE=native uses the existing desktop server; Python remains in Docker.
ARGS ?=
MODE ?= native
RUN_SERVICE := local-run
ifeq ($(MODE),provider)
RUN_SERVICE := app
endif
ifeq ($(MODE),native)
RUN_SERVICE := native-run
endif
ifeq ($(filter $(MODE),local provider native),)
$(error MODE must be local, provider or native)
endif

.PHONY: run smoke plan-run budget-init budget-show budget-raise export-run verify-export
.PHONY: evaluate
.PHONY: diagnose-rows
.PHONY: setup-native

# Make runs from the project root with one canonical recipe per action.
# Prefer local resource overrides; the tracked example keeps a fresh checkout usable.
# Override explicitly with: make COMPOSE_ENV_FILE=path/to/file <target>.
COMPOSE_ENV_FILE := .env.compose.example
ifneq ($(wildcard .env.compose),)
COMPOSE_ENV_FILE := .env.compose
endif
COMPOSE := docker compose --env-file "$(COMPOSE_ENV_FILE)"

# Reject stale shell/Make overrides and old Compose files before substitution.
ifneq ($(filter HW01_%,$(.VARIABLES)),)
$(error Retired HW01_ overrides detected; migrate all names to DI_)
endif
ifneq ($(shell rg -l '^[[:space:]]*(export[[:space:]]+)?HW01_' "$(COMPOSE_ENV_FILE)" 2>/dev/null),)
$(error Retired HW01_ names in COMPOSE_ENV_FILE; migrate all names to DI_)
endif

# Offline checks: build with locked dependencies, then run without network/model calls.
# Each && makes a failed gate stop the remaining checks.
check:
	$(COMPOSE) run --build --rm checks sh -c 'ruff check --no-cache . && ruff format --check --no-cache . && mypy --cache-dir=/tmp/mypy-cache && pytest && python -m extraction_service validate-gold && python -m extraction_service preflight'

# The checks image defaults to validating the frozen gold objects.
validate-gold:
	$(COMPOSE) run --build --rm checks

# Validate the complete public corpus/configuration without a live model.
preflight:
	$(COMPOSE) run --build --rm checks python -m extraction_service preflight

# --no-deps keeps provider preparation independent of Ollama; no provider inference.
setup-provider:
	$(COMPOSE) run --build --rm --no-deps app python -m extraction_service.runtime provider

# Explicit initialization may download missing pinned weights, then checks readiness.
# up applies changed server/resource settings and waits for the HTTP health check.
setup-local:
	$(COMPOSE) --profile local up -d --wait --wait-timeout 120 ollama
	$(COMPOSE) run --build --rm local-init

# Explicitly initialize missing pinned weights through the already running desktop app.
# No host installation, Docker Ollama startup or model generation is performed here.
setup-native:
	$(COMPOSE) run --build --rm --no-deps native-run python -m extraction_service.runtime initialize-native

# Explicit Docker diagnostic: representative one-token probes across configured variants.
local-ready:
	$(COMPOSE) run --build --rm local-ready

# Optional full prepared-request pass. Its one-hour budget overrides the routine
# readiness deadline; these local diagnostics are not measured extraction results.
local-capacity:
	$(COMPOSE) run --build --rm -e DI_SETUP_CAPACITY_SECONDS=3600 local-ready python -m extraction_service.runtime readiness --exhaustive

# Test persistent non-root storage without initializing/changing the budget ledger.
storage-check:
	$(COMPOSE) run --build --rm --no-deps app python -m extraction_service.runtime storage

# Remove containers/network only. Omitting -v preserves weights and results/accounting.
down:
	$(COMPOSE) --profile local down --remove-orphans

# Inference requires initialized local weights, or approved provider selections.
# No --allow-provider flag is added by Make. The operator must supply it explicitly.
run:
	$(COMPOSE) run --build --rm $(RUN_SERVICE) python -m extraction_service run $(ARGS)

smoke:
	$(COMPOSE) run --build --rm $(RUN_SERVICE) python -m extraction_service smoke $(ARGS)

# Planning and accounting use no network and cannot generate model responses.
plan-run:
	$(COMPOSE) run --build --rm --no-deps offline python -m extraction_service plan-run $(ARGS)

budget-init:
	$(COMPOSE) run --build --rm --no-deps offline python -m extraction_service budget-init $(ARGS)

budget-show:
	$(COMPOSE) run --build --rm --no-deps offline python -m extraction_service budget-show $(ARGS)

# Administrative action only: preserve reservations and audit the expected old cap.
budget-raise:
	$(COMPOSE) run --build --rm --no-deps offline python -m extraction_service budget-raise $(ARGS)

# Overlay only the submission subtree to copy reviewed output to the host.
# Raw logs, setup snapshots and the cumulative ledger stay in the named volume.
export-run:
	mkdir -p results/submission
	$(COMPOSE) run --build --rm --no-deps --volume "$(CURDIR)/results/submission:/app/results/submission" offline python -m extraction_service export-run $(ARGS)

# Read-only source/output evidence; diagnostic flags never trigger inference.
diagnose-rows:
	$(COMPOSE) build offline 1>&2
	$(COMPOSE) run --rm --no-deps --volume "$(CURDIR)/results/submission:/app/results/submission:ro" offline python -m extraction_service diagnose-rows $(ARGS)

.PHONY: assess-source
assess-source:
	$(COMPOSE) build offline 1>&2
	$(COMPOSE) run --rm --no-deps --volume "$(CURDIR)/results/submission:/app/results/submission:ro" offline python -m extraction_service assess-source $(ARGS)

verify-export:
	$(COMPOSE) run --build --rm --no-deps --volume "$(CURDIR)/results/submission:/app/results/submission:ro" offline python -m extraction_service verify-export $(ARGS)

# Saved-run scoring has no network, key, model loading or generation.
evaluate:
	$(COMPOSE) run --build --rm --no-deps offline python -m extraction_service evaluate $(ARGS)

.PHONY: archive-dirs archive-results verify-archive restore-results upload-archive download-archive evaluate-restored archive-store-init archive-store-up archive-store-down
archive-dirs:
	mkdir -p results/submission results/archives results/restored archive-index

# Network-disabled operations use read-only original evidence and isolated writable outputs.
archive-results: archive-dirs
	$(COMPOSE) run --build --rm --no-deps archive-offline python -m extraction_service.archiving create $(ARGS)

verify-archive: archive-dirs
	$(COMPOSE) run --build --rm --no-deps archive-offline python -m extraction_service.archiving verify $(ARGS)

restore-results: archive-dirs
	$(COMPOSE) run --build --rm --no-deps archive-offline python -m extraction_service.archiving restore $(ARGS)

evaluate-restored: archive-dirs
	$(COMPOSE) run --build --rm --no-deps --volume "$(CURDIR)/results/restored:/app/results/restored:ro" offline python -m extraction_service evaluate $(ARGS)

.PHONY: reproduce-report
reproduce-report: archive-dirs
	mkdir -p results/reproductions
	$(COMPOSE) run --build --rm --no-deps reproduce python -m extraction_service.evaluation.reproduce $(ARGS)

# Storage credentials are confined to the online helper; provider credentials are never loaded.
upload-archive: archive-dirs
	$(COMPOSE) run --build --rm --no-deps archive-online python -m extraction_service.archiving upload $(ARGS)

download-archive: archive-dirs
	$(COMPOSE) run --build --rm --no-deps archive-online python -m extraction_service.archiving download $(ARGS)

archive-store-init: archive-dirs
	$(COMPOSE) run --build --rm --no-deps --volume "$(CURDIR):/workspace" archive-offline python -m extraction_service.archiving --project-dir /workspace init-store

archive-store-up:
	$(COMPOSE) --profile archive up --build -d --wait --wait-timeout 120 garage

archive-store-down:
	$(COMPOSE) --profile archive stop garage

# Corrections reuse exact saved gold10 primaries; native mode and one-call guards
# are enforced in the command. The baseline submission mount is read-only.
.PHONY: correct-identifiers export-correction verify-correction evaluate-correction
correct-identifiers:
	$(COMPOSE) run --build --rm --no-deps --volume "$(CURDIR)/results/submission:/app/results/submission:ro" native-run python -m extraction_service.corrections run $(ARGS)

export-correction:
	mkdir -p results/submission
	$(COMPOSE) run --build --rm --no-deps --volume "$(CURDIR)/results/submission:/app/results/submission" offline python -m extraction_service.corrections export $(ARGS)

verify-correction:
	$(COMPOSE) run --build --rm --no-deps --volume "$(CURDIR)/results/submission:/app/results/submission:ro" offline python -m extraction_service.corrections verify $(ARGS)

evaluate-correction:
	$(COMPOSE) run --build --rm --no-deps --volume "$(CURDIR)/results/submission:/app/results/submission:ro" offline python -m extraction_service.corrections evaluate $(ARGS)

.PHONY: run-split export-split verify-split evaluate-split
run-split:
	$(COMPOSE) run --build --rm --no-deps --volume "$(CURDIR)/results/submission:/app/results/submission:ro" native-run python -m extraction_service.staged run $(ARGS)

export-split:
	$(COMPOSE) run --build --rm --no-deps --volume "$(CURDIR)/results/submission:/app/results/submission" offline python -m extraction_service.staged export $(ARGS)

verify-split:
	$(COMPOSE) run --build --rm --no-deps --volume "$(CURDIR)/results/submission:/app/results/submission:ro" offline python -m extraction_service.staged verify $(ARGS)

evaluate-split:
	$(COMPOSE) run --build --rm --no-deps --volume "$(CURDIR)/results/submission:/app/results/submission:ro" offline python -m extraction_service.staged evaluate $(ARGS)

.PHONY: help
.PHONY: validate-provenance-protocol assess-provenance
validate-provenance-protocol: archive-dirs
	$(COMPOSE) run --build --rm --no-deps --volume "$(CURDIR)/docs:/app/docs:ro" --volume "$(CURDIR)/results/restored:/app/results/restored:ro" reproduce python -m extraction_service validate-provenance-protocol $(ARGS)

assess-provenance: archive-dirs
	$(COMPOSE) run --build --rm --no-deps --volume "$(CURDIR)/docs:/app/docs:ro" --volume "$(CURDIR)/results/restored:/app/results/restored:ro" --volume "$(CURDIR)/results/submission:/app/results/submission" reproduce python -m extraction_service assess-provenance $(ARGS)

.PHONY: validate-evaluation-protocol evaluate-experiment
validate-evaluation-protocol: archive-dirs
	$(COMPOSE) run --build --rm --no-deps --volume "$(CURDIR)/results/restored:/app/results/restored:ro" reproduce python -m extraction_service validate-evaluation-protocol $(ARGS)

evaluate-experiment: archive-dirs
	$(COMPOSE) run --build --rm --no-deps --volume "$(CURDIR)/results/restored:/app/results/restored:ro" --volume "$(CURDIR)/results/submission:/app/results/submission" reproduce python -m extraction_service evaluate-experiment $(ARGS)

help:
	@echo "Document intelligence R&D: check, preflight, reproduce-report, run, archive-results"
	@echo "Commands run from this root; inference requires explicit scope and approval."

# E01 runs only against public sources/configuration, without network or ledger access.
.PHONY: prepare-encoder encode-references vector-store-up vector-store-stop evaluate-vectors
prepare-encoder:
	mkdir -p results/embedding-models results/submission
	$(COMPOSE) run --build --rm --no-deps --volume "$(CURDIR)/results/embedding-models:/app/results/embedding-models" vector-e02-online python -m extraction_service.retrieval.vector_cli prepare $(ARGS)

encode-references:
	$(COMPOSE) run --build --rm --no-deps vector-e02-offline python -m extraction_service.retrieval.vector_cli encode --output results/submission/P03-E02-v1/vectors.json $(ARGS)

vector-store-up:
	$(COMPOSE) --profile retrieval up -d qdrant-e02

vector-store-stop:
	$(COMPOSE) --profile retrieval stop qdrant-e02

evaluate-vectors:
	$(COMPOSE) run --build --rm --no-deps --volume "$(CURDIR)/compose.yaml:/app/compose.yaml:ro" --volume "$(CURDIR)/tests/application/test_vector_store.py:/app/tests/application/test_vector_store.py:ro" vector-e02 python -m extraction_service.retrieval.vector_cli $(ARGS)

.PHONY: validate-retrieval-protocol build-reference-index evaluate-retrieval
validate-retrieval-protocol build-reference-index evaluate-retrieval:
	mkdir -p results/submission
	$(COMPOSE) run --build --rm --no-deps --volume "$(CURDIR)/config:/app/config:ro" --volume "$(CURDIR)/data/references:/app/data/references:ro" --volume "$(CURDIR)/src:/app/src:ro" --volume "$(CURDIR)/results/submission:/app/results/submission" reproduce python -m extraction_service $@ $(ARGS)
