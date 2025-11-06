"""
Unit tests for concept feeling extraction processor.

Tests the ConceptFeelingProcessor with mocked dependencies.
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime, timedelta

from minerva_backend.graph.models.documents import JournalEntry, Span
from minerva_backend.graph.models.entities import FeelingConcept
from minerva_backend.processing.extraction.context import ExtractionContext
from minerva_backend.processing.extraction.processors.concept_feeling_processor import ConceptFeelingProcessor
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
        "FeelingConcept": Mock(),
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
def concept_feeling_processor(mock_llm_service, mock_entity_repositories, mock_span_service, mock_obsidian_service):
    """Create ConceptFeelingProcessor with mocked dependencies."""
    return ConceptFeelingProcessor(
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
        text="I was thinking about existentialism and felt inspired by the concept of free will. The idea of determinism worries me.",
        entry_text="I was thinking about existentialism and felt inspired by the concept of free will. The idea of determinism worries me.",
        date="2025-09-29",
        metadata={}
    )


@pytest.fixture
def mock_extraction_context(sample_journal_entry, mock_entity_repositories):
    """Create mock extraction context with people and concepts."""
    mock_kg_service = Mock()
    mock_kg_service.entity_repositories = mock_entity_repositories
    
    context = ExtractionContext(
        journal_entry=sample_journal_entry,
        obsidian_entities={},
        kg_service=mock_kg_service
    )
    
    # Mock the context methods directly
    context.get_people_context_string = Mock(return_value="Alex (UUID: person-uuid-123)")
    context.get_concepts_context_string = Mock(return_value=[
        {"name": "existentialism", "uuid": "concept-uuid-456"},
        {"name": "free will", "uuid": "concept-uuid-789"},
        {"name": "determinism", "uuid": "concept-uuid-101"}
    ])
    
    return context


class TestConceptFeelingProcessorInitialization:
    """Test ConceptFeelingProcessor initialization."""
    
    def test_entity_type(self, concept_feeling_processor):
        """Test that entity type is correct."""
        assert concept_feeling_processor.entity_type == "FeelingConcept"


class TestConceptFeelingProcessorProcess:
    """Test concept feeling processing functionality."""
    
    @pytest.mark.asyncio
    async def test_process_success(self, concept_feeling_processor, mock_extraction_context, mock_llm_service):
        """Test successful concept feeling extraction."""
        # Arrange
        # Create mock concept feeling objects with proper attributes
        mock_feeling1 = Mock()
        mock_feeling1.person_uuid = "person-uuid-123"
        mock_feeling1.concept_uuid = "concept-uuid-456"
        mock_feeling1.spans = ["felt inspired by"]
        mock_feeling1.timestamp = datetime(2025, 9, 29, 10, 0, 0)
        mock_feeling1.intensity = 8
        mock_feeling1.duration = timedelta(minutes=30)
        mock_feeling1.summary_short = "Inspired by existentialism"
        mock_feeling1.summary = "FeelingConcept inspired by the concept of existentialism and its emphasis on individual freedom"
        
        mock_feeling2 = Mock()
        mock_feeling2.person_uuid = "person-uuid-123"
        mock_feeling2.concept_uuid = "concept-uuid-101"
        mock_feeling2.spans = ["worries me"]
        mock_feeling2.timestamp = datetime(2025, 9, 29, 10, 0, 0)
        mock_feeling2.intensity = 6
        mock_feeling2.duration = None
        mock_feeling2.summary_short = "Worried about determinism"
        mock_feeling2.summary = "FeelingConcept worried about the concept of determinism and its implications for free will"
        
        mock_response = Mock()
        mock_response.concept_feelings = [mock_feeling1, mock_feeling2]
        mock_llm_service.generate.return_value = mock_response
        
        # Mock span service to return proper EntityMapping objects
        from minerva_backend.processing.models import EntityMapping
        from minerva_backend.graph.models.entities import FeelingConcept
        
        mock_entity1 = FeelingConcept(
            name="Sentimiento sobre concepto",
            timestamp=datetime(2025, 9, 29, 10, 0, 0),
            intensity=8,
            duration=timedelta(minutes=30),
            concept_uuid="concept-uuid-456",
            person_uuid="person-uuid-123",
            summary_short="Inspired by existentialism",
            summary="FeelingConcept inspired by the concept of existentialism and its emphasis on individual freedom"
        )
        mock_entity2 = FeelingConcept(
            name="Sentimiento sobre concepto",
            timestamp=datetime(2025, 9, 29, 10, 0, 0),
            intensity=6,
            duration=None,
            concept_uuid="concept-uuid-101",
            person_uuid="person-uuid-123",
            summary_short="Worried about determinism",
            summary="FeelingConcept worried about the concept of determinism and its implications for free will"
        )
        
        concept_feeling_processor.span_service.process_spans = Mock(return_value=[
            EntityMapping(entity=mock_entity1, spans=[]),
            EntityMapping(entity=mock_entity2, spans=[])
        ])
        
        # Act
        result = await concept_feeling_processor.process(mock_extraction_context)
        
        # Assert
        assert len(result) == 2
        assert all(isinstance(entity, EntityMapping) for entity in result)
        assert all(isinstance(entity.entity, FeelingConcept) for entity in result)
        
        # Check first feeling
        feeling1 = result[0].entity
        assert feeling1.name == "Sentimiento sobre concepto"
        assert feeling1.person_uuid == "person-uuid-123"
        assert feeling1.concept_uuid == "concept-uuid-456"
        assert feeling1.intensity == 8
        assert feeling1.duration == timedelta(minutes=30)
        assert feeling1.summary_short == "Inspired by existentialism"
        assert feeling1.summary == "FeelingConcept inspired by the concept of existentialism and its emphasis on individual freedom"
        assert result[0].spans == []
        
        # Check second feeling
        feeling2 = result[1].entity
        assert feeling2.name == "Sentimiento sobre concepto"
        assert feeling2.person_uuid == "person-uuid-123"
        assert feeling2.concept_uuid == "concept-uuid-101"
        assert feeling2.intensity == 6
        assert feeling2.duration is None
        assert feeling2.summary_short == "Worried about determinism"
        assert feeling2.summary == "FeelingConcept worried about the concept of determinism and its implications for free will"
        assert result[1].spans == []
        
        # Verify LLM service was called
        mock_llm_service.generate.assert_called_once()
        call_args = mock_llm_service.generate.call_args
        assert "existentialism" in call_args[1]["prompt"]
        assert "free will" in call_args[1]["prompt"]
        assert "determinism" in call_args[1]["prompt"]
    
    @pytest.mark.asyncio
    async def test_process_no_concept_feelings(self, concept_feeling_processor, mock_extraction_context, mock_llm_service):
        """Test processing when no concept feelings are found."""
        # Arrange
        mock_response = Mock()
        mock_response.concept_feelings = []
        mock_llm_service.generate.return_value = mock_response
        
        # Mock span service to return empty list
        concept_feeling_processor.span_service.process_spans = Mock(return_value=[])
        
        # Act
        result = await concept_feeling_processor.process(mock_extraction_context)
        
        # Assert
        assert result == []
        mock_llm_service.generate.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_process_no_people_context(self, concept_feeling_processor, sample_journal_entry, mock_entity_repositories, mock_llm_service):
        """Test processing when no people context is available."""
        # Arrange
        mock_kg_service = Mock()
        mock_kg_service.entity_repositories = mock_entity_repositories
        
        context = ExtractionContext(
            journal_entry=sample_journal_entry,
            obsidian_entities={},
            kg_service=mock_kg_service
        )
        
        # Mock empty people context
        context.get_people_context_string = Mock(return_value="")
        context.get_concepts_context_string = Mock(return_value=[
            {"name": "existentialism", "uuid": "concept-uuid-456"}
        ])
        
        # Act
        result = await concept_feeling_processor.process(context)
        
        # Assert
        assert result == []
        mock_llm_service.generate.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_process_no_concepts_context(self, concept_feeling_processor, sample_journal_entry, mock_entity_repositories, mock_llm_service):
        """Test processing when no concepts context is available."""
        # Arrange
        mock_kg_service = Mock()
        mock_kg_service.entity_repositories = mock_entity_repositories
        
        context = ExtractionContext(
            journal_entry=sample_journal_entry,
            obsidian_entities={},
            kg_service=mock_kg_service
        )
        
        # Mock people context
        context.get_people_context_string = Mock(return_value="Alex (UUID: person-uuid-123)")
        # Mock empty concepts context
        context.get_concepts_context_string = Mock(return_value=[])
        
        # Act
        result = await concept_feeling_processor.process(context)
        
        # Assert
        assert result == []
        mock_llm_service.generate.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_process_llm_error(self, concept_feeling_processor, mock_extraction_context, mock_llm_service):
        """Test processing when LLM service raises an error."""
        # Arrange
        mock_llm_service.generate.side_effect = Exception("LLM service error")
        
        # Act
        result = await concept_feeling_processor.process(mock_extraction_context)
        
        # Assert
        assert result == []
    
    @pytest.mark.asyncio
    async def test_process_with_intensity_and_duration(self, concept_feeling_processor, mock_extraction_context, mock_llm_service):
        """Test processing with various intensity and duration values."""
        # Arrange
        # Create mock concept feeling objects with proper attributes
        mock_feeling1 = Mock()
        mock_feeling1.person_uuid = "person-uuid-123"
        mock_feeling1.concept_uuid = "concept-uuid-456"
        mock_feeling1.spans = ["felt strongly about"]
        mock_feeling1.timestamp = datetime(2025, 9, 29, 10, 0, 0)
        mock_feeling1.intensity = 10  # Maximum intensity
        mock_feeling1.duration = timedelta(hours=2)  # Long duration
        mock_feeling1.summary_short = "Very strong feeling"
        mock_feeling1.summary = "A very intense and long-lasting feeling about the concept"
        
        mock_feeling2 = Mock()
        mock_feeling2.person_uuid = "person-uuid-123"
        mock_feeling2.concept_uuid = "concept-uuid-789"
        mock_feeling2.spans = ["briefly thought about"]
        mock_feeling2.timestamp = datetime(2025, 9, 29, 10, 0, 0)
        mock_feeling2.intensity = 2  # Low intensity
        mock_feeling2.duration = timedelta(minutes=5)  # Short duration
        mock_feeling2.summary_short = "Brief thought"
        mock_feeling2.summary = "A brief and mild thought about the concept"
        
        mock_response = Mock()
        mock_response.concept_feelings = [mock_feeling1, mock_feeling2]
        mock_llm_service.generate.return_value = mock_response
        
        # Mock span service to return proper EntityMapping objects
        from minerva_backend.processing.models import EntityMapping
        from minerva_backend.graph.models.entities import FeelingConcept
        
        mock_entity1 = FeelingConcept(
            name="Sentimiento sobre concepto",
            timestamp=datetime(2025, 9, 29, 10, 0, 0),
            intensity=10,
            duration=timedelta(hours=2),
            concept_uuid="concept-uuid-456",
            person_uuid="person-uuid-123",
            summary_short="Very strong feeling",
            summary="A very intense and long-lasting feeling about the concept"
        )
        mock_entity2 = FeelingConcept(
            name="Sentimiento sobre concepto",
            timestamp=datetime(2025, 9, 29, 10, 0, 0),
            intensity=2,
            duration=timedelta(minutes=5),
            concept_uuid="concept-uuid-789",
            person_uuid="person-uuid-123",
            summary_short="Brief thought",
            summary="A brief and mild thought about the concept"
        )
        
        concept_feeling_processor.span_service.process_spans = Mock(return_value=[
            EntityMapping(entity=mock_entity1, spans=[]),
            EntityMapping(entity=mock_entity2, spans=[])
        ])
        
        # Act
        result = await concept_feeling_processor.process(mock_extraction_context)
        
        # Assert
        assert len(result) == 2
        
        # Check first feeling (high intensity, long duration)
        feeling1 = result[0].entity
        assert feeling1.intensity == 10
        assert feeling1.duration == timedelta(hours=2)
        
        # Check second feeling (low intensity, short duration)
        feeling2 = result[1].entity
        assert feeling2.intensity == 2
        assert feeling2.duration == timedelta(minutes=5)
