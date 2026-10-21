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
