# Testing Guide

## 🧪 Comprehensive Testing Strategy

This guide covers all aspects of testing in the Minerva Backend, from unit tests to integration tests and performance testing.

## 📋 Testing Overview

### Test Categories
- **Unit Tests**: Test individual components in isolation
- **Integration Tests**: Test component interactions
- **API Tests**: Test HTTP endpoints
- **Performance Tests**: Test system performance under load
- **End-to-End Tests**: Test complete user workflows

### Test Structure
```
tests/
├── unit/                    # Unit tests
│   ├── api/                # API unit tests
│   ├── processing/         # Processing unit tests
│   ├── graph/              # Graph unit tests
│   └── utils/              # Utility unit tests
├── integration/            # Integration tests
│   ├── pipeline/           # Pipeline integration tests
│   ├── database/           # Database integration tests
│   └── api/                # API integration tests
├── fixtures/               # Test fixtures and data
├── conftest.py             # Pytest configuration
├── pytest.ini             # Pytest settings
└── run_tests.py            # Test runner script
```

## 🚀 Running Tests

### Basic Test Commands
```bash
# Run all tests
poetry run pytest

# Run specific test categories
poetry run pytest tests/unit/
poetry run pytest tests/integration/

# Run with coverage
poetry run pytest --cov=minerva_backend --cov-report=html

# Run specific tests
poetry run pytest tests/unit/api/test_journal.py
poetry run pytest tests/integration/pipeline/test_complete_pipeline.py

# Run with markers
poetry run pytest -m "not slow"
poetry run pytest -m "api"
poetry run pytest -m "integration"
```

### Advanced Test Commands
```bash
# Run tests in parallel
poetry run pytest -n auto

# Run tests with verbose output
poetry run pytest -v

# Run tests with detailed output
poetry run pytest -s

# Run tests and stop on first failure
poetry run pytest -x

# Run tests with coverage and HTML report
poetry run pytest --cov=minerva_backend --cov-report=html --cov-report=term

# Run tests with performance profiling
poetry run pytest --profile
```

## 🔧 Test Configuration

### Pytest Configuration (`pytest.ini`)
```ini
[tool:pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = 
    -v
    --tb=short
    --strict-markers
    --disable-warnings
    --cov=minerva_backend
    --cov-report=term-missing
    --cov-report=html
    --cov-fail-under=80
markers =
    unit: Unit tests
    integration: Integration tests
    api: API tests
    slow: Slow running tests
    performance: Performance tests
    database: Database tests
    temporal: Temporal workflow tests
    llm: LLM service tests
    neo4j: Neo4j database tests
```

### Test Fixtures (`conftest.py`)
```python
import pytest
import asyncio
from typing import AsyncGenerator, Generator
from fastapi.testclient import TestClient
from minerva_backend.containers import Container
from minerva_backend.api.main import backend_app
from minerva_backend.graph.db import Neo4jConnection
from minerva_backend.processing.llm_service import LLMService
from minerva_backend.obsidian.obsidian_service import ObsidianService

# Async test support
@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

# Test client
@pytest.fixture
def client() -> TestClient:
    """Create a test client for the FastAPI application."""
    return TestClient(backend_app)

# Container fixtures
@pytest.fixture
def container() -> Container:
    """Create a test container with mocked dependencies."""
    return Container()

# Database fixtures
@pytest.fixture
async def db_connection() -> AsyncGenerator[Neo4jConnection, None]:
    """Create a test database connection."""
    connection = Neo4jConnection(
        uri="bolt://localhost:7687",
        user="neo4j",
        password="test_password"
    )
    await connection.connect()
    yield connection
    await connection.close()

# Service fixtures
@pytest.fixture
def llm_service() -> LLMService:
    """Create a mocked LLM service."""
    return LLMService()

@pytest.fixture
def obsidian_service() -> ObsidianService:
    """Create a mocked Obsidian service."""
    return ObsidianService()

# Test data fixtures
@pytest.fixture
def sample_journal_entry():
    """Sample journal entry for testing."""
    return {
        "text": "Today I went to the park with John. It was a beautiful day and I felt happy.",
        "date": "2024-01-15"
    }

@pytest.fixture
def sample_entities():
    """Sample entities for testing."""
    return [
        {
            "type": "Person",
            "name": "John",
            "summary": "A person mentioned in the journal entry"
        },
        {
            "type": "Place",
            "name": "park",
            "summary": "A location mentioned in the journal entry"
        }
    ]
```

