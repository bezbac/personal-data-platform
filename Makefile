.DEFAULT_GOAL := run

lint:
	uv run ruff check
	uv run ty check
	uv run sqruff lint assets/
	pnpm -C observable format:check

check:
	uv run bdp check

run:
	uv run bdp materialize

serve:
	pnpm -C observable dev
