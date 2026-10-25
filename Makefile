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
	@echo "hw01-diagnose-rows Inspect saved row selection without inference or rescoring"
	@echo "hw01-archive-results Create and verify a copy-only archive (ARGS='--selection final-baselines')"
	@echo "hw01-verify-archive Verify a cached archive (ARGS='--index archive-index/<sha>.json')"
	@echo "hw01-restore-results Restore an archive into an isolated results/restored directory"
	@echo "hw01-upload-archive Upload to configured S3/Garage and verify with a download"
	@echo "hw01-download-archive Download and verify indexed evidence from S3/Garage"
	@echo "hw01-evaluate-restored Score restored evidence offline (ARGS includes --source-dir)"
	@echo "hw01-archive-store-init Generate private single-node Garage settings once"
	@echo "hw01-archive-store-up Start the optional local Garage bucket"
	@echo "hw01-archive-store-down Stop Garage; preserve its data volume"

.PHONY: hw01-archive-results hw01-verify-archive hw01-restore-results hw01-upload-archive hw01-download-archive hw01-evaluate-restored hw01-archive-store-init hw01-archive-store-up hw01-archive-store-down
hw01-archive-results hw01-verify-archive hw01-restore-results hw01-upload-archive hw01-download-archive hw01-evaluate-restored hw01-archive-store-init hw01-archive-store-up hw01-archive-store-down:
	$(MAKE) -C hw-01 $(patsubst hw01-%,%,$@)

.PHONY: hw01-run hw01-smoke hw01-plan-run hw01-budget-init hw01-budget-show hw01-budget-raise hw01-export-run hw01-verify-export hw01-setup-native hw01-evaluate hw01-diagnose-rows

hw01-run hw01-smoke hw01-plan-run hw01-budget-init hw01-budget-show hw01-budget-raise hw01-export-run hw01-verify-export hw01-setup-native hw01-evaluate hw01-diagnose-rows:
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