## 🧪 Unit Testing

### API Unit Tests
```python
# tests/unit/api/test_journal.py
import pytest
from fastapi.testclient import TestClient
from minerva_backend.api.main import backend_app
from minerva_backend.api.models import JournalSubmission

class TestJournalAPI:
    """Test journal API endpoints."""
    
    def test_submit_journal_success(self, client: TestClient):
        """Test successful journal submission."""
        response = client.post(
            "/api/journal/submit",
            json={
                "text": "Today I went to the park with John.",
                "date": "2024-01-15"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "workflow_id" in data
        assert "journal_id" in data
    
    def test_submit_journal_invalid_data(self, client: TestClient):
        """Test journal submission with invalid data."""
        response = client.post(
            "/api/journal/submit",
            json={
                "text": "",  # Empty text
                "date": "invalid-date"
            }
        )
        assert response.status_code == 422
    
    def test_validate_journal_format(self, client: TestClient):
        """Test journal format validation."""
        response = client.post(
            "/api/journal/validate",
            json={
                "text": "Today I went to the park with John.",
                "date": "2024-01-15"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["valid"] is True
```

### Processing Unit Tests
```python
# tests/unit/processing/test_extraction_service.py
import pytest
from unittest.mock import Mock, AsyncMock, patch
from minerva_backend.processing.extraction_service import ExtractionService
from minerva_backend.graph.models.documents import JournalEntry

class TestExtractionService:
    """Test extraction service functionality."""
    
    @pytest.fixture
    def extraction_service(self, test_container):
        """Create real extraction service with mocked dependencies."""
        with patch('minerva_backend.processing.extraction_service.ProcessorFactory') as mock_factory, \
             patch('minerva_backend.processing.extraction_service.EntityExtractionOrchestrator') as mock_orchestrator, \
             patch('minerva_backend.processing.extraction_service.SpanProcessingService') as mock_span_service, \
             patch('minerva_backend.graph.repositories.base.BaseRepository._generate_embedding') as mock_embedding, \
             patch('minerva_backend.graph.repositories.base.BaseRepository._ensure_embedding') as mock_ensure_embedding:
            
            # Configure mocks
            mock_factory.create_all_processors.return_value = []
            mock_orchestrator_instance = Mock()
            mock_orchestrator.return_value = mock_orchestrator_instance
            
            # Mock embedding generation to return dummy vectors
            mock_embedding.return_value = [0.1, 0.2, 0.3] * 341 + [0.1]  # Dummy 1024-dim vector
            mock_ensure_embedding.side_effect = lambda node: node  # Return node as-is
            
            # Create real extraction service with mocked dependencies
            service = ExtractionService(
                connection=test_container.db_connection(),
                llm_service=test_container.llm_service(),
                obsidian_service=test_container.obsidian_service(),
                kg_service=test_container.kg_service(),
                entity_repositories=test_container.entity_repositories()
            )
            
            # Store the mock orchestrator instance for testing
            service._mock_orchestrator = mock_orchestrator_instance
            service.orchestrator = mock_orchestrator_instance
            
            return service
    
    @pytest.mark.asyncio
    async def test_extract_entities(self, extraction_service, sample_journal_entry):
        """Test entity extraction."""
        journal_entry = JournalEntry.from_text(
            sample_journal_entry["text"],
            sample_journal_entry["date"]
        )
        
        entities = await extraction_service.extract_entities(journal_entry)
        
        assert isinstance(entities, list)
        assert len(entities) > 0
        assert all(hasattr(entity, 'entity') for entity in entities)
    
    @pytest.mark.asyncio
    async def test_extract_relationships(self, extraction_service, sample_journal_entry):
        """Test relationship extraction."""
        journal_entry = JournalEntry.from_text(
            sample_journal_entry["text"],
            sample_journal_entry["date"]
        )
        
        relationships = await extraction_service.extract_relationships(journal_entry)
        
        assert isinstance(relationships, list)
        assert all(hasattr(rel, 'relationship') for rel in relationships)
```

