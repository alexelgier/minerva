"""
Unit tests for concept relation extraction processor.

Tests the ConceptRelationProcessor with mocked dependencies.
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime

from minerva_backend.graph.models.documents import JournalEntry
from minerva_backend.graph.models.entities import Concept
from minerva_backend.graph.models.relations import ConceptRelationType, ConceptRelation
from minerva_backend.processing.extraction.context import ExtractionContext
from minerva_backend.processing.extraction.processors.concept_relation_processor import ConceptRelationProcessor
from minerva_backend.processing.models import EntityMapping, CuratableMapping


@pytest.fixture
def mock_llm_service():
    """Create mock LLM service."""
    mock = Mock()
    mock.generate = AsyncMock()
    return mock


@pytest.fixture
def mock_entity_repositories():
    """Create mock entity repositories."""
    mock_concept_repo = Mock()
    mock_concept_repo.find_relevant_concepts = AsyncMock(return_value=[])
    mock_concept_repo.get_concepts_with_recent_mentions = Mock(return_value=[])
    
    return {
        "Concept": mock_concept_repo,
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
def concept_relation_processor(mock_llm_service, mock_entity_repositories, mock_span_service, mock_obsidian_service):
    """Create ConceptRelationProcessor with mocked dependencies."""
    return ConceptRelationProcessor(
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
def mock_concept_entities():
    """Create mock concept entities for testing."""
    concept1 = Concept(
        name="existentialism",
        title="Existentialism",
        analysis="A philosophical concept that emphasizes individual existence, freedom, and choice",
        concept="Test concept content",
        source=None,
        summary_short="Philosophical concept about existence",
        summary="A philosophical concept that emphasizes individual existence, freedom, and choice"
    )
    concept2 = Concept(
        name="free will",
        title="Free Will",
        analysis="The ability to make choices that are not determined by prior causes",
        concept="Test concept content",
        source=None,
        summary_short="Concept of voluntary choice",
        summary="The ability to make choices that are not determined by prior causes"
    )
    
    return [
        EntityMapping(entity=concept1, spans=[]),
        EntityMapping(entity=concept2, spans=[])
    ]


@pytest.fixture
def mock_extraction_context(sample_journal_entry, mock_entity_repositories, mock_concept_entities):
    """Create mock extraction context."""
    mock_kg_service = Mock()
    mock_kg_service.entity_repositories = mock_entity_repositories
    
    context = ExtractionContext(
        journal_entry=sample_journal_entry,
        obsidian_entities={},
        kg_service=mock_kg_service
    )
    context.add_entities(mock_concept_entities)
    return context


class TestConceptRelationProcessorInitialization:
    """Test ConceptRelationProcessor initialization."""
    
    def test_initialization(self, concept_relation_processor):
        """Test that processor initializes correctly."""
        assert concept_relation_processor.llm_service is not None
        assert concept_relation_processor.entity_repositories is not None
        assert concept_relation_processor.span_service is not None
        assert concept_relation_processor.obsidian_service is not None


class TestConceptRelationProcessorProcess:
    """Test concept relation processing functionality."""
    
    @pytest.mark.asyncio
    async def test_process_success(self, concept_relation_processor, mock_extraction_context, mock_llm_service):
        """Test successful concept relation extraction."""
        # Arrange
        mock_relation1 = Mock()
        mock_relation1.type = ConceptRelationType.GENERALIZES
        mock_relation1.source_uuid = "concept1-uuid"
        mock_relation1.target_uuid = "concept2-uuid"
        
        mock_relation2 = Mock()
        mock_relation2.type = ConceptRelationType.RELATES_TO
        mock_relation2.source_uuid = "concept2-uuid"
        mock_relation2.target_uuid = "concept1-uuid"
        
        mock_response = Mock()
        mock_response.relations = [mock_relation1, mock_relation2]
        mock_llm_service.generate.return_value = mock_response
        
        # Mock span service
        concept_relation_processor.span_service.find_relation_spans = Mock(return_value=[])
        
        # Act
        result = await concept_relation_processor.process(mock_extraction_context)
        
        # Assert
        assert len(result) == 2  # 2 relations (GENERALIZES + reverse SPECIFIC_OF, RELATES_TO is symmetric)
        assert all(isinstance(rel, CuratableMapping) for rel in result)
        
        # Verify LLM service was called
        mock_llm_service.generate.assert_called()
    
    @pytest.mark.asyncio
    async def test_process_no_concepts(self, concept_relation_processor, sample_journal_entry, mock_entity_repositories):
        """Test processing when no concepts are found."""
        # Arrange
        mock_kg_service = Mock()
        mock_kg_service.entity_repositories = mock_entity_repositories
        
        context = ExtractionContext(
            journal_entry=sample_journal_entry,
            obsidian_entities={},
            kg_service=mock_kg_service
        )
        # No entities added to context
        
        # Act
        result = await concept_relation_processor.process(context)
        
        # Assert
        assert result == []
    
    @pytest.mark.asyncio
    async def test_process_llm_error(self, concept_relation_processor, mock_extraction_context, mock_llm_service):
        """Test processing when LLM service raises an error."""
        # Arrange
        mock_llm_service.generate.side_effect = Exception("LLM service error")
        
        # Act
        result = await concept_relation_processor.process(mock_extraction_context)
        
        # Assert
        assert result == []
    
    @pytest.mark.asyncio
    async def test_process_with_different_relation_types(self, concept_relation_processor, mock_extraction_context, mock_llm_service):
        """Test processing with different relation types."""
        # Arrange
        mock_relation1 = Mock()
        mock_relation1.type = ConceptRelationType.SUPPORTS
        mock_relation1.source_uuid = "concept1-uuid"
        mock_relation1.target_uuid = "concept2-uuid"
        
        mock_relation2 = Mock()
        mock_relation2.type = ConceptRelationType.OPPOSES
        mock_relation2.source_uuid = "concept2-uuid"
        mock_relation2.target_uuid = "concept1-uuid"
        
        mock_response = Mock()
        mock_response.relations = [mock_relation1, mock_relation2]
        mock_llm_service.generate.return_value = mock_response
        
        # Mock span service
        concept_relation_processor.span_service.find_relation_spans = Mock(return_value=[])
        
        # Act
        result = await concept_relation_processor.process(mock_extraction_context)
        
        # Assert
        assert len(result) == 2  # 2 relations (SUPPORTS + reverse SUPPORTED_BY, OPPOSES is symmetric)
        assert all(isinstance(rel, CuratableMapping) for rel in result)
    
    @pytest.mark.asyncio
    async def test_process_relation_validation(self, concept_relation_processor, mock_extraction_context, mock_llm_service):
        """Test that invalid relations are filtered out."""
        # Arrange
        mock_relation1 = Mock()
        mock_relation1.type = ConceptRelationType.GENERALIZES
        mock_relation1.source_uuid = "concept1-uuid"
        mock_relation1.target_uuid = "concept2-uuid"
        
        mock_relation2 = Mock()
        mock_relation2.type = "INVALID_TYPE"  # Invalid relation type
        mock_relation2.source_uuid = "concept1-uuid"
        mock_relation2.target_uuid = "concept2-uuid"
        
        mock_relation3 = Mock()
        mock_relation3.type = ConceptRelationType.RELATES_TO
        mock_relation3.source_uuid = "concept1-uuid"
        mock_relation3.target_uuid = "concept1-uuid"  # Self-connection (invalid)
        
        mock_response = Mock()
        mock_response.relations = [mock_relation1, mock_relation2, mock_relation3]
        mock_llm_service.generate.return_value = mock_response
        
        # Mock span service
        concept_relation_processor.span_service.find_relation_spans = Mock(return_value=[])
        
        # Act
        result = await concept_relation_processor.process(mock_extraction_context)
        
        # Assert
        assert len(result) == 2  # Only valid relation + its reverse
        assert all(isinstance(rel, CuratableMapping) for rel in result)


class TestConceptRelationProcessorHelperMethods:
    """Test helper methods of ConceptRelationProcessor."""
    
    def test_get_reverse_relation_type(self, concept_relation_processor):
        """Test reverse relation type mapping."""
        # Test bidirectional relations
        assert concept_relation_processor._get_reverse_relation_type("GENERALIZES") == "SPECIFIC_OF"
        assert concept_relation_processor._get_reverse_relation_type("SPECIFIC_OF") == "GENERALIZES"
        assert concept_relation_processor._get_reverse_relation_type("PART_OF") == "HAS_PART"
        assert concept_relation_processor._get_reverse_relation_type("HAS_PART") == "PART_OF"
        assert concept_relation_processor._get_reverse_relation_type("SUPPORTS") == "SUPPORTED_BY"
        assert concept_relation_processor._get_reverse_relation_type("SUPPORTED_BY") == "SUPPORTS"
        
        # Test symmetric relations (should return themselves)
        assert concept_relation_processor._get_reverse_relation_type("OPPOSES") == "OPPOSES"
        assert concept_relation_processor._get_reverse_relation_type("SIMILAR_TO") == "SIMILAR_TO"
        assert concept_relation_processor._get_reverse_relation_type("RELATES_TO") == "RELATES_TO"
    
    def test_validate_relation(self, concept_relation_processor):
        """Test relation validation."""
        # Valid relation
        valid_relation = Mock()
        valid_relation.type = ConceptRelationType.GENERALIZES
        valid_relation.source = "source-uuid"
        valid_relation.target = "target-uuid"
        assert concept_relation_processor._validate_relation(valid_relation) is True
        
        # Invalid relation type
        invalid_type_relation = Mock()
        invalid_type_relation.type = "INVALID_TYPE"
        invalid_type_relation.source = "source-uuid"
        invalid_type_relation.target = "target-uuid"
        assert concept_relation_processor._validate_relation(invalid_type_relation) is False
        
        # Self-connection (invalid)
        self_connection_relation = Mock()
        self_connection_relation.type = ConceptRelationType.GENERALIZES
        self_connection_relation.source = "same-uuid"
        self_connection_relation.target = "same-uuid"
        assert concept_relation_processor._validate_relation(self_connection_relation) is False
    
    def test_find_relation_spans(self, concept_relation_processor, sample_journal_entry):
        """Test finding relation spans in text."""
        # Test with a relation that should be found in the text
        relation_type = ConceptRelationType.GENERALIZES
        source_uuid = "concept1-uuid"
        target_uuid = "concept2-uuid"
        
        spans = concept_relation_processor._find_relation_spans(
            relation_type, source_uuid, target_uuid, sample_journal_entry.entry_text
        )
        
        # Should return empty list since we're not actually finding spans in this test
        assert isinstance(spans, list)
