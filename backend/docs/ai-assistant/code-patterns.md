# Code Patterns for AI Assistants

## 🏗️ Common Code Patterns

### Entity Model Pattern
```python
from pydantic import BaseModel, Field
from typing import Optional, List
from uuid import UUID, uuid4
from datetime import datetime

class Entity(BaseModel):
    """Base entity class with common fields."""
    uuid: str = Field(default_factory=lambda: str(uuid4()))
    name: str = Field(..., min_length=1)
    type: str = Field(..., description="Entity type")
    summary_short: str = Field(..., max_length=150)
    summary: str = Field(..., max_length=500)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    partition: str = Field(default="DOMAIN")
    embedding: Optional[List[float]] = Field(default=None)

class Person(Entity):
    """Person entity with specific fields."""
    type: str = Field(default="Person")
    name_embedding: Optional[List[float]] = Field(default=None)

class Concept(Entity):
    """Concept entity with Zettelkasten fields."""
    type: str = Field(default="Concept")
    title: str = Field(..., description="Zettel title")
    concept: str = Field(..., description="Main concept definition")
    analysis: str = Field(..., description="Zettel analysis content")
    source: Optional[str] = Field(default=None, description="Source reference")
```

### Repository Pattern
```python
from typing import List, Optional, Dict, Any
from abc import ABC, abstractmethod

class BaseRepository(ABC):
    """Base repository with common CRUD operations."""
    
    def __init__(self, connection: Neo4jConnection, llm_service: LLMService):
        self.connection = connection
        self.llm_service = llm_service
        self.entity_class = None  # Override in subclasses
    
    @abstractmethod
    async def create(self, entity: Entity) -> Entity:
        """Create a new entity."""
        pass
    
    @abstractmethod
    async def find_by_uuid(self, uuid: str) -> Optional[Entity]:
        """Find entity by UUID."""
        pass
    
    @abstractmethod
    async def find_by_name(self, name: str) -> Optional[Entity]:
        """Find entity by name."""
        pass
    
    async def vector_search(
        self, 
        query_text: str, 
        limit: int = 10, 
        threshold: float = 0.7
    ) -> List[Entity]:
        """Vector similarity search."""
        # Implementation for vector search
        pass

class PersonRepository(BaseRepository):
    """Person-specific repository."""
    
    def __init__(self, connection: Neo4jConnection, llm_service: LLMService):
        super().__init__(connection, llm_service)
        self.entity_class = Person
    
    async def create(self, person: Person) -> Person:
        """Create a new person."""
        # Implementation for creating person
        pass
```

### Processor Pattern
```python
from typing import List
from abc import ABC, abstractmethod

class BaseEntityProcessor(ABC):
    """Base processor for entity extraction."""
    
    def __init__(
        self,
        llm_service: LLMService,
        entity_repositories: Dict[str, BaseRepository],
        span_service: SpanProcessingService,
        obsidian_service: ObsidianService,
    ):
        self.llm_service = llm_service
        self.entity_repositories = entity_repositories
        self.span_service = span_service
        self.obsidian_service = obsidian_service
    
    @property
    @abstractmethod
    def entity_type(self) -> str:
        """Entity type this processor handles."""
        pass
    
    @abstractmethod
    async def process(self, context: ExtractionContext) -> List[EntityMapping]:
        """Process entities from journal entry."""
        pass
    
    async def _generate_embedding(self, text: str) -> List[float]:
        """Generate embedding for text."""
        return await self.llm_service.generate_embedding(text)

class PersonProcessor(BaseEntityProcessor):
    """Processor for Person entities."""
    
    @property
    def entity_type(self) -> str:
        return "Person"
    
    async def process(self, context: ExtractionContext) -> List[EntityMapping]:
        """Extract Person entities from journal entry."""
        # Implementation for person extraction
        pass
```

### Service Pattern
```python
from typing import List, Dict, Any
import logging

class ExtractionService:
    """Main service for entity extraction."""
    
    def __init__(
        self,
        connection: Neo4jConnection,
        llm_service: LLMService,
        obsidian_service: ObsidianService,
        kg_service: KnowledgeGraphService,
        entity_repositories: Dict[str, BaseRepository],
    ):
        self.connection = connection
        self.llm_service = llm_service
        self.obsidian_service = obsidian_service
        self.kg_service = kg_service
        self.entity_repositories = entity_repositories
        self.logger = logging.getLogger(__name__)
    
    async def extract_entities(self, journal_entry: JournalEntry) -> List[EntityMapping]:
        """Extract entities from journal entry."""
        try:
            self.logger.info(f"Starting entity extraction for journal {journal_entry.uuid}")
            
            # Create extraction context
            obsidian_entities = self.obsidian_service.build_entity_lookup(journal_entry)
            context = ExtractionContext(
                journal_entry=journal_entry,
                obsidian_entities=obsidian_entities,
                kg_service=self.kg_service,
            )
            
            # Process entities in order
            all_entities = []
            for entity_type in self.processing_order:
                processor = self.processor_factory.create_processor(entity_type)
                entities = await processor.process(context)
                all_entities.extend(entities)
            
            self.logger.info(f"Extracted {len(all_entities)} entities")
            return all_entities
            
        except Exception as e:
            self.logger.error(f"Entity extraction failed: {e}")
            raise ProcessingError(f"Failed to extract entities: {e}")
```

