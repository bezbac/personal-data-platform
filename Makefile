.DEFAULT_GOAL := run

lint:
	uv run ruff check
	uv run ty check
	uv run sqruff lint assets/

check:
	uv run bdp check

run:
	uv run bdp materialize
