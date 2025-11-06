# Minerva Backend Test Makefile

.PHONY: help test unit integration all coverage fast check clean

help: ## Show this help message
	@echo "Minerva Backend Test Commands:"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

check: ## Check test environment
	python tests/run_tests.py check

unit: ## Run unit tests only
	python tests/run_tests.py unit

integration: ## Run integration tests only
	python tests/run_tests.py integration

all: ## Run all tests
	python tests/run_tests.py all

coverage: ## Run tests with coverage report
	python tests/run_tests.py coverage

fast: ## Run fast tests only (exclude slow/integration)
	python tests/run_tests.py fast

test: all ## Alias for 'all'

clean: ## Clean test artifacts
	rm -rf .pytest_cache/
	rm -rf htmlcov/
	rm -rf .coverage
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

# Specific test targets
test-journal: ## Run journal API tests
	python tests/run_tests.py specific tests/unit/api/test_journal.py

test-database: ## Run database integration tests
	python tests/run_tests.py specific tests/integration/database/

test-api: ## Run all API tests
	python tests/run_tests.py specific tests/unit/api/

test-processing: ## Run processing tests
	python tests/run_tests.py specific tests/unit/processing/

test-graph: ## Run graph tests
	python tests/run_tests.py specific tests/unit/graph/
