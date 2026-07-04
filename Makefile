.PHONY: sync lint format typecheck test coverage build clean

sync:
	uv sync --all-groups

lint:
	uv run ruff check .

format:
	uv run ruff format .

typecheck:
	uv run ty check pygleif

test:
	uv run pytest tests/

coverage:
	uv run pytest tests/ --cov pygleif --cov-report term-missing --cov-report xml:coverage.xml

build:
	uv build

clean:
	rm -rf dist build *.egg-info .pytest_cache .ruff_cache .ty_cache .coverage coverage.xml
