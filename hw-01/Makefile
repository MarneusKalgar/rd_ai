.PHONY: check validate-gold

check:
	docker compose run --build --rm checks sh -c 'ruff check --no-cache . && ruff format --check --no-cache . && mypy --cache-dir=/tmp/mypy-cache && pytest && python -m hw01 validate-gold'

validate-gold:
	docker compose run --build --rm checks