### Graph Unit Tests
```python
# tests/unit/graph/test_repositories.py
import pytest
from unittest.mock import Mock
from minerva_backend.graph.repositories.person_repository import PersonRepository
from minerva_backend.graph.models.entities import Person

class TestPersonRepository:
    """Test person repository functionality."""
    
    @pytest.fixture
    def person_repository(self, db_connection):
        """Create person repository with test database."""
        return PersonRepository(db_connection)
    
    @pytest.mark.asyncio
    async def test_create_person(self, person_repository):
        """Test creating a person."""
        person = Person(
            name="John Doe",
            summary="A test person"
        )
        
        created_person = await person_repository.create(person)
        
        assert created_person.uuid is not None
        assert created_person.name == "John Doe"
        assert created_person.summary == "A test person"
    
    @pytest.mark.asyncio
    async def test_find_person_by_name(self, person_repository):
        """Test finding a person by name."""
        person = Person(
            name="Jane Doe",
            summary="Another test person"
        )
        await person_repository.create(person)
        
        found_person = await person_repository.find_by_name("Jane Doe")
        
        assert found_person is not None
        assert found_person.name == "Jane Doe"
```

## 🔗 Integration Testing

### Pipeline Integration Tests
```python
# tests/integration/pipeline/test_complete_pipeline.py
import pytest
from minerva_backend.containers import Container
from minerva_backend.graph.models.documents import JournalEntry

class TestCompletePipeline:
    """Test complete processing pipeline."""
    
    @pytest.fixture
    def container(self):
        """Create container with real dependencies."""
        return Container()
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    @pytest.mark.slow
    async def test_complete_journal_processing(self, container):
        """Test complete journal processing pipeline."""
        # Create journal entry
        journal_entry = JournalEntry.from_text(
            "Today I went to the park with John. It was a beautiful day and I felt happy.",
            "2024-01-15"
        )
        
        # Submit to pipeline
        orchestrator = container.pipeline_orchestrator()
        workflow_id = await orchestrator.submit_journal(journal_entry)
        
        assert workflow_id is not None
        
        # Wait for processing to complete
        status = await orchestrator.get_workflow_status(workflow_id)
        assert status is not None
        
        # Verify entities were created
        extraction_service = container.extraction_service()
        entities = await extraction_service.extract_entities(journal_entry)
        assert len(entities) > 0
        
        # Verify relationships were created
        relationships = await extraction_service.extract_relationships(journal_entry)
        assert len(relationships) > 0
```

### Database Integration Tests
```python
# tests/integration/database/test_neo4j_integration.py
import pytest
from minerva_backend.graph.db import Neo4jConnection
from minerva_backend.graph.repositories.person_repository import PersonRepository
from minerva_backend.graph.models.entities import Person

class TestNeo4jIntegration:
    """Test Neo4j database integration."""
    
    @pytest.fixture
    async def db_connection(self):
        """Create test database connection."""
        connection = Neo4jConnection(
            uri="bolt://localhost:7687",
            user="neo4j",
            password="test_password"
        )
        await connection.connect()
        yield connection
        await connection.close()
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    @pytest.mark.neo4j
    async def test_person_crud_operations(self, db_connection):
        """Test CRUD operations for Person entity."""
        person_repository = PersonRepository(db_connection)
        
        # Create person
        person = Person(
            name="Test Person",
            summary="A test person for integration testing"
        )
        created_person = await person_repository.create(person)
        assert created_person.uuid is not None
        
        # Read person
        found_person = await person_repository.find_by_uuid(created_person.uuid)
        assert found_person is not None
        assert found_person.name == "Test Person"
        
        # Update person
        found_person.summary = "Updated summary"
        updated_person = await person_repository.update(found_person)
        assert updated_person.summary == "Updated summary"
        
        # Delete person
        await person_repository.delete(created_person.uuid)
        deleted_person = await person_repository.find_by_uuid(created_person.uuid)
        assert deleted_person is None
```

