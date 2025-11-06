# AI Assistant Quick Reference

## 🎯 System Overview

**Minerva Backend** is a personal knowledge management system that processes journal entries to extract entities and relationships, building a comprehensive knowledge graph using Neo4j, Temporal workflows, and local LLM processing.

## 🏗️ Core Architecture

### Key Components
- **API Layer**: FastAPI with dependency injection
- **Processing Pipeline**: 5-stage entity extraction and relationship processing
- **Knowledge Graph**: Neo4j database with vector search capabilities
- **Workflow Orchestration**: Temporal for reliable long-running processes
- **LLM Integration**: Local Ollama service for entity extraction

### Data Flow
```
Journal Entry → API → Temporal Workflow → Entity Extraction → Human Curation → Relationship Extraction → Knowledge Graph
```

## 📊 Entity Types

### Domain Entities (with UUIDs)
- **Person**: People mentioned in journal entries
- **Concept**: Abstract ideas and concepts (Zettelkasten-style)
- **Feeling**: Emotional states and experiences
- **Emotion**: Specific emotions with intensity levels
- **Event**: Activities and occurrences
- **Project**: Ongoing initiatives and goals
- **Content**: Books, articles, videos, etc.
- **Consumable**: Resources being consumed
- **Place**: Locations and places

### Processing Order
```python
processing_order = [
    "Person",         # People first (needed for emotions)
    "Concept",        # Concepts (needed for concept feelings)
    "Feeling",        # Emotions (require person context)
    "FeelingConcept", # Concept feelings (require person and concept context)
    "Project",        # Projects
    "Consumable",     # Consumables
    "Content",        # Content
    "Event",          # Events
    "Place",          # Places
]
```

## 🔧 Key Files & Locations

### Core Application Files
- **Main API**: `src/minerva_backend/api/main.py`
- **Configuration**: `src/minerva_backend/config.py`
- **Dependency Injection**: `src/minerva_backend/containers.py`
- **Database Connection**: `src/minerva_backend/graph/db.py`

### Processing Pipeline
- **Extraction Service**: `src/minerva_backend/processing/extraction_service.py`
- **Temporal Orchestrator**: `src/minerva_backend/processing/temporal_orchestrator.py`
- **LLM Service**: `src/minerva_backend/processing/llm_service.py`
- **Curation Manager**: `src/minerva_backend/processing/curation_manager.py`

### Entity Processing
- **Base Processor**: `src/minerva_backend/processing/extraction/processors/base.py`
- **Concept Processor**: `src/minerva_backend/processing/extraction/processors/concept_processor.py`
- **Entity Models**: `src/minerva_backend/graph/models/entities.py`
- **Relation Models**: `src/minerva_backend/graph/models/relations.py`

### Repositories
- **Base Repository**: `src/minerva_backend/graph/repositories/base.py`
- **Concept Repository**: `src/minerva_backend/graph/repositories/concept_repository.py`
- **Person Repository**: `src/minerva_backend/graph/repositories/person_repository.py`

## 🚀 Common Patterns

### Adding New Entity Type
1. **Create Entity Model** in `graph/models/entities.py`
2. **Create Repository** in `graph/repositories/`
3. **Create Processor** in `processing/extraction/processors/` (if needed)
4. **Update Processing Order** in `extraction_service.py`
5. **Update Database Schema** documentation

### Processing Pipeline Stages
1. **SUBMITTED**: Journal entry received
2. **ENTITY_PROCESSING**: Extracting entities
3. **SUBMIT_ENTITY_CURATION**: Queuing entities for curation
4. **WAIT_ENTITY_CURATION**: Waiting for human curation
5. **RELATION_PROCESSING**: Extracting relationships
6. **SUBMIT_RELATION_CURATION**: Queuing relationships for curation
7. **WAIT_RELATION_CURATION**: Waiting for relationship curation
8. **DB_WRITE**: Writing to knowledge graph
9. **COMPLETED**: Processing complete

### Error Handling Patterns
```python
# Service unavailable errors
try:
    result = await service.operation()
except ServiceUnavailableError as e:
    logger.error(f"Service unavailable: {e}")
    raise

# Processing errors
try:
    entities = await extract_entities(journal_entry)
except ProcessingError as e:
    logger.error(f"Processing failed: {e}")
    raise
```

### Dependency Injection Pattern
```python
# In containers.py
concept_repository = providers.Factory(
    ConceptRepository,
    connection=db_connection,
    llm_service=llm_service,
)

# In services
class SomeService:
    def __init__(self, concept_repository: ConceptRepository):
        self.concept_repository = concept_repository
```

## 🔍 Common Debugging Steps

