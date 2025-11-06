# Minerva Backend Makefile
# Easy commands for development and quality checks

.PHONY: help install format lint test docs clean quality

help: ## Show this help message
	@echo "Minerva Backend Development Commands"
	@echo "===================================="
	@echo ""
	@echo "Setup:"
	@echo "  install     Install dependencies"
	@echo "  clean       Clean build artifacts"
	@echo ""
	@echo "Code Quality:"
	@echo "  format      Format code with black and isort"
	@echo "  lint        Run linting checks"
	@echo "  quality     Run all quality checks"
	@echo ""
	@echo "Testing:"
	@echo "  test        Run all tests"
	@echo "  test-cov    Run tests with coverage"
	@echo "  test-cov-html Run tests with HTML coverage report"
	@echo "  test-cov-xml  Run tests with XML coverage report"
	@echo "  test-cov-open Open HTML coverage report in browser"
	@echo "  test-unit   Run unit tests only"
	@echo "  test-fast   Run fast tests only (exclude slow/integration)"
	@echo ""
	@echo "Documentation:"
	@echo "  docs        Generate all documentation"
	@echo "  docs-serve  Serve documentation locally"
	@echo ""
	@echo "Development:"
	@echo "  run         Run the application"
	@echo "  dev         Run in development mode"

install: ## Install dependencies
	poetry install

clean: ## Clean build artifacts
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	rm -rf .pytest_cache/
	rm -rf .mypy_cache/
	rm -rf docs/_build/
	rm -rf docs/site/
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

format: ## Format code with black and isort
	poetry run black src/
	poetry run isort src/

lint: ## Run linting checks
	poetry run flake8 src/
	poetry run radon cc src/ --min B
	poetry run vulture src/ --min-confidence 60
	poetry run mypy src/

quality: ## Run all quality checks
	python scripts/quality_check.py

test: ## Run all tests
	poetry run pytest

test-cov: ## Run tests with coverage
	poetry run pytest --cov=src/minerva_backend --cov-report=term-missing --cov-report=html:htmlcov --cov-report=xml:coverage.xml --cov-fail-under=50

test-cov-html: ## Run tests with HTML coverage report
	poetry run pytest --cov=src/minerva_backend --cov-report=html:htmlcov --cov-fail-under=50

test-cov-xml: ## Run tests with XML coverage report
	poetry run pytest --cov=src/minerva_backend --cov-report=xml:coverage.xml --cov-fail-under=50

test-cov-open: ## Open HTML coverage report in browser
	@if [ -f "htmlcov/index.html" ]; then \
		echo "Opening coverage report..."; \
		start htmlcov/index.html 2>/dev/null || open htmlcov/index.html 2>/dev/null || xdg-open htmlcov/index.html 2>/dev/null || echo "Please open htmlcov/index.html in your browser"; \
	else \
		echo "Coverage report not found. Run 'make test-cov-html' first."; \
	fi

test-unit: ## Run unit tests only
	poetry run pytest tests/unit/ -v

test-fast: ## Run fast tests only (exclude slow/integration)
	poetry run pytest -m "not slow and not integration" -v

docs: ## Generate all documentation
	python scripts/generate_docs.py

docs-serve: ## Serve documentation locally
	poetry run mkdocs serve

run: ## Run the application
	poetry run python -m minerva_backend.api.main

dev: ## Run in development mode
	poetry run uvicorn minerva_backend.api.main:backend_app --reload --host 0.0.0.0 --port 8000