### API Integration Tests
```python
# tests/integration/api/test_journal_pipeline.py
import pytest
from fastapi.testclient import TestClient
from minerva_backend.api.main import backend_app

class TestJournalPipelineIntegration:
    """Test journal processing pipeline integration."""
    
    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(backend_app)
    
    @pytest.mark.integration
    @pytest.mark.api
    @pytest.mark.slow
    def test_complete_journal_workflow(self, client):
        """Test complete journal workflow from API to database."""
        # Submit journal entry
        response = client.post(
            "/api/journal/submit",
            json={
                "text": "Today I went to the park with John. It was a beautiful day and I felt happy.",
                "date": "2024-01-15"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        
        workflow_id = data["workflow_id"]
        journal_id = data["journal_id"]
        
        # Check workflow status
        status_response = client.get(f"/api/pipeline/status/{workflow_id}")
        assert status_response.status_code == 200
        status_data = status_response.json()
        assert "status" in status_data
        
        # Wait for processing to complete (in real test, you'd poll)
        # For now, just verify the workflow was created
        assert workflow_id is not None
        assert journal_id is not None
```

## 📊 Performance Testing

### Test Performance Optimization

#### Recent Improvements (2024)
- **LLM Service Tests**: Optimized from 53s to 11s execution time (3x faster)
- **Mock Strategy**: Implemented comprehensive mocking of expensive external calls
- **Async Mocking**: Proper use of `AsyncMock` for async methods instead of `Mock`
- **Dependency Injection**: Enhanced test fixtures with proper container mocking

#### Performance Best Practices
```python
# ✅ GOOD: Mock expensive initialization
@pytest.fixture
def llm_service(mock_ollama_client, mock_cache):
    """Create LLMService with mocked dependencies."""
    with patch('ollama.AsyncClient') as mock_client_class:
        mock_client_class.return_value = mock_ollama_client
        with patch('minerva_backend.processing.llm_service.Cache') as mock_cache_class:
            mock_cache_class.return_value = mock_cache
            service = LLMService()
            service.cache_enabled = True
            service.cache = mock_cache
    return service

# ✅ GOOD: Mock time-consuming operations
@patch('asyncio.sleep')
def test_retry_logic(mock_sleep, llm_service):
    """Test retry logic without actual delays."""
    # Test retry behavior without waiting
    pass
```

### Load Testing
```python
# tests/performance/test_load.py
import pytest
import asyncio
import time
from concurrent.futures import ThreadPoolExecutor
from fastapi.testclient import TestClient
from minerva_backend.api.main import backend_app

class TestLoadPerformance:
    """Test system performance under load."""
    
    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(backend_app)
    
    @pytest.mark.performance
    @pytest.mark.slow
    def test_concurrent_journal_submissions(self, client):
        """Test concurrent journal submissions."""
        def submit_journal():
            response = client.post(
                "/api/journal/submit",
                json={
                    "text": "Test journal entry for load testing.",
                    "date": "2024-01-15"
                }
            )
            return response.status_code == 200
        
        # Submit 10 concurrent requests
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(submit_journal) for _ in range(10)]
            results = [future.result() for future in futures]
        
        # All requests should succeed
        assert all(results)
    
    @pytest.mark.performance
    @pytest.mark.slow
    def test_entity_extraction_performance(self, client):
        """Test entity extraction performance."""
        start_time = time.time()
        
        response = client.post(
            "/api/journal/submit",
            json={
                "text": "Today I went to the park with John. It was a beautiful day and I felt happy. We had a great time together.",
                "date": "2024-01-15"
            }
        )
        
        end_time = time.time()
        duration = end_time - start_time
        
        assert response.status_code == 200
        assert duration < 5.0  # Should complete within 5 seconds
```

## 🎯 Test Data and Fixtures

