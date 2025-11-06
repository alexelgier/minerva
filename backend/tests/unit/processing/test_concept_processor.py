"""
Unit tests for concept extraction processor.

Tests the ConceptProcessor with mocked dependencies.
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime

from minerva_backend.graph.models.documents import JournalEntry, Span
from minerva_backend.graph.models.entities import Concept
from minerva_backend.processing.extraction.context import ExtractionContext
from minerva_backend.processing.extraction.processors.concept_processor import ConceptProcessor
from minerva_backend.processing.models import EntityMapping


@pytest.fixture
def mock_llm_service():
    """Create mock LLM service."""
    mock = Mock()
    mock.generate = AsyncMock()
    return mock


@pytest.fixture
def mock_entity_repositories():
    """Create mock entity repositories."""
    return {
        "Concept": Mock(),
        "Person": Mock(),
        "Feeling": Mock(),
    }


@pytest.fixture
def mock_span_service():
    """Create mock span processing service."""
    return Mock()


@pytest.fixture
def mock_obsidian_service():
    """Create mock Obsidian service."""
    return Mock()


@pytest.fixture
def concept_processor(mock_llm_service, mock_entity_repositories, mock_span_service, mock_obsidian_service):
    """Create ConceptProcessor with mocked dependencies."""
    return ConceptProcessor(
        llm_service=mock_llm_service,
        entity_repositories=mock_entity_repositories,
        span_service=mock_span_service,
        obsidian_service=mock_obsidian_service
    )


@pytest.fixture
def sample_journal_entry():
    """Create a sample journal entry for testing."""
    return JournalEntry(
        uuid="test-uuid",
        text="I was thinking about existentialism and the meaning of life today. The concept of free will is fascinating.",
        entry_text="I was thinking about existentialism and the meaning of life today. The concept of free will is fascinating.",
        date="2025-09-29",
        metadata={}
    )


@pytest.fixture
def mock_extraction_context(sample_journal_entry, mock_entity_repositories):
    """Create mock extraction context."""
    mock_kg_service = Mock()
    mock_kg_service.entity_repositories = mock_entity_repositories
    
    return ExtractionContext(
        journal_entry=sample_journal_entry,
        obsidian_entities={},
        kg_service=mock_kg_service
    )


class TestConceptProcessorInitialization:
    """Test ConceptProcessor initialization."""
    
    def test_entity_type(self, concept_processor):
        """Test that entity type is correct."""
        assert concept_processor.entity_type == "Concept"


class TestConceptProcessorProcess:
    """Test concept processing functionality."""
    
    @pytest.mark.asyncio
    async def test_process_success(self, concept_processor, mock_extraction_context, mock_llm_service):
        """Test successful concept extraction."""
        # Arrange
        # Create mock concept objects with proper attributes
        mock_concept1 = Mock()
        mock_concept1.name = "existentialism"
        mock_concept1.title = "Existentialism"
        mock_concept1.spans = ["existentialism"]
        mock_concept1.existing_uuid = None
        mock_concept1.confidence = 0.9
        mock_concept1.concept = "A philosophical concept that emphasizes individual existence, freedom, and choice"
        mock_concept1.analysis = "A philosophical concept that emphasizes individual existence, freedom, and choice"
        mock_concept1.source = None
        mock_concept1.summary_short = "Philosophical concept about existence"
        mock_concept1.summary = "A philosophical concept that emphasizes individual existence, freedom, and choice"
        
        mock_concept2 = Mock()
        mock_concept2.name = "free will"
        mock_concept2.title = "Free Will"
        mock_concept2.spans = ["free will"]
        mock_concept2.existing_uuid = "existing-uuid-123"
        mock_concept2.confidence = 0.8
        mock_concept2.concept = "The ability to make choices that are not determined by prior causes"
        mock_concept2.analysis = "The ability to make choices that are not determined by prior causes"
        mock_concept2.source = None
        mock_concept2.summary_short = "Concept of voluntary choice"
        mock_concept2.summary = "The ability to make choices that are not determined by prior causes"
        
        mock_response = Mock()
        mock_response.concepts = [mock_concept1, mock_concept2]
        mock_llm_service.generate.return_value = mock_response
        
        # Mock concept repository for enhanced context
        mock_concept_repo = Mock()
        mock_concept_repo.find_relevant_concepts = AsyncMock(return_value=[])
        mock_concept_repo.get_concepts_with_recent_mentions = Mock(return_value=[])
        mock_extraction_context.kg_service.entity_repositories["Concept"] = mock_concept_repo
        
        # Mock obsidian service for linked concepts
        mock_extraction_context.obsidian_entities = {"db_entities": []}
        
        # Mock span service to return proper EntityMapping objects
        from minerva_backend.processing.models import EntityMapping
        from minerva_backend.graph.models.entities import Concept
        
        mock_entity1 = Concept(
            name="existentialism",
            title="Existentialism",
            analysis="A philosophical concept that emphasizes individual existence, freedom, and choice",
            concept="Test concept content",
            source=None,
            summary_short="Philosophical concept about existence",
            summary="A philosophical concept that emphasizes individual existence, freedom, and choice"
        )
        mock_entity2 = Concept(
            name="free will",
            title="Free Will",
            analysis="The ability to make choices that are not determined by prior causes",
            concept="Test concept content",
            source=None,
            summary_short="Concept of voluntary choice",
            summary="The ability to make choices that are not determined by prior causes"
        )
        
        concept_processor.span_service.process_spans = Mock(return_value=[
            EntityMapping(entity=mock_entity1, spans=[]),
            EntityMapping(entity=mock_entity2, spans=[])
        ])
        
        # Act
        result = await concept_processor.process(mock_extraction_context)
        
        # Assert
        assert len(result) == 2
        assert all(isinstance(entity, EntityMapping) for entity in result)
        assert all(isinstance(entity.entity, Concept) for entity in result)
        
        # Check first concept
        concept1 = result[0].entity
        assert concept1.name == "existentialism"
        assert concept1.title == "Existentialism"
        assert concept1.summary_short == "Philosophical concept about existence"
        assert concept1.analysis == "A philosophical concept that emphasizes individual existence, freedom, and choice"
        assert result[0].spans == []
        
        # Check second concept
        concept2 = result[1].entity
        assert concept2.name == "free will"
        assert concept2.title == "Free Will"
        assert concept2.summary_short == "Concept of voluntary choice"
        assert concept2.analysis == "The ability to make choices that are not determined by prior causes"
        assert result[1].spans == []
        
        # Verify LLM service was called (once for extraction, once for merging existing concept)
        assert mock_llm_service.generate.call_count == 2
        
        # Check first call (extraction)
        first_call = mock_llm_service.generate.call_args_list[0]
        assert "existentialism" in first_call[1]["prompt"]
        assert "free will" in first_call[1]["prompt"]
        
        # Check second call (merging)
        second_call = mock_llm_service.generate.call_args_list[1]
        assert "free will" in second_call[1]["prompt"]
    
    @pytest.mark.asyncio
    async def test_process_no_concepts(self, concept_processor, mock_extraction_context, mock_llm_service):
        """Test processing when no concepts are found."""
        # Arrange
        mock_response = Mock()
        mock_response.concepts = []
        mock_llm_service.generate.return_value = mock_response
        
        # Mock concept repository for enhanced context
        mock_concept_repo = Mock()
        mock_concept_repo.find_relevant_concepts = AsyncMock(return_value=[])
        mock_concept_repo.get_concepts_with_recent_mentions = Mock(return_value=[])
        mock_extraction_context.kg_service.entity_repositories["Concept"] = mock_concept_repo
        
        # Mock obsidian service for linked concepts
        mock_extraction_context.obsidian_entities = {"db_entities": []}
        
        # Act
        result = await concept_processor.process(mock_extraction_context)
        
        # Assert
        assert result == []
        mock_llm_service.generate.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_process_llm_error(self, concept_processor, mock_extraction_context, mock_llm_service):
        """Test processing when LLM service raises an error."""
        # Arrange
        mock_llm_service.generate.side_effect = Exception("LLM service error")
        
        # Mock concept repository for enhanced context
        mock_concept_repo = Mock()
        mock_concept_repo.find_relevant_concepts = AsyncMock(return_value=[])
        mock_concept_repo.get_concepts_with_recent_mentions = Mock(return_value=[])
        mock_extraction_context.kg_service.entity_repositories["Concept"] = mock_concept_repo
        
        # Mock obsidian service for linked concepts
        mock_extraction_context.obsidian_entities = {"db_entities": []}
        
        # Act
        result = await concept_processor.process(mock_extraction_context)
        
        # Assert
        assert result == []
    
    @pytest.mark.asyncio
    async def test_process_concept_context_error(self, concept_processor, mock_extraction_context, mock_llm_service):
        """Test processing when concept context retrieval fails."""
        # Arrange
        mock_response = Mock()
        mock_response.concepts = []
        mock_llm_service.generate.return_value = mock_response
        
        # Mock concept repository for enhanced context (with error)
        mock_concept_repo = Mock()
        mock_concept_repo.find_relevant_concepts = AsyncMock(side_effect=Exception("RAG error"))
        mock_concept_repo.get_concepts_with_recent_mentions = Mock(return_value=[])
        mock_extraction_context.kg_service.entity_repositories["Concept"] = mock_concept_repo
        
        # Mock obsidian service for linked concepts
        mock_extraction_context.obsidian_entities = {"db_entities": []}
        
        # Act
        result = await concept_processor.process(mock_extraction_context)
        
        # Assert
        assert result == []
        # Should still call LLM with fallback context
        mock_llm_service.generate.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_process_with_existing_concepts(self, concept_processor, mock_extraction_context, mock_llm_service):
        """Test processing with existing concepts (existing_uuid not None)."""
        # Arrange
        # Create mock concept object with proper attributes
        mock_concept = Mock()
        mock_concept.name = "existing concept"
        mock_concept.title = "Existing Concept"
        mock_concept.spans = ["existing concept"]
        mock_concept.existing_uuid = "existing-uuid-456"
        mock_concept.confidence = 0.9
        mock_concept.concept = "A concept that already exists in the database"
        mock_concept.analysis = "A concept that already exists in the database"
        mock_concept.source = None
        mock_concept.summary_short = "Existing concept"
        mock_concept.summary = "A concept that already exists in the database"
        
        mock_response = Mock()
        mock_response.concepts = [mock_concept]
        mock_llm_service.generate.return_value = mock_response
        
        # Mock concept repository for enhanced context
        mock_concept_repo = Mock()
        mock_concept_repo.find_relevant_concepts = AsyncMock(return_value=[])
        mock_concept_repo.get_concepts_with_recent_mentions = Mock(return_value=[])
        mock_extraction_context.kg_service.entity_repositories["Concept"] = mock_concept_repo
        
        # Mock obsidian service for linked concepts
        mock_extraction_context.obsidian_entities = {"db_entities": []}
        
        # Mock span service to return proper EntityMapping objects
        from minerva_backend.processing.models import EntityMapping
        from minerva_backend.graph.models.entities import Concept
        
        mock_entity = Concept(
            name="existing concept",
            title="Existing Concept",
            analysis="A concept that already exists in the database",
            concept="Test concept content",
            source=None,
            summary_short="Existing concept",
            summary="A concept that already exists in the database"
        )
        
        concept_processor.span_service.process_spans = Mock(return_value=[
            EntityMapping(entity=mock_entity, spans=[])
        ])
        
        # Act
        result = await concept_processor.process(mock_extraction_context)
        
        # Assert
        assert len(result) == 1
        concept = result[0].entity
        assert concept.name == "existing concept"
        assert concept.title == "Existing Concept"
        # Note: existing_uuid is not stored in the Concept entity itself,
        # it's used by the processor to determine if it's a new or existing concept
