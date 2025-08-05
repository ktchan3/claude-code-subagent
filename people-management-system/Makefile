.PHONY: help install dev-install test lint format clean run-server run-client build

help: ## Show this help message
	@echo 'Usage: make [target]'
	@echo ''
	@echo 'Targets:'
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  %-20s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

install: ## Install production dependencies
	uv sync --no-dev

dev-install: ## Install development dependencies
	uv sync
	uv add --dev ruff black mypy pytest pytest-asyncio pytest-qt pre-commit

test: ## Run tests
	uv run pytest

test-coverage: ## Run tests with coverage
	uv run pytest --cov=server --cov=client --cov=shared --cov-report=html --cov-report=term-missing

lint: ## Run linting
	uv run ruff check .
	uv run mypy server client shared

format: ## Format code
	uv run ruff format .
	uv run black server client shared

format-check: ## Check if code is formatted
	uv run ruff format --check .
	uv run black --check server client shared

clean: ## Clean build artifacts
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -rf build/
	rm -rf dist/
	rm -rf .coverage
	rm -rf htmlcov/
	rm -rf .pytest_cache/
	rm -rf .mypy_cache/

run-server: ## Run the FastAPI server
	uv run uvicorn server.main:app --reload --host 0.0.0.0 --port 8000

run-client: ## Run the PySide6 client
	uv run python -m client.main

build: ## Build the project
	uv build

setup-db: ## Set up the database (requires database to be running)
	uv run alembic upgrade head

create-migration: ## Create a new migration (usage: make create-migration name=migration_name)
	uv run alembic revision --autogenerate -m "$(name)"

reset-db: ## Reset the database
	uv run alembic downgrade base
	uv run alembic upgrade head