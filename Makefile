.PHONY: help hw01-check hw01-validate-gold hw01-preflight
.DEFAULT_GOAL := help

help:
	@echo "hw01-check          Run HW-01 contract tests, lint and type checks in Docker"
	@echo "hw01-validate-gold  Validate the frozen HW-01 gold objects in Docker"
	@echo "hw01-preflight      Verify configuration and the complete HW-01 corpus offline"

hw01-check:
	$(MAKE) -C hw-01 check

hw01-validate-gold:
	$(MAKE) -C hw-01 validate-gold

hw01-preflight:
	$(MAKE) -C hw-01 preflight