### Dependency Injection Pattern
```python
from dependency_injector import containers, providers

class Container(containers.DeclarativeContainer):
    """Main dependency injection container."""
    
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
    person_repository = providers.Factory(
        PersonRepository,
        connection=db_connection,
        llm_service=llm_service,
    )
    
    # Services with dependencies
    extraction_service = providers.Factory(
        ExtractionService,
        connection=db_connection,
        llm_service=llm_service,
        obsidian_service=obsidian_service,
        kg_service=kg_service,
        entity_repositories=entity_repositories,
    )
```

### API Endpoint Pattern
```python
from fastapi import APIRouter, Depends, HTTPException
from typing import List

router = APIRouter(prefix="/api/journal", tags=["journal"])

@router.post("/submit")
async def submit_journal(
    request: JournalSubmission,
    extraction_service: ExtractionService = Depends(get_extraction_service),
    pipeline_orchestrator: PipelineOrchestrator = Depends(get_pipeline_orchestrator),
) -> JSONResponse:
    """Submit journal entry for processing."""
    try:
        # Validate input
        if not request.entry_text.strip():
            raise HTTPException(
                status_code=400,
                detail="Journal text cannot be empty"
            )
        
        # Create journal entry
        journal_entry = JournalEntry.from_text(
            request.entry_text,
            request.entry_date
        )
        
        # Submit to pipeline
        workflow_id = await pipeline_orchestrator.submit_journal(journal_entry)
        
        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "message": "Journal entry submitted successfully",
                "workflow_id": workflow_id,
                "data": {
                    "journal_id": journal_entry.uuid,
                    "estimated_completion": "2024-01-15T18:00:00Z"
                }
            }
        )
        
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except ProcessingError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error")
```

### Error Handling Pattern
```python
from typing import Optional
import logging

class MinervaError(Exception):
    """Base exception for Minerva errors."""
    
    def __init__(self, message: str, context: Optional[Dict[str, Any]] = None):
        self.message = message
        self.context = context or {}
        super().__init__(self.message)

class ServiceUnavailableError(MinervaError):
    """Service is currently unavailable."""
    pass

class ProcessingError(MinervaError):
    """Processing operation failed."""
    pass

class ValidationError(MinervaError):
    """Validation failed."""
    pass

# Usage in services
async def some_operation(self):
    try:
        result = await external_service.call()
        return result
    except ConnectionError as e:
        self.logger.error(f"Service unavailable: {e}")
        raise ServiceUnavailableError(
            "External service is currently unavailable",
            context={"service": "external_service", "error": str(e)}
        )
    except ValueError as e:
        self.logger.error(f"Validation error: {e}")
        raise ValidationError(
            "Invalid input data",
            context={"field": "input_data", "error": str(e)}
        )
```

### Temporal Workflow Pattern
```python
from temporalio import workflow, activity
from typing import List

@workflow.defn(name="JournalProcessing")
class JournalProcessingWorkflow:
    """Temporal workflow for journal processing."""
    
    async def run(self, journal_entry: JournalEntry) -> PipelineState:
        """Main workflow execution."""
        try:
            # Stage 1: Entity Extraction
            entities = await workflow.execute_activity(
                PipelineActivities.extract_entities,
                args=[journal_entry],
                start_to_close_timeout=timedelta(minutes=60)
            )
            
            # Stage 2: Submit for Curation
            await workflow.execute_activity(
                PipelineActivities.submit_entity_curation,
                args=[journal_entry, entities],
                start_to_close_timeout=timedelta(minutes=10)
            )
            
            # Stage 3: Wait for Curation
            curated_entities = await workflow.execute_activity(
                PipelineActivities.wait_for_entity_curation,
                args=[journal_entry],
                start_to_close_timeout=timedelta(days=7)
            )
            
            # Stage 4: Relationship Extraction
            relationships = await workflow.execute_activity(
                PipelineActivities.extract_relationships,
                args=[journal_entry, curated_entities],
                start_to_close_timeout=timedelta(minutes=60)
            )
            
            # Stage 5: Write to Knowledge Graph
            await workflow.execute_activity(
                PipelineActivities.write_to_knowledge_graph,
                args=[journal_entry, curated_entities, relationships],
                start_to_close_timeout=timedelta(minutes=10)
            )
            
            return PipelineState.COMPLETED
            
        except Exception as e:
            workflow.logger.error(f"Workflow failed: {e}")
            return PipelineState.FAILED

class PipelineActivities:
    """Temporal activities for pipeline operations."""
    
    @activity.defn
    async def extract_entities(journal_entry: JournalEntry) -> List[EntityMapping]:
        """Extract entities - stateless activity."""
        from minerva_backend.containers import Container
        container = Container()
        return await container.extraction_service().extract_entities(journal_entry)
```

