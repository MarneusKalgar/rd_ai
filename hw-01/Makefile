.PHONY: check validate-gold preflight setup-provider setup-local local-ready local-capacity storage-check down
.DEFAULT_GOAL := check

# ARGS carries explicit model/input/run selections; local is the safe default.
# MODE=provider selects the credentialed app and never starts Ollama.
ARGS ?=
MODE ?= local
RUN_SERVICE := local-run
ifeq ($(MODE),provider)
RUN_SERVICE := app
endif

.PHONY: run smoke plan-run budget-init budget-show export-run verify-export

# Make runs from hw-01/ (including calls routed from the root Makefile).
# Prefer local resource overrides; the tracked example keeps a fresh checkout usable.
# Override explicitly with: make COMPOSE_ENV_FILE=path/to/file <target>.
COMPOSE_ENV_FILE := .env.compose.example
ifneq ($(wildcard .env.compose),)
COMPOSE_ENV_FILE := .env.compose
endif
COMPOSE := docker compose --env-file "$(COMPOSE_ENV_FILE)"

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

# Six representative one-token probes in the current configuration; no model pull.
local-ready:
	$(COMPOSE) run --build --rm local-ready

# Optional full prepared-request pass. Its one-hour budget overrides the routine
# readiness deadline; these local diagnostics are not measured extraction results.
local-capacity:
	$(COMPOSE) run --build --rm -e HW01_SETUP_CAPACITY_SECONDS=3600 local-ready python -m extraction_service.runtime readiness --exhaustive

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

# Overlay only the submission subtree to copy reviewed output to the host.
# Raw logs, setup snapshots and the cumulative ledger stay in the named volume.
export-run:
	mkdir -p results/submission
	$(COMPOSE) run --build --rm --no-deps --volume "$(CURDIR)/results/submission:/app/results/submission" offline python -m extraction_service export-run $(ARGS)

verify-export:
	$(COMPOSE) run --build --rm --no-deps --volume "$(CURDIR)/results/submission:/app/results/submission:ro" offline python -m extraction_service verify-export $(ARGS)
