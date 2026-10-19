.PHONY: check validate-gold preflight

check:
	docker compose run --build --rm checks sh -c 'ruff check --no-cache . && ruff format --check --no-cache . && mypy --cache-dir=/tmp/mypy-cache && pytest && python -m extraction_service validate-gold && python -m extraction_service preflight'

validate-gold:
	docker compose run --build --rm checks

preflight:
	docker compose run --build --rm checks python -m extraction_service preflight
