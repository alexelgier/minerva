# Dependency Injection Architecture

## 🏗️ Overview

Minerva Backend uses the `dependency-injector` library to implement dependency injection (DI) throughout the application. This provides loose coupling, easier testing, and better maintainability.

## 📦 Container Configuration

The main DI container is defined in `src/minerva_backend/containers.py`:

```python
from dependency_injector import containers, providers
from minerva_backend.config import settings

class Container(containers.DeclarativeContainer):
    config = providers.Configuration()
    config.from_pydantic(settings)

    # Database connection
    db_connection = providers.Singleton(
        Neo4jConnection,
        uri=config.NEO4J_URI,
        user=config.NEO4J_USER,
        password=config.NEO4J_PASSWORD,
    )

    # Services
    llm_service = providers.Singleton(LLMService, cache=True)
    curation_manager = providers.Singleton(CurationManager, db_path=config.CURATION_DB_PATH)
    
    # Repositories
    concept_repository = providers.Factory(
        ConceptRepository,
        connection=db_connection,
        llm_service=llm_service,
    )
    
    # ... other providers
```

## 🔧 Provider Types

### Singleton Providers
Used for services that should have only one instance throughout the application lifecycle:

```python
llm_service = providers.Singleton(LLMService, cache=True)
curation_manager = providers.Singleton(CurationManager, db_path=config.CURATION_DB_PATH)
```

### Factory Providers
Used for repositories and other components that can have multiple instances:

```python
concept_repository = providers.Factory(
    ConceptRepository,
    connection=db_connection,
    llm_service=llm_service,
)
```

### Configuration Providers
Used for accessing configuration values:

```python
config = providers.Configuration()
config.from_pydantic(settings)
```

## 🚀 Usage in Services

### Constructor Injection
Services receive their dependencies through constructor parameters:

```python
class KnowledgeGraphService:
    def __init__(
        self,
        connection: Neo4jConnection,
        llm_service: LLMService,
        entity_repositories: Dict[str, BaseRepository],
        # ... other dependencies
    ):
        self.connection = connection
        self.llm_service = llm_service
        self.entity_repositories = entity_repositories
```

### Container Resolution
Services are resolved from the container:

```python
# In main.py
container = Container()
kg_service = container.kg_service()
```

## 🌐 FastAPI Integration

### Dependency Functions
FastAPI dependencies are defined in `api/dependencies.py`:

```python
from dependency_injector.wiring import inject, Provide

@inject
async def get_db_connection(
    db: Neo4jConnection = Depends(Provide[Container.db_connection]),
) -> Neo4jConnection:
    """Get Neo4j database connection."""
    return db

@inject
async def get_llm_service(
    llm_service: LLMService = Depends(Provide[Container.llm_service]),
) -> LLMService:
    """Get LLM service."""
    return llm_service
```

### Router Usage
Routers use dependency injection for their endpoints:

```python
@router.get("/")
async def health_check(
    db_connection: Neo4jConnection = Depends(get_db_connection),
    llm_service: LLMService = Depends(get_llm_service),
    # ... other dependencies
) -> JSONResponse:
    # Use injected dependencies
    pass
```

### Container Wiring
The container is wired to enable dependency injection:

```python
# In main.py
container.wire(modules=[
    "minerva_backend.api.dependencies",
    "minerva_backend.processing.temporal_orchestrator",
])
```

## 🧪 Testing with Dependency Injection

### Test Container
Tests use a test container with mocked dependencies:

```python
@pytest.fixture
def test_container(
    mock_neo4j_connection,
    mock_llm_service,
    # ... other mocks
):
    """Test container with mocked dependencies."""
    container = Container()
    
    # Override with mocks
    container.db_connection.override(mock_neo4j_connection)
    container.llm_service.override(mock_llm_service)
    
    return container
```

### Test Client
The test client uses the test container:

```python
@pytest.fixture
def client(test_container):
    """Create test client with mocked dependencies."""
    backend_app.state.container = test_container
    test_container.wire(modules=["minerva_backend.api.dependencies"])
    return TestClient(backend_app)
```

## 🔄 Temporal Workflows