### Testing Pattern
```python
import pytest
from unittest.mock import Mock, AsyncMock, patch
from fastapi.testclient import TestClient

class TestExtractionService:
    """Test extraction service functionality."""
    
    @pytest.fixture
    def extraction_service(self, test_container):
        """Create real extraction service with mocked dependencies."""
        with patch('minerva_backend.processing.extraction_service.ProcessorFactory') as mock_factory:
            # Configure mocks
            mock_factory.create_all_processors.return_value = []
            
            # Create real service with mocked dependencies
            service = ExtractionService(
                connection=test_container.db_connection(),
                llm_service=test_container.llm_service(),
                obsidian_service=test_container.obsidian_service(),
                kg_service=test_container.kg_service(),
                entity_repositories=test_container.entity_repositories()
            )
            
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

class TestAPI:
    """Test API endpoints."""
    
    def test_submit_journal_success(self, client):
        """Test successful journal submission."""
        response = client.post("/api/journal/submit", json={
            "text": "Today I went to the park with John.",
            "date": "2024-01-15"
        })
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "workflow_id" in data
```

### Configuration Pattern
```python
from pydantic import BaseSettings, Field
from typing import List, Optional

class Settings(BaseSettings):
    """Application settings."""
    
    # Database Configuration
    NEO4J_URI: str = Field(default="bolt://localhost:7687")
    NEO4J_USER: str = Field(default="neo4j")
    NEO4J_PASSWORD: str = Field(default="password")
    CURATION_DB_PATH: str = Field(default="curation.db")
    
    # Temporal Configuration
    TEMPORAL_URI: str = Field(default="localhost:7233")
    
    # API Configuration
    DEBUG: bool = Field(default=False)
    LOG_LEVEL: str = Field(default="INFO")
    HOST: str = Field(default="0.0.0.0")
    PORT: int = Field(default=8000)
    
    # CORS Configuration
    CORS_ORIGINS: List[str] = Field(default=["http://localhost:3000", "http://localhost:5173"])
    CORS_ALLOW_CREDENTIALS: bool = Field(default=True)
    CORS_ALLOW_METHODS: List[str] = Field(default=["*"])
    CORS_ALLOW_HEADERS: List[str] = Field(default=["*"])
    
    # Processing Configuration
    DEFAULT_PROCESSING_START: str = Field(default="06:00")
    DEFAULT_PROCESSING_END: str = Field(default="12:00")
    MAX_STATUS_POLL_ATTEMPTS: int = Field(default=10)
    STATUS_POLL_INTERVAL: float = Field(default=0.2)
    
    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()
```

## 🔧 Common Utilities

### Logging Pattern
```python
import logging
from typing import Dict, Any

class PerformanceLogger:
    """Logger for performance metrics."""
    
    def __init__(self):
        self.logger = logging.getLogger("minerva_backend.performance")
    
    def log_processing_time(
        self, 
        operation: str, 
        duration_ms: float, 
        **context: Any
    ):
        """Log processing time with context."""
        self.logger.info(
            f"Processing time: {operation}",
            extra={
                "operation": operation,
                "duration_ms": duration_ms,
                **context
            }
        )

# Usage
performance_logger = PerformanceLogger()
performance_logger.log_processing_time(
    "entity_extraction",
    1500.0,
    journal_id="uuid-123",
    entity_count=5
)
```

### Validation Pattern
```python
from pydantic import BaseModel, Field, validator
from typing import Optional
from datetime import date

class JournalSubmission(BaseModel):
    """Journal submission request model."""
    
    entry_text: str = Field(..., min_length=1, max_length=10000)
    entry_date: str = Field(..., regex=r"^\d{4}-\d{2}-\d{2}$")
    
    @validator('entry_text')
    def validate_text(cls, v):
        if not v.strip():
            raise ValueError('Journal text cannot be empty')
        return v.strip()
    
    @validator('entry_date')
    def validate_date(cls, v):
        try:
            date.fromisoformat(v)
        except ValueError:
            raise ValueError('Invalid date format. Use YYYY-MM-DD')
        return v
```

---

*These code patterns provide templates and examples for common implementation tasks in the Minerva Backend system.*
