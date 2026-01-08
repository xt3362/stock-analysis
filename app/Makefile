format:
	uv run ruff format . --config=pyproject.toml

lint:
	uv run ruff check . --fix --config=pyproject.toml

typecheck:
	uv run pyright

test:
	uv run pytest

check: format lint typecheck test

dashboard:
	PYTHONPATH=. uv run streamlit run src/interfaces/streamlit/market_regime_dashboard.py

help:
	@echo "Available commands:"
	@echo "  make format     - Format the code using ruff"
	@echo "  make lint       - Lint the code using ruff and apply fixes"
	@echo "  make typecheck  - Type check the code using pyright"
	@echo "  make test       - Run tests using pytest"
	@echo "  make check      - Run all checks (format, lint, typecheck, test)"
	@echo "  make dashboard  - Launch market regime analysis dashboard"
	@echo "  make help       - Show this help message"