### Stateless Activities
Temporal activities must be stateless, so they create their own container instances:

```python
class PipelineActivities:
    @activity.defn
    async def extract_entities(journal_entry: JournalEntry) -> List[EntityMapping]:
        """Extract entities - stateless activity."""
        from minerva_backend.containers import Container
        container = Container()
        return await container.extraction_service().extract_entities(journal_entry)
```

### Worker Setup
The worker uses direct configuration access:

```python
async def run_worker():
    """Start the Temporal worker."""
    from minerva_backend.config import settings
    
    client = await Client.connect(
        settings.TEMPORAL_URI, data_converter=pydantic_data_converter
    )
    # ... worker setup
```

## 📋 Best Practices

### 1. Constructor Injection
Always inject dependencies through constructors, not through method parameters:

```python
# ✅ Good
class ObsidianService:
    def __init__(self, concept_repository: ConceptRepository):
        self.concept_repository = concept_repository
    
    async def sync_zettels_to_db(self):
        # Use self.concept_repository
        pass

# ❌ Bad
class ObsidianService:
    async def sync_zettels_to_db(self, concept_repository: ConceptRepository):
        # Don't pass dependencies as method parameters
        pass
```

### 2. Interface Segregation
Use specific interfaces rather than concrete types when possible:

```python
# ✅ Good
def __init__(self, entity_repositories: Dict[str, BaseRepository]):
    self.entity_repositories = entity_repositories

# ❌ Bad
def __init__(self, concept_repo: ConceptRepository, person_repo: PersonRepository):
    # Too many specific dependencies
    pass
```

### 3. Configuration Injection
Inject configuration through the container, not directly:

```python
# ✅ Good
db_connection = providers.Singleton(
    Neo4jConnection,
    uri=config.NEO4J_URI,
    user=config.NEO4J_USER,
    password=config.NEO4J_PASSWORD,
)

# ❌ Bad
db_connection = providers.Singleton(
    Neo4jConnection,
    uri="bolt://localhost:7687",  # Hardcoded values
    user="neo4j",
    password="password",
)
```

### 4. Test Isolation
Override dependencies in tests rather than modifying the container:

```python
# ✅ Good
def test_something(test_container):
    mock_service = Mock()
    test_container.some_service.override(mock_service)
    # Test with mocked service

# ❌ Bad
def test_something():
    container = Container()
    container.some_service = Mock()  # Modifying container directly
    # Test with modified container
```

## 🚨 Common Pitfalls

### 1. Circular Dependencies
Avoid circular dependencies between services:

```python
# ❌ Bad - Circular dependency
class ServiceA:
    def __init__(self, service_b: ServiceB):
        self.service_b = service_b

class ServiceB:
    def __init__(self, service_a: ServiceA):
        self.service_a = service_a
```

### 2. Manual Instantiation
Don't manually instantiate services outside the container:

```python
# ❌ Bad
def some_function():
    service = SomeService()  # Manual instantiation
    service.do_something()

# ✅ Good
def some_function(service: SomeService = Depends(get_some_service)):
    service.do_something()
```

### 3. Missing Wiring
Ensure containers are wired for dependency injection:

```python
# ❌ Bad - Missing wiring
container = Container()
# Dependencies won't be injected

# ✅ Good - Proper wiring
container = Container()
container.wire(modules=["minerva_backend.api.dependencies"])
```

## 🔍 Debugging Dependency Injection

### 1. Check Container Wiring
Ensure all modules are properly wired:

```python
container.wire(modules=[
    "minerva_backend.api.dependencies",
    "minerva_backend.processing.temporal_orchestrator",
])
```

### 2. Verify Provider Configuration
Check that all providers are correctly configured:

```python
# Test container resolution
container = Container()
service = container.some_service()  # Should not raise errors
```

### 3. Check Test Overrides
Ensure test overrides are properly applied:

```python
def test_something(test_container):
    mock_service = Mock()
    test_container.some_service.override(mock_service)
    
    # Verify override worked
    assert test_container.some_service() is mock_service
```

## 🧪 Testing with Dependency Injection