### Sample Data
```python
# tests/fixtures/sample_data.py
from typing import Dict, List, Any

SAMPLE_JOURNAL_ENTRIES = [
    {
        "text": "Today I went to the park with John. It was a beautiful day and I felt happy.",
        "date": "2024-01-15"
    },
    {
        "text": "I had a meeting with Sarah about the new project. We discussed the timeline and budget.",
        "date": "2024-01-16"
    },
    {
        "text": "I went to the gym and then had dinner at the Italian restaurant downtown.",
        "date": "2024-01-17"
    }
]

SAMPLE_ENTITIES = [
    {
        "type": "Person",
        "name": "John",
        "summary": "A person mentioned in the journal entry"
    },
    {
        "type": "Person",
        "name": "Sarah",
        "summary": "A person mentioned in the journal entry"
    },
    {
        "type": "Place",
        "name": "park",
        "summary": "A location mentioned in the journal entry"
    },
    {
        "type": "Place",
        "name": "gym",
        "summary": "A location mentioned in the journal entry"
    }
]

SAMPLE_RELATIONSHIPS = [
    {
        "type": "KNOWS",
        "source": "John",
        "target": "Sarah",
        "summary": "John knows Sarah"
    },
    {
        "type": "VISITED",
        "source": "John",
        "target": "park",
        "summary": "John visited the park"
    }
]
```

### Test Utilities
```python
# tests/fixtures/test_utils.py
import pytest
from typing import Dict, Any
from minerva_backend.graph.models.documents import JournalEntry
from minerva_backend.graph.models.entities import Person, Place, Event

def create_test_journal_entry(text: str, date: str) -> JournalEntry:
    """Create a test journal entry."""
    return JournalEntry.from_text(text, date)

def create_test_person(name: str, summary: str = "Test person") -> Person:
    """Create a test person."""
    return Person(name=name, summary=summary)

def create_test_place(name: str, summary: str = "Test place") -> Place:
    """Create a test place."""
    return Place(name=name, summary=summary)

def create_test_event(name: str, summary: str = "Test event") -> Event:
    """Create a test event."""
    return Event(name=name, summary=summary)

def assert_entity_created(entity: Any, expected_name: str, expected_type: str):
    """Assert that an entity was created correctly."""
    assert entity is not None
    assert entity.name == expected_name
    assert entity.type == expected_type
    assert entity.uuid is not None
```

## 🔍 Test Debugging

### Debugging Failed Tests
```bash
# Run tests with detailed output
poetry run pytest -v -s

# Run specific test with debugging
poetry run pytest tests/unit/api/test_journal.py::TestJournalAPI::test_submit_journal_success -v -s

# Run tests with coverage and HTML report
poetry run pytest --cov=minerva_backend --cov-report=html

# Run tests with profiling
poetry run pytest --profile
```

### Common Test Issues

#### Issue: Async Test Failures
**Error**: `RuntimeError: There is no current event loop`

**Solution**:
```python
@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()
```

#### Issue: Database Connection Failures
**Error**: `ServiceUnavailableError: Neo4j Database service is currently unavailable`

**Solution**:
```python
@pytest.fixture
async def db_connection():
    """Create a test database connection."""
    connection = Neo4jConnection(
        uri="bolt://localhost:7687",
        user="neo4j",
        password="test_password"
    )
    await connection.connect()
    yield connection
    await connection.close()
```

#### Issue: Temporal Workflow Failures
**Error**: `ConnectionError: Failed to connect to Temporal`

**Solution**:
```python
@pytest.fixture
def temporal_client():
    """Create a mocked Temporal client."""
    return Mock()
```

## 📈 Test Coverage

### Coverage Requirements
- **Minimum Coverage**: 80%
- **Critical Components**: 90%
- **API Endpoints**: 100%
- **Core Services**: 85%

### Coverage Reports
```bash
# Generate coverage report
poetry run pytest --cov=minerva_backend --cov-report=html --cov-report=term

# View coverage report
open htmlcov/index.html
```

### Coverage Configuration
```toml
# pyproject.toml
[tool.coverage.run]
source = ["src/minerva_backend"]
omit = [
    "*/tests/*",
    "*/test_*",
    "*/__pycache__/*",
    "*/migrations/*"
]

[tool.coverage.report]
exclude_lines = [
    "pragma: no cover",
    "def __repr__",
    "if self.debug:",
    "if settings.DEBUG",
    "raise AssertionError",
    "raise NotImplementedError",
    "if 0:",
    "if __name__ == .__main__.:",
    "class .*\\bProtocol\\):",
    "@(abc\\.)?abstractmethod"
]
```

## 🚀 Continuous Integration

