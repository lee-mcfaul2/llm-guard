.PHONY: install test test-integration test-conformance lint typecheck security build run clean

install:
	uv sync --all-extras

test:
	uv run pytest tests/unit/ -v

test-integration:
	uv run pytest tests/integration/ -m integration -v

test-conformance:
	uv run pytest tests/conformance/ -m conformance -v

lint:
	uv run ruff check src/ tests/

typecheck:
	uv run mypy src/

security:
	uv run bandit -r src/ -q

build:
	uv build

run:
	uv run python -m llm_guard_svc

clean:
	rm -rf dist/ build/ .pytest_cache/ .mypy_cache/ .ruff_cache/