### Unit Testing Pattern: Real Service with Mocked Dependencies

For unit tests, we create **real services** with **mocked dependencies** to test actual business logic while maintaining isolation:

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

### API Testing Pattern: Container with Mocked Services

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

### Test Container Configuration

The test suite uses a comprehensive test container that provides mocked dependencies:

```python
@pytest.fixture
def test_container(
    # Core service mocks
    mock_neo4j_connection,
    mock_curation_manager,
    mock_pipeline_orchestrator,
    mock_llm_service,
    mock_obsidian_service,
    mock_kg_service,
    mock_extraction_service,
    # Repository mocks (all 20+ repositories)
    mock_concept_repository,
    mock_people_repository,
    # ... (all other repository mocks)
    # Dict providers
    mock_entity_repositories,
    mock_emotions_dict
):
    """Test container with mocked dependencies."""
    container = Container()
    
    # Override providers with mocks
    container.db_connection.override(mock_neo4j_connection)
    container.curation_manager.override(mock_curation_manager)
    # ... (all other provider overrides)
    
    return container
```

### ❌ Anti-Patterns to Avoid

#### Don't Mock the Service Under Test
```python
# ❌ WRONG: Mocking the service under test
@pytest.fixture
def obsidian_service(test_container):
    return test_container.obsidian_service()  # Returns mock!

def test_parse_conexiones_section(obsidian_service):
    # This tests the mock, not the real service logic!
    result = obsidian_service.parse_conexiones_section(content)
```

#### Don't Manually Instantiate Services
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

### Test Isolation Features

Tests are **completely isolated** from external dependencies:
- **Database**: All database operations are mocked (no real Neo4j connections)
- **LLM Service**: All LLM calls are mocked (no real Ollama calls)
- **File System**: All file operations are mocked (no real file I/O)
- **External APIs**: All external service calls are mocked
- **Logging**: All logging is disabled during tests (no log file writes)

### Logging Disabled in Tests

```python
@pytest.fixture(autouse=True)
def disable_logging():
    """Disable all logging during tests to prevent log file writes."""
    # Disable all logging
    logging.disable(logging.CRITICAL)
    
    # Also disable specific loggers
    for logger_name in ['minerva_backend', 'minerva_backend.graph', 'minerva_backend.processing', 'minerva_backend.api']:
        logging.getLogger(logger_name).disabled = True
    
    yield
    
    # Re-enable logging after test
    logging.disable(logging.NOTSET)
    for logger_name in ['minerva_backend', 'minerva_backend.graph', 'minerva_backend.processing', 'minerva_backend.api']:
        logging.getLogger(logger_name).disabled = False
```

### Critical Fix: Lazy Provider Evaluation

**IMPORTANT**: The `emotions_dict` provider was fixed to use lazy evaluation:

```python
# BEFORE (caused immediate execution during import)
emotions_dict = db_connection.provided.init_emotion_types()()

# AFTER (lazy evaluation with Singleton)
emotions_dict = providers.Singleton(
    lambda: db_connection().init_emotion_types()
)
```

This prevents real database connections during import time, ensuring tests start with complete isolation.

### Test Results

All **238 unit tests** pass with complete isolation:
- ✅ No real database connections
- ✅ No real LLM calls to Ollama
- ✅ No log file writes
- ✅ No external API calls
- ✅ Fast execution (10.33 seconds for full suite)

## 📚 Additional Resources

- [Dependency Injector Documentation](https://python-dependency-injector.ets-labs.org/)
- [FastAPI Dependency Injection](https://fastapi.tiangolo.com/tutorial/dependencies/)
- [Temporal Python SDK](https://docs.temporal.io/application-development/foundations/install-temporal)

## 🎯 Summary

Dependency injection in Minerva Backend provides:

- **Loose Coupling**: Services depend on interfaces, not concrete implementations
- **Easy Testing**: Dependencies can be easily mocked and overridden
- **Configuration Management**: Centralized configuration through the container
- **Maintainability**: Changes to dependencies are isolated and manageable
- **Scalability**: New services can be easily added to the container

The DI system is designed to be simple, consistent, and maintainable across the entire application.
