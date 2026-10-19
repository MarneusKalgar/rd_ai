.PHONY: check validate-gold preflight

check:
	docker compose run --build --rm checks sh -c 'ruff check --no-cache . && ruff format --check --no-cache . && mypy --cache-dir=/tmp/mypy-cache && pytest && python -m hw01 validate-gold && python -m hw01 preflight'

validate-gold:
	docker compose run --build --rm checks

preflight:
	docker compose run --build --rm checks python -m hw01 preflight
