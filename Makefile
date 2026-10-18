.PHONY: help hw01-check hw01-validate-gold
.DEFAULT_GOAL := help

help:
	@echo "hw01-check          Run HW-01 contract tests, lint and type checks in Docker"
	@echo "hw01-validate-gold  Validate the frozen HW-01 gold objects in Docker"

hw01-check:
	$(MAKE) -C hw-01 check

hw01-validate-gold:
	$(MAKE) -C hw-01 validate-gold
