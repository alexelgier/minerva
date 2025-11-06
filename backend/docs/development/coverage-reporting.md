# Code Coverage Reporting

This document describes the code coverage reporting setup for the Minerva Backend project.

## Overview

Code coverage reporting helps identify which parts of the codebase are tested and which areas need additional test coverage. The project uses `pytest-cov` to generate comprehensive coverage reports.

## Configuration

### Dependencies

The coverage reporting functionality is provided by the `pytest-cov` package, which is included in the development dependencies:

```toml
[tool.poetry.group.dev.dependencies]
pytest-cov = "^4.0"
```

### Coverage Configuration

Coverage settings are configured in multiple places:

1. **`.coveragerc`** - Main coverage configuration file
2. **`tests/pytest.ini`** - Pytest configuration with coverage options
3. **`Makefile`** - Convenient commands for running coverage

### Coverage Threshold

The project currently has a coverage threshold of **50%**, which is a reasonable starting point that can be increased as more tests are added.

## Available Commands

### Using Poetry (Recommended)

```bash
# Run all tests with coverage
poetry run pytest --cov=src/minerva_backend --cov-report=term-missing --cov-report=html:htmlcov --cov-report=xml:coverage.xml --cov-fail-under=50

# Run only unit tests with coverage
poetry run pytest tests/unit/ --cov=src/minerva_backend --cov-report=term-missing --cov-report=html:htmlcov --cov-report=xml:coverage.xml --cov-fail-under=50

# Run tests with HTML coverage report only
poetry run pytest --cov=src/minerva_backend --cov-report=html:htmlcov --cov-fail-under=50

# Run tests with XML coverage report only
poetry run pytest --cov=src/minerva_backend --cov-report=xml:coverage.xml --cov-fail-under=50
```

### Using Make (if available)

```bash
# Run all tests with coverage
make test-cov

# Run tests with HTML coverage report
make test-cov-html

# Run tests with XML coverage report
make test-cov-xml

# Open HTML coverage report in browser
make test-cov-open

# Run unit tests only
make test-unit

# Run fast tests only (exclude slow/integration)
make test-fast
```

### Using the Test Runner Script

```bash
# Run tests with coverage
python tests/run_tests.py coverage

# Run unit tests only
python tests/run_tests.py unit

# Run all tests
python tests/run_tests.py all
```

## Coverage Reports

### Terminal Report

The terminal report shows:
- Coverage percentage for each file
- Missing line numbers
- Overall coverage statistics

### HTML Report

The HTML report is generated in the `htmlcov/` directory and provides:
- Interactive coverage browsing
- File-by-file coverage details
- Line-by-line coverage highlighting
- Branch coverage information

To view the HTML report:
1. Run coverage with HTML report: `poetry run pytest --cov=src/minerva_backend --cov-report=html:htmlcov`
2. Open `htmlcov/index.html` in your browser

### XML Report

The XML report is generated as `coverage.xml` and can be used by:
- CI/CD systems
- Code quality tools
- IDE integrations

## Coverage Exclusions

The following are excluded from coverage calculations:

### Files and Directories
- Test files (`test_*.py`, `*/tests/*`)
- Configuration files (`conftest.py`, `__init__.py`)
- Migration files (`*/migrations/*`)
- Virtual environments (`*/venv/*`, `*/env/*`)
- Documentation (`*/docs/*`)
- Scripts (`*/scripts/*`)

### Code Patterns
- Debug-only code (`if self.debug`)
- Abstract methods (`@abstractmethod`)
- Type checking code (`if TYPE_CHECKING`)
- Main blocks (`if __name__ == "__main__"`)
- Test fixtures and utilities (`def test_*`, `class Test*`)

## Current Coverage Status

As of the latest test run:
- **Total Coverage**: 53.69%
- **Threshold**: 50%
- **Status**: ✅ Passing

### Coverage by Module

| Module | Coverage | Status |
|--------|----------|--------|
| API Layer | 73-99% | ✅ Good |
| Graph Models | 88-100% | ✅ Excellent |
| Graph Repositories | 16-80% | ⚠️ Needs improvement |
| Processing Services | 25-100% | ⚠️ Mixed |
| Prompt Templates | 0-89% | ⚠️ Needs improvement |
| Utilities | 19-89% | ⚠️ Mixed |

## Improving Coverage

### Areas Needing Attention

1. **Graph Repositories** - Many repository classes have low coverage (16-32%)
2. **Processing Services** - Some services like `CurationManager` have low coverage (25%)
3. **Prompt Templates** - Some prompt files have 0% coverage
4. **Utilities** - `validators.py` has only 19% coverage

### Strategies for Improvement

1. **Add Unit Tests** - Focus on untested methods and edge cases
2. **Mock Dependencies** - Use mocks for external services (Neo4j, LLM services)
3. **Test Error Paths** - Add tests for exception handling and error conditions
4. **Integration Tests** - Add tests that verify component interactions

## CI/CD Integration

The coverage reporting is designed to work with CI/CD systems:

1. **XML Report** - Can be consumed by CI systems for coverage tracking
2. **Threshold Enforcement** - Tests will fail if coverage drops below threshold
3. **HTML Report** - Can be published as build artifacts

## Troubleshooting

### Common Issues

1. **Async Test Failures** - Ensure async tests are marked with `@pytest.mark.asyncio`
2. **Database Connection Errors** - Use mocks for database-dependent tests
3. **Import Errors** - Check that the source path is correctly configured

### Debugging Coverage

1. **Check Exclusions** - Verify that files aren't being excluded unintentionally
2. **Review Missing Lines** - Use the HTML report to see exactly which lines aren't covered
3. **Test Isolation** - Ensure tests don't depend on external services

## Best Practices

1. **Maintain High Coverage** - Aim for at least 80% coverage on critical modules
2. **Test Edge Cases** - Don't just test happy paths
3. **Mock External Dependencies** - Keep tests fast and reliable
4. **Regular Coverage Reviews** - Check coverage reports regularly
5. **Incremental Improvement** - Gradually increase coverage over time

## Future Enhancements

1. **Branch Coverage** - Enable branch coverage reporting
2. **Coverage Trends** - Track coverage changes over time
3. **Coverage Badges** - Add coverage badges to README
4. **Coverage Reports in PRs** - Automatically comment on PRs with coverage changes