### GitHub Actions
```yaml
# .github/workflows/test.yml
name: Tests

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest
    
    services:
      neo4j:
        image: neo4j:5.0
        env:
          NEO4J_AUTH: neo4j/test_password
        ports:
          - 7474:7474
          - 7687:7687
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.13'
    
    - name: Install Poetry
      uses: snok/install-poetry@v1
    
    - name: Install dependencies
      run: poetry install
    
    - name: Run tests
      run: poetry run pytest --cov=minerva_backend --cov-report=xml
    
    - name: Upload coverage
      uses: codecov/codecov-action@v3
      with:
        file: ./coverage.xml
```

## 🎯 Best Practices

### Dependency Injection in Testing

#### Unit Test Pattern: Real Service with Mocked Dependencies
For unit tests, we use **real services** with **mocked dependencies** to test actual business logic while maintaining isolation:

```python
# ✅ CORRECT: Real service with mocked dependencies
@pytest.fixture
def obsidian_service(test_container):
    """Create real ObsidianService with mocked dependencies."""
    from minerva_backend.obsidian.obsidian_service import ObsidianService
    
    return ObsidianService(
        vault_path="/tmp/minerva_test_vault",  # Test-specific path
        llm_service=test_container.llm_service(),  # Mocked dependency
        concept_repository=test_container.concept_repository()  # Mocked dependency
    )

def test_parse_conexiones_section(obsidian_service):
    """Test parsing Conexiones section."""
    content = "- GENERALIZES: [[Deep Learning]]"
    result = obsidian_service.parse_conexiones_section(content)
    
    expected = {"GENERALIZES": ["Deep Learning"]}
    assert result == expected
```

#### API Test Pattern: Container with Mocked Services
For API tests, we use the **test container** directly with mocked services:

```python
# ✅ CORRECT: API tests use test_container directly
@pytest.fixture
def client(test_container):
    """Create test client with mocked dependencies."""
    return TestClient(backend_app)

def test_submit_journal_success(client):
    """Test successful journal submission."""
    response = client.post("/api/journal/submit", json={
        "text": "Today I went to the park with John.",
        "date": "2024-01-15"
    })
    assert response.status_code == 200
```

#### ❌ AVOID: Mocking the Service Under Test
Never mock the service you're testing in unit tests:

```python
# ❌ WRONG: Mocking the service under test
@pytest.fixture
def obsidian_service(test_container):
    return test_container.obsidian_service()  # Returns mock!

def test_parse_conexiones_section(obsidian_service):
    # This tests the mock, not the real service logic!
    result = obsidian_service.parse_conexiones_section(content)
```

#### ❌ AVOID: Manual Service Instantiation
Don't manually instantiate services in tests (breaks DI):

```python
# ❌ WRONG: Manual instantiation breaks DI
def test_parse_conexiones_section():
    service = ObsidianService(
        vault_path="/tmp/test",
        llm_service=Mock(),
        concept_repository=Mock()
    )
    # This bypasses the DI container!
```

### Test Organization
1. **Group related tests** in classes
2. **Use descriptive test names** that explain what is being tested
3. **Keep tests independent** - no shared state between tests
4. **Use fixtures** for common setup and teardown
5. **Mock external dependencies** in unit tests
6. **Use real services** in unit tests (not mocked services)
7. **Use test-specific paths** for file system operations

### Test Data
1. **Use realistic test data** that reflects real usage
2. **Create reusable fixtures** for common test scenarios
3. **Clean up after tests** to avoid test pollution
4. **Use factories** for generating test data

### Performance Testing
1. **Test under realistic load** conditions
2. **Measure and track** performance metrics
3. **Set performance benchmarks** and fail tests that exceed them
4. **Profile slow tests** to identify bottlenecks

### Maintenance
1. **Keep tests up to date** with code changes
2. **Refactor tests** when refactoring code
3. **Remove obsolete tests** that are no longer relevant
4. **Document test requirements** and assumptions

## 🎉 Conclusion

This testing guide provides a comprehensive framework for testing the Minerva Backend. By following these practices, you can ensure:

- **Code Quality**: High test coverage and quality
- **Reliability**: Robust error handling and edge cases
- **Performance**: System performance under load
- **Maintainability**: Easy to maintain and extend tests

Remember: **Good tests are an investment in the future of your codebase!** 🚀