"""
Unit tests for enhanced context system in ConceptProcessor.

Tests the enhanced concept context functionality.
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch

from minerva_backend.graph.models.documents import JournalEntry
from minerva_backend.graph.models.entities import Concept
from minerva_backend.processing.extraction.context import ExtractionContext
from minerva_backend.processing.extraction.processors.concept_processor import ConceptProcessor


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
        text="I was thinking about existentialism and the meaning of life today.",
        entry_text="I was thinking about existentialism and the meaning of life today.",
        date="2025-09-29",
        metadata={}
    )


@pytest.fixture
def mock_concept():
    """Create a mock concept for testing."""
    concept = Concept(
        name="existentialism",
        title="Existentialism",
        analysis="A philosophical concept that emphasizes individual existence, freedom, and choice",
        concept="Test concept content",
        source=None,
        summary_short="Philosophical concept about existence",
        summary="A philosophical concept that emphasizes individual existence, freedom, and choice"
    )
    return concept


class TestEnhancedConceptContext:
    """Test enhanced concept context functionality."""
    
    @pytest.mark.asyncio
    async def test_get_enhanced_concept_context_with_linked_concepts(self, concept_processor, sample_journal_entry, mock_concept):
        """Test getting enhanced context with linked concepts."""
        # Arrange
        mock_kg_service = Mock()
        mock_concept_repo = Mock()
        mock_concept_repo.find_relevant_concepts = AsyncMock(return_value=[])
        mock_concept_repo.get_concepts_with_recent_mentions = Mock(return_value=[])
        mock_concept_repo.find_by_uuid = Mock(return_value=mock_concept)
        # Mock the concept processor's concept_repository property
        concept_processor.entity_repositories = {"Concept": mock_concept_repo}
        
        obsidian_entities = {
            "db_entities": [
                Mock(entity_type="Concept", entity_id="concept-uuid-123")
            ]
        }
        
        context = ExtractionContext(
            journal_entry=sample_journal_entry,
            obsidian_entities=obsidian_entities,
            kg_service=mock_kg_service
        )
        
        # Act
        result = await concept_processor._get_enhanced_concept_context(context)
        
        # Assert
        assert isinstance(result, str)
        assert len(result) > 0
        assert "CONCEPTOS EXPLÍCITAMENTE MENCIONADOS" in result
        # Only linked concepts are present, no RAG/recent concepts
    
    @pytest.mark.asyncio
    async def test_get_enhanced_concept_context_with_rag_concepts(self, concept_processor, sample_journal_entry, mock_concept):
        """Test getting enhanced context with RAG concepts."""
        # Arrange
        mock_kg_service = Mock()
        mock_concept_repo = Mock()
        mock_concept_repo.find_relevant_concepts = AsyncMock(return_value=[mock_concept])
        mock_concept_repo.get_concepts_with_recent_mentions = Mock(return_value=[])
        # Mock the concept processor's concept_repository property
        concept_processor.entity_repositories = {"Concept": mock_concept_repo}
        
        context = ExtractionContext(
            journal_entry=sample_journal_entry,
            obsidian_entities={"db_entities": []},
            kg_service=mock_kg_service
        )
        
        # Act
        result = await concept_processor._get_enhanced_concept_context(context)
        
        # Assert
        assert isinstance(result, str)
        assert len(result) > 0
        assert "Existentialism" in result
        mock_concept_repo.find_relevant_concepts.assert_called_once_with(
            sample_journal_entry.entry_text, limit=10
        )
    
    @pytest.mark.asyncio
    async def test_get_enhanced_concept_context_with_recent_concepts(self, concept_processor, sample_journal_entry, mock_concept):
        """Test getting enhanced context with recent concepts."""
        # Arrange
        mock_kg_service = Mock()
        mock_concept_repo = Mock()
        mock_concept_repo.find_relevant_concepts = AsyncMock(return_value=[])
        mock_concept_repo.get_concepts_with_recent_mentions = Mock(return_value=[mock_concept])
        # Mock the concept processor's concept_repository property
        concept_processor.entity_repositories = {"Concept": mock_concept_repo}
        
        context = ExtractionContext(
            journal_entry=sample_journal_entry,
            obsidian_entities={"db_entities": []},
            kg_service=mock_kg_service
        )
        
        # Act
        result = await concept_processor._get_enhanced_concept_context(context)
        
        # Assert
        assert isinstance(result, str)
        assert len(result) > 0
        assert "Existentialism" in result
        mock_concept_repo.get_concepts_with_recent_mentions.assert_called_once_with(days=30)
    
    @pytest.mark.asyncio
    async def test_get_enhanced_concept_context_error_handling(self, concept_processor, sample_journal_entry):
        """Test error handling in enhanced context retrieval."""
        # Arrange
        mock_kg_service = Mock()
        mock_concept_repo = Mock()
        mock_concept_repo.find_relevant_concepts = AsyncMock(side_effect=Exception("RAG error"))
        mock_concept_repo.get_concepts_with_recent_mentions = Mock(side_effect=Exception("Recent error"))
        # Mock the concept processor's concept_repository property
        concept_processor.entity_repositories = {"Concept": mock_concept_repo}
        
        context = ExtractionContext(
            journal_entry=sample_journal_entry,
            obsidian_entities={"db_entities": []},
            kg_service=mock_kg_service
        )
        
        # Act
        result = await concept_processor._get_enhanced_concept_context(context)
        
        # Assert
        assert result == "No concept context available."
    
    def test_format_context(self, concept_processor, mock_concept):
        """Test context formatting."""
        # Arrange
        linked_concepts = [mock_concept]
        rag_concepts = [mock_concept]
        recent_concepts = [mock_concept]
        
        # Act
        result = concept_processor._format_context(linked_concepts, rag_concepts, recent_concepts)
        
        # Assert
        assert isinstance(result, str)
        assert "CONCEPTOS EXPLÍCITAMENTE MENCIONADOS" in result
        assert "CONCEPTOS RELACIONADOS DE TU BASE DE CONOCIMIENTO" in result
        assert "Existentialism" in result
    
    def test_format_context_empty_lists(self, concept_processor):
        """Test context formatting with empty lists."""
        # Arrange
        linked_concepts = []
        rag_concepts = []
        recent_concepts = []

        # Act
        result = concept_processor._format_context(linked_concepts, rag_concepts, recent_concepts)

        # Assert
        assert isinstance(result, str)
        assert result == ""  # Empty lists should return empty string
    
    def test_format_context_with_limits(self, concept_processor, mock_concept):
        """Test context formatting respects limits."""
        # Arrange
        # Create more concepts than the limit
        many_concepts = [mock_concept] * 15
        linked_concepts = many_concepts
        rag_concepts = many_concepts
        recent_concepts = many_concepts
        
        # Act
        result = concept_processor._format_context(linked_concepts, rag_concepts, recent_concepts)
        
        # Assert
        assert isinstance(result, str)
        # Should limit to 10 concepts per section
        assert result.count("existentialism") <= 30  # 10 per section * 3 sections


class TestConceptMerging:
    """Test concept merging functionality."""
    
    @pytest.mark.asyncio
    async def test_merge_with_existing_concept(self, concept_processor, mock_llm_service, mock_concept):
        """Test merging with existing concept."""
        # Arrange
        concept_mention = Mock()
        concept_mention.name = "free will"
        concept_mention.title = "Free Will"
        concept_mention.concept = "New concept definition"
        concept_mention.analysis = "New analysis"
        concept_mention.source = "New source"
        concept_mention.summary_short = "New short summary"
        concept_mention.summary = "New detailed summary"
        concept_mention.existing_uuid = "existing-uuid-123"
        
        mock_concept_repo = Mock()
        mock_concept_repo.find_by_uuid = Mock(return_value=mock_concept)
        
        # Mock merged concept response
        mock_merged_concept = Mock()
        mock_merged_concept.title = "Merged Title"
        mock_merged_concept.concept = "Merged concept definition"
        mock_merged_concept.analysis = "Merged analysis"
        mock_merged_concept.source = "Merged source"
        mock_merged_concept.summary_short = "Merged short summary"
        mock_merged_concept.summary = "Merged detailed summary"
        
        mock_llm_service.generate.return_value = mock_merged_concept
        
        # Act
        result = await concept_processor._merge_with_existing_concept(concept_mention, mock_concept_repo)
        
        # Assert
        assert result == mock_concept
        assert mock_concept.title == "Merged Title"
        assert mock_concept.concept == "Merged concept definition"
        assert mock_concept.analysis == "Merged analysis"
        assert mock_concept.source == "Merged source"
        assert mock_concept.summary_short == "Merged short summary"
        assert mock_concept.summary == "Merged detailed summary"
        
        # Verify LLM was called with correct prompt
        mock_llm_service.generate.assert_called_once()
        call_args = mock_llm_service.generate.call_args
        assert "free will" in call_args[1]["prompt"]
        assert "Existentialism" in call_args[1]["prompt"]  # Existing concept title
    
    @pytest.mark.asyncio
    async def test_merge_with_existing_concept_llm_error(self, concept_processor, mock_llm_service, mock_concept):
        """Test merging when LLM service raises an error."""
        # Arrange
        concept_mention = Mock()
        concept_mention.name = "free will"
        concept_mention.title = "Free Will"
        concept_mention.concept = "New concept definition"
        concept_mention.analysis = "New analysis"
        concept_mention.source = "New source"
        concept_mention.summary_short = "New short summary"
        concept_mention.summary = "New detailed summary"
        concept_mention.existing_uuid = "existing-uuid-123"
        
        mock_concept_repo = Mock()
        mock_concept_repo.find_by_uuid = Mock(return_value=mock_concept)
        
        mock_llm_service.generate.side_effect = Exception("LLM error")
        
        # Act & Assert
        with pytest.raises(Exception, match="LLM error"):
            await concept_processor._merge_with_existing_concept(concept_mention, mock_concept_repo)
