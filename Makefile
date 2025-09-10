.PHONY: help install dev test lint format clean build run docker

# Default target
help: ## Show this help message
	@echo "Operato Runner - Development Commands"
	@echo "===================================="
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-15s\033[0m %s\n", $$1, $$2}'

# === Installation ===
install: ## Install production dependencies
	pip install -e .

install-dev: ## Install development dependencies
	pip install -e ".[dev,test,security]"

install-uv: ## Install with uv (recommended)
	uv pip install -e ".[dev,test,security]"

# === Development ===
run: ## Run the development server
	python main.py

run-minimal: ## Run with minimal configuration
	python main.py --no-redis --no-grpc

dev: ## Start development environment with auto-reload
	uvicorn src.main:app --reload --host 0.0.0.0 --port 8000

# === Testing ===
test: ## Run tests
	pytest

test-cov: ## Run tests with coverage
	pytest --cov=src --cov-report=html --cov-report=term

test-verbose: ## Run tests with verbose output
	pytest -v -s

test-fast: ## Run tests excluding slow ones
	pytest -m "not slow"

# === Code Quality ===
lint: ## Run linting (ruff + mypy)
	ruff check src tests
	mypy src

lint-fix: ## Fix linting issues
	ruff check --fix src tests
	black src tests

format: ## Format code with black
	black src tests

format-check: ## Check code formatting
	black --check src tests

security: ## Run security checks
	bandit -r src/
	safety check

# === Database ===
db-upgrade: ## Apply database migrations
	alembic upgrade head

db-downgrade: ## Rollback database migrations
	alembic downgrade -1

db-revision: ## Create new migration
	alembic revision --autogenerate -m "$(msg)"

db-reset: ## Reset database (development only)
	rm -f app.db
	alembic upgrade head

# === Build and Deploy ===
build: ## Build the package
	python -m build

clean: ## Clean build artifacts
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	find . -type d -name __pycache__ -delete
	find . -type f -name "*.pyc" -delete

# === Docker ===
docker-build: ## Build Docker image
	docker build -t operato-runner .

docker-run: ## Run Docker container
	docker run -p 8000:8000 -p 50051:50051 operato-runner

docker-compose: ## Run with docker-compose
	docker-compose up -d

docker-compose-minimal: ## Run minimal stack
	docker-compose -f docker-compose-minimal.yml up -d

# === Admin UI ===
ui-install: ## Install admin UI dependencies
	cd admin-ui && npm install

ui-dev: ## Start admin UI development server
	cd admin-ui && npm start

ui-build: ## Build admin UI for production
	cd admin-ui && npm run build

ui-test: ## Test admin UI
	cd admin-ui && npm test

# === Utilities ===
setup-dirs: ## Create runtime directories
	mkdir -p runtime/module_envs runtime/uploads runtime/logs runtime/temp

setup-pre-commit: ## Setup pre-commit hooks
	pre-commit install

check-deps: ## Check for dependency updates
	pip list --outdated

validate: ## Run all validation checks
	make lint
	make test
	make security

init: install-dev setup-dirs setup-pre-commit ## Initialize development environment

# === Environment Info ===
info: ## Show environment information
	@echo "Python version: $$(python --version)"
	@echo "Pip version: $$(pip --version)"
	@echo "Current directory: $$(pwd)"
	@echo "Virtual environment: $${VIRTUAL_ENV:-None}"
	@ls -la runtime/ 2>/dev/null || echo "Runtime directories not created yet"