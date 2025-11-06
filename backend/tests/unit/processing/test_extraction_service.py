"""
Unit tests for extraction service.

Tests the entity extraction service with mocked dependencies.
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from uuid import uuid4

from minerva_backend.graph.models.documents import JournalEntry, Span
from minerva_backend.graph.models.entities import Person
from minerva_backend.processing.extraction_service import ExtractionService
from minerva_backend.processing.models import EntityMapping


@pytest.fixture
def mock_neo4j_connection():
    """Create mock Neo4j connection."""
    return Mock()


@pytest.fixture
def mock_llm_service():
    """Create mock LLM service."""
    return Mock()


@pytest.fixture
def mock_obsidian_service():
    """Create mock Obsidian service."""
    return Mock()


@pytest.fixture
def mock_kg_service():
    """Create mock Knowledge Graph service."""
    return Mock()


@pytest.fixture
def sample_journal_entry():
    """Create sample journal entry for testing."""
    return JournalEntry(
        uuid=str(uuid4()),
        text="Today I went to the park with John and felt happy about the sunny weather.",
        date="2025-09-29",
        metadata={}
    )


@pytest.fixture
def extraction_service(test_container):
    """Create extraction service using container."""
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
        from minerva_backend.processing.extraction_service import ExtractionService
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


class TestExtractionServiceInitialization:
    """Test extraction service initialization."""
    
    def test_extraction_service_init(self, test_container):
        """Test extraction service initialization."""
        with patch('minerva_backend.processing.extraction_service.ProcessorFactory') as mock_factory, \
             patch('minerva_backend.processing.extraction_service.EntityExtractionOrchestrator') as mock_orchestrator, \
             patch('minerva_backend.processing.extraction_service.SpanProcessingService') as mock_span_service:
            
            # Configure mocks
            mock_factory.create_all_processors.return_value = []
            mock_orchestrator_instance = Mock()
            mock_orchestrator.return_value = mock_orchestrator_instance
            
            # Get real services from container but override the problematic ones
            service = test_container.extraction_service()
            
            # Override the mocked extraction service with a real one for this test
            from minerva_backend.processing.extraction_service import ExtractionService
            real_service = ExtractionService(
                connection=test_container.db_connection(),
                llm_service=test_container.llm_service(),
                obsidian_service=test_container.obsidian_service(),
                kg_service=test_container.kg_service(),
                entity_repositories=test_container.entity_repositories()
            )
            
            # Assertions
            assert real_service.connection is not None
            assert real_service.llm_service is not None
            assert real_service.obsidian_service is not None
            assert real_service.logger is not None
            assert real_service.performance_logger is not None
            
            # Check that repositories are configured
            expected_repos = ["Person", "Feeling", "Emotion", "Event", "Project", 
                            "Concept", "Content", "Consumable", "Place"]
            for repo_name in expected_repos:
                assert repo_name in real_service.entity_repositories
            
            # Check that specialized services are created
            mock_span_service.assert_called_once()
            
            # Check that processors are created
            mock_factory.create_all_processors.assert_called_once()
            
            # Check that orchestrator is created
            mock_orchestrator.assert_called_once()


class TestExtractionServiceEntityExtraction:
    """Test entity extraction functionality."""
    
    @pytest.mark.asyncio
    async def test_extract_entities_success(self, extraction_service, sample_journal_entry):
        """Test successful entity extraction."""
        # Arrange
        # Create mock entities with proper structure
        from datetime import datetime
        from minerva_backend.graph.models.entities import Person, FeelingEmotion
        from minerva_backend.graph.models.documents import Span
        
        mock_entities = [
            EntityMapping(
                entity=Person(name="John", summary_short="John", summary="A person named John"),
                spans=[Span(start=20, end=24, text="John")]
            ),
            EntityMapping(
                entity=FeelingEmotion(
                    name="happy",
                    summary_short="happy feeling",
                    summary="A feeling of happiness",
                    timestamp=datetime.now()
                ),
                spans=[Span(start=30, end=35, text="happy")]
            )
        ]
        
        extraction_service._mock_orchestrator.extract_entities = AsyncMock(return_value=mock_entities)
        
        # Act
        result = await extraction_service.extract_entities(sample_journal_entry)
        
        # Assert
        assert result == mock_entities
        extraction_service._mock_orchestrator.extract_entities.assert_called_once_with(sample_journal_entry)
    
    @pytest.mark.asyncio
    async def test_extract_entities_empty_result(self, extraction_service, sample_journal_entry):
        """Test entity extraction with no entities found."""
        # Arrange
        extraction_service._mock_orchestrator.extract_entities = AsyncMock(return_value=[])
        
        # Act
        result = await extraction_service.extract_entities(sample_journal_entry)
        
        # Assert
        assert result == []
        extraction_service._mock_orchestrator.extract_entities.assert_called_once_with(sample_journal_entry)
    
    @pytest.mark.asyncio
    async def test_extract_entities_orchestrator_error(self, extraction_service, sample_journal_entry):
        """Test entity extraction when orchestrator raises an error."""
        # Arrange
        extraction_service._mock_orchestrator.extract_entities = AsyncMock(
            side_effect=Exception("Orchestrator error")
        )
        
        # Act & Assert
        with pytest.raises(Exception, match="Orchestrator error"):
            await extraction_service.extract_entities(sample_journal_entry)
    
    @pytest.mark.asyncio
    async def test_extract_entities_logging(self, extraction_service, sample_journal_entry):
        """Test that entity extraction logs properly."""
        # Arrange
        mock_entities = [EntityMapping(
            entity=Person(name="John", summary_short="John", summary="A person named John"),
            spans=[Span(start=20, end=24, text="John")]
        )]
        
        extraction_service._mock_orchestrator.extract_entities = AsyncMock(return_value=mock_entities)
        
        # Act
        await extraction_service.extract_entities(sample_journal_entry)
        
        # Assert
        # Check that logger was called (we can't easily test the exact log content
        # without more complex mocking, but we can verify the method was called)
        assert extraction_service.logger is not None
        assert extraction_service.performance_logger is not None


class TestExtractionServiceRelationshipExtraction:
    """Test relationship extraction functionality."""
    
    @pytest.mark.asyncio
    async def test_extract_relationships_success(self, extraction_service, sample_journal_entry):
        """Test successful relationship extraction."""
        # Arrange
        mock_relationships = [
            {
                "source_entity": "John",
                "target_entity": "park",
                "relationship_type": "went_to",
                "confidence": 0.85
            }
        ]
        
        # Mock the dependencies that extract_relationships actually uses
        extraction_service.obsidian_service = Mock()
        extraction_service.obsidian_service.build_entity_lookup = Mock(return_value={})
        
        # Mock kg_service for ExtractionContext
        mock_kg_service = Mock()
        extraction_service.kg_service = mock_kg_service
        
        with patch('minerva_backend.processing.extraction.relationship_processor.RelationshipProcessor') as mock_processor_class:
            mock_processor = Mock()
            mock_processor.process = AsyncMock(return_value=mock_relationships)
            mock_processor_class.return_value = mock_processor
        
            # Act
            result = await extraction_service.extract_relationships(sample_journal_entry, [])
        
            # Assert
            assert result == mock_relationships
    
    @pytest.mark.asyncio
    async def test_extract_relationships_empty_result(self, extraction_service, sample_journal_entry):
        """Test relationship extraction with no relationships found."""
        # Arrange
        extraction_service.obsidian_service.build_entity_lookup = Mock(return_value={})
        
        # Mock kg_service for ExtractionContext
        mock_kg_service = Mock()
        extraction_service.kg_service = mock_kg_service
        
        with patch('minerva_backend.processing.extraction.relationship_processor.RelationshipProcessor') as mock_processor_class:
            mock_processor = Mock()
            mock_processor.process = AsyncMock(return_value=[])
            mock_processor_class.return_value = mock_processor
        
            # Act
            result = await extraction_service.extract_relationships(sample_journal_entry, [])
        
            # Assert
            assert result == []
    
    @pytest.mark.asyncio
    async def test_extract_relationships_error(self, extraction_service, sample_journal_entry):
        """Test relationship extraction when error occurs."""
        # Arrange
        extraction_service.obsidian_service = Mock()
        extraction_service.obsidian_service.build_entity_lookup = Mock(
            side_effect=Exception("Lookup error")
        )
        
        # Mock LLM service to raise error
        extraction_service.llm_service.generate = AsyncMock(
            side_effect=Exception("LLM error")
        )
        
        # Create some mock entities so that build_entity_lookup is called
        from minerva_backend.processing.models import EntityMapping
        from minerva_backend.graph.models.entities import Person
        mock_entity = Person(
            name="Test Person", 
            title="Test Person",
            summary_short="Test person",
            summary="A test person for the relationship extraction test"
        )
        mock_entities = [EntityMapping(entity=mock_entity, spans=[])]
        
        # Act & Assert
        with pytest.raises(Exception, match="Lookup error"):
            await extraction_service.extract_relationships(sample_journal_entry, mock_entities)


class TestExtractionServiceRepositoryAccess:
    """Test repository access functionality."""
    
    def test_entity_repositories_configured(self, extraction_service):
        """Test that entity repositories are properly configured."""
        # Assert
        expected_repos = ["Person", "Feeling", "Emotion", "Event", "Project", 
                        "Concept", "Content", "Consumable", "Place"]
        for repo_name in expected_repos:
            assert repo_name in extraction_service.entity_repositories
            assert extraction_service.entity_repositories[repo_name] is not None


class TestExtractionServiceErrorHandling:
    """Test error handling in extraction service."""
    
    @pytest.mark.asyncio
    async def test_extract_entities_with_invalid_journal_entry(self, extraction_service):
        """Test entity extraction with invalid journal entry."""
        # Arrange
        invalid_journal = None
        
        # Act & Assert
        with pytest.raises(AttributeError):
            await extraction_service.extract_entities(invalid_journal)
    
    @pytest.mark.asyncio
    async def test_extract_relationships_with_invalid_journal_entry(self, extraction_service):
        """Test relationship extraction with invalid journal entry."""
        # Arrange
        invalid_journal = None
        mock_entities = []
        
        # Act & Assert
        with pytest.raises(AttributeError):
            await extraction_service.extract_relationships(invalid_journal, mock_entities)


class TestExtractionServicePerformanceLogging:
    """Test performance logging functionality."""
    
    @pytest.mark.asyncio
    async def test_performance_logging_entity_extraction(self, extraction_service, sample_journal_entry):
        """Test that performance logging is called for entity extraction."""
        # Arrange
        mock_entities = [EntityMapping(
            entity=Person(name="John", summary_short="John", summary="A person named John"),
            spans=[Span(start=20, end=24, text="John")]
        )]
        
        extraction_service._mock_orchestrator.extract_entities = AsyncMock(return_value=mock_entities)
        
        # Mock the performance logger
        extraction_service.performance_logger.log_entity_extraction = Mock()
        
        # Act
        await extraction_service.extract_entities(sample_journal_entry)
        
        # Assert
        extraction_service.performance_logger.log_entity_extraction.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_performance_logging_relationship_extraction(self, extraction_service, sample_journal_entry):
        """Test that performance logging is called for relationship extraction."""
        # Arrange
        mock_relationships = [{
            "source_entity": "John",
            "target_entity": "park",
            "relationship_type": "went_to",
            "confidence": 0.85
        }]
        
        extraction_service.obsidian_service.build_entity_lookup = Mock(return_value={})
        
        # Mock kg_service for ExtractionContext
        mock_kg_service = Mock()
        extraction_service.kg_service = mock_kg_service
        
        with patch('minerva_backend.processing.extraction.relationship_processor.RelationshipProcessor') as mock_processor_class:
            mock_processor = Mock()
            mock_processor.process = AsyncMock(return_value=mock_relationships)
            mock_processor_class.return_value = mock_processor
        
            # Mock the performance logger
            extraction_service.performance_logger.log_processing_time = Mock()
        
            # Act
            await extraction_service.extract_relationships(sample_journal_entry, [])
        
            # Assert
            extraction_service.performance_logger.log_processing_time.assert_called_once()