### Service Issues
1. **Check health endpoints**: `curl http://localhost:8000/api/health`
2. **Check individual services**: Neo4j (7474), Ollama (11434), Temporal (7233)
3. **Check logs**: `tail -f logs/minerva_errors.log`
4. **Restart services** if needed

### Processing Issues
1. **Check LLM service**: `curl http://localhost:11434`
2. **Check processing logs**: `tail -f logs/minerva_performance.log`
3. **Test with simple data**: Use basic journal entry
4. **Check database connectivity**: Neo4j Browser

### Database Issues
1. **Check Neo4j**: `curl http://localhost:7474`
2. **Check database state**: Use Neo4j Browser
3. **Check indexes**: `CALL db.indexes()`
4. **Reinitialize if needed**: Run init_emotion_types()

## 📋 API Endpoints

### Core Endpoints
- **POST** `/api/journal/submit` - Submit journal entry
- **GET** `/api/pipeline/status/{workflow_id}` - Get pipeline status
- **GET** `/api/curation/pending` - Get pending curation items
- **POST** `/api/curation/complete-entity/{journal_id}` - Complete entity curation
- **GET** `/api/health` - System health check

### Error Responses
```json
{
  "success": false,
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable error message",
    "status_code": 400,
    "context": {
      "field": "additional context"
    }
  }
}
```

## 🧪 Testing Patterns

### Unit Tests
```python
# Test with mocked dependencies
@pytest.fixture
def test_container(mock_neo4j_connection, mock_llm_service):
    container = Container()
    container.db_connection.override(mock_neo4j_connection)
    container.llm_service.override(mock_llm_service)
    return container

def test_something(test_container):
    service = test_container.some_service()
    result = service.do_something()
    assert result is not None
```

### API Tests
```python
def test_api_endpoint(client):
    response = client.post("/api/endpoint", json={"data": "test"})
    assert response.status_code == 200
    assert response.json()["success"] is True
```

## 🔧 Configuration

### Required Environment Variables
```env
# Database
MINERVA_NEO4J_URI=bolt://localhost:7687
MINERVA_NEO4J_USER=neo4j
MINERVA_NEO4J_PASSWORD=Alxe342!

# Temporal
MINERVA_TEMPORAL_URI=localhost:7233

# API
MINERVA_DEBUG=true
MINERVA_LOG_LEVEL=DEBUG
MINERVA_HOST=0.0.0.0
MINERVA_PORT=8000
```

### Service URLs
- **API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **Neo4j Browser**: http://localhost:7474
- **Temporal Web UI**: http://localhost:8080

## 🎯 Common Tasks

### "How do I add a new entity type?"
1. Create entity model in `graph/models/entities.py`
2. Create repository in `graph/repositories/`
3. Create processor if needed
4. Update processing order
5. Update documentation

### "How do I debug processing issues?"
1. Check service health
2. Check processing logs
3. Test with simple data
4. Check database state

### "How do I add a new API endpoint?"
1. Add to appropriate router
2. Define request/response models
3. Implement business logic
4. Add error handling
5. Write tests
6. Update documentation

### "How do I test my changes?"
1. Write unit tests
2. Write integration tests
3. Run test suite: `poetry run pytest`
4. Check coverage: `poetry run pytest --cov=minerva_backend --cov-report=html`

## 🚨 Common Error Patterns

### Service Unavailable
- **Neo4j**: Check if running on port 7474/7687
- **Temporal**: Check if running on port 7233
- **Ollama**: Check if running on port 11434

### Processing Errors
- **LLM Service**: Check Ollama is running and has models
- **Database**: Check Neo4j connection and data
- **Temporal**: Check workflow execution

### Validation Errors
- **Input Data**: Check request format and required fields
- **Entity Data**: Check entity model validation
- **Configuration**: Check environment variables

## 📚 Key Documentation

### Architecture
- [System Overview](architecture/overview.md)
- [Processing Pipeline](architecture/processing-pipeline.md)
- [Database Schema](architecture/database-schema.md)
- [Dependency Injection](architecture/dependency-injection.md)

### Features
- [Concept Extraction](features/concept-extraction.md)
- [Concept Relations](features/concept-relations.md)
- [Temporal Serialization](features/temporal-serialization.md)
- [Field Comparison](features/field-comparison.md)

### Development
- [Setup Guide](development/setup.md)
- [Testing Guide](development/testing.md)
- [Onboarding Guide](development/onboarding.md)

### API
- [Endpoints](api/endpoints.md)
- [Error Codes](api/error-codes.md)

---

*This quick reference provides essential information for AI assistants to understand and work with the Minerva Backend system effectively.*
