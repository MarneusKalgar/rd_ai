.PHONY: help hw01-check hw01-validate-gold hw01-preflight hw01-setup-provider hw01-setup-local hw01-local-ready hw01-local-capacity hw01-storage-check hw01-down
.DEFAULT_GOAL := help

help:
	@echo "hw01-check          Run HW-01 contract tests, lint and type checks in Docker"
	@echo "hw01-validate-gold  Validate the frozen HW-01 gold objects in Docker"
	@echo "hw01-preflight      Verify configuration and the complete HW-01 corpus offline"
	@echo "hw01-setup-provider Check provider artifacts/storage without model calls"
	@echo "hw01-setup-local    Start Ollama, initialize pinned Gemma and diagnose readiness"
	@echo "hw01-local-ready    Check local identity/load and representative context probes"
	@echo "hw01-local-capacity Check all prepared local requests (optional, slow)"
	@echo "hw01-storage-check Verify persistent non-root results storage"
	@echo "hw01-down          Stop HW-01 containers; preserve results and model weights"
	@echo "hw01-run           Execute selected work (MODE=local/provider/native, ARGS='...')"
	@echo "hw01-setup-native  Initialize pinned weights through the existing desktop app"
	@echo "hw01-smoke         Run the explicit three-document extraction smoke"
	@echo "hw01-plan-run      Describe selections and available cost bounds offline"
	@echo "hw01-budget-init   Declare prior spend explicitly (ARGS required)"
	@echo "hw01-budget-show   Reopen cumulative spending without resetting it"
	@echo "hw01-budget-raise  Explicitly raise an existing cap with retained audit evidence"
	@echo "hw01-export-run    Export saved evidence to results/submission (ARGS=run-id)"
	@echo "hw01-verify-export Recheck exported byte hashes and records (ARGS=run-id)"
	@echo "hw01-evaluate      Score saved terminal runs offline (ARGS='run-id ...')"

.PHONY: hw01-run hw01-smoke hw01-plan-run hw01-budget-init hw01-budget-show hw01-budget-raise hw01-export-run hw01-verify-export hw01-setup-native hw01-evaluate

hw01-run hw01-smoke hw01-plan-run hw01-budget-init hw01-budget-show hw01-budget-raise hw01-export-run hw01-verify-export hw01-setup-native hw01-evaluate:
	$(MAKE) -C hw-01 $(patsubst hw01-%,%,$@)

hw01-check:
	$(MAKE) -C hw-01 check

hw01-validate-gold:
	$(MAKE) -C hw-01 validate-gold

hw01-preflight:
	$(MAKE) -C hw-01 preflight

hw01-setup-provider:
	$(MAKE) -C hw-01 setup-provider

hw01-setup-local:
	$(MAKE) -C hw-01 setup-local

hw01-local-ready:
	$(MAKE) -C hw-01 local-ready

hw01-local-capacity:
	$(MAKE) -C hw-01 local-capacity

hw01-storage-check:
	$(MAKE) -C hw-01 storage-check

hw01-down:
	$(MAKE) -C hw-01 down
