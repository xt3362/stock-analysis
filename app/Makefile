format:
	uv run ruff format . --config=pyproject.toml

lint:
	uv run ruff check . --fix --config=pyproject.toml

typecheck:
	uv run pyright

test:
	uv run pytest

check: format lint typecheck test

help:
	@echo "Available commands:"
	@echo "  make format     - Format the code using ruff"
	@echo "  make lint       - Lint the code using ruff and apply fixes"
	@echo "  make typecheck  - Type check the code using pyright"
	@echo "  make test       - Run tests using pytest"
	@echo "  make check      - Run all checks (format, lint, typecheck, test)"
	@echo "  make help       - Show this help message"
