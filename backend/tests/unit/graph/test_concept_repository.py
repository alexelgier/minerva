"""
Unit tests for concept repository with RAG functionality.

Tests the ConceptRepository with mocked dependencies.
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime

from minerva_backend.graph.models.entities import Concept
from minerva_backend.graph.repositories.concept_repository import ConceptRepository


@pytest.fixture
def mock_neo4j_connection():
    """Create mock Neo4j connection."""
    from unittest.mock import MagicMock
    mock = MagicMock()
    mock_session = AsyncMock()
    
    # Mock async session context manager
    mock_context_manager = AsyncMock()
    mock_context_manager.__aenter__ = AsyncMock(return_value=mock_session)
    mock_context_manager.__aexit__ = AsyncMock(return_value=None)
    mock.session_async = MagicMock(return_value=mock_context_manager)
    
    return mock


@pytest.fixture
def mock_llm_service():
    """Create mock LLM service."""
    mock = Mock()
    mock.create_embedding = AsyncMock(return_value=[0.1, 0.2, 0.3] * 341 + [0.1])  # Dummy 1024-dim vector
    return mock


@pytest.fixture
def concept_repository(mock_neo4j_connection, mock_llm_service):
    """Create ConceptRepository with mocked dependencies."""
    return ConceptRepository(
        connection=mock_neo4j_connection,
        llm_service=mock_llm_service
    )


@pytest.fixture
def sample_concept():
    """Create a sample concept for testing."""
    return Concept(
        name="existentialism",
        title="Existentialism",
        concept="A philosophical concept about individual existence and freedom",
        analysis="A philosophical concept about individual existence and freedom",
        source="Philosophy textbook",
        summary_short="Philosophical concept about existence",
        summary="A philosophical concept that emphasizes individual existence, freedom, and choice"
    )


class TestConceptRepositoryInitialization:
    """Test ConceptRepository initialization."""
    
    def test_entity_label(self, concept_repository):
        """Test that entity label is correct."""
        assert concept_repository.entity_label == "Concept"
    
    def test_entity_class(self, concept_repository):
        """Test that entity class is correct."""
        assert concept_repository.entity_class == Concept


class TestConceptRepositoryRAGMethods:
    """Test RAG functionality methods."""
    
    @pytest.mark.asyncio
    async def test_find_relevant_concepts_success(self, concept_repository, mock_llm_service):
        """Test finding relevant concepts using vector search."""
        # Arrange
        journal_text = "I was thinking about existentialism and free will today."
        
        # Mock vector search to return sample concepts
        with patch.object(concept_repository, 'vector_search') as mock_vector_search:
            mock_concepts = [
                Concept(
                    name="existentialism",
                    title="Existentialism",
                    concept="Philosophical concept",
                    analysis="Philosophical concept",
                    source=None,
                    summary_short="Philosophical concept",
                    summary="A philosophical concept about existence"
                ),
                Concept(
                    name="free will",
                    title="Free Will",
                    concept="Concept of choice",
                    analysis="Concept of choice",
                    source=None,
                    summary_short="Concept of choice",
                    summary="The ability to make voluntary choices"
                )
            ]
            mock_vector_search.return_value = mock_concepts
            
            # Act
            result = await concept_repository.find_relevant_concepts(journal_text, limit=5)
            
            # Assert
            assert len(result) == 2
            assert all(isinstance(concept, Concept) for concept in result)
            assert result[0].name == "existentialism"
            assert result[1].name == "free will"
            
            # Verify vector search was called with correct parameters
            mock_vector_search.assert_called_once_with(
                query_text=journal_text,
                limit=5,
                threshold=0.6
            )
    
    @pytest.mark.asyncio
    async def test_find_relevant_concepts_empty_result(self, concept_repository, mock_llm_service):
        """Test finding relevant concepts when no matches are found."""
        # Arrange
        journal_text = "Random text with no relevant concepts."
        
        with patch.object(concept_repository, 'vector_search') as mock_vector_search:
            mock_vector_search.return_value = []
            
            # Act
            result = await concept_repository.find_relevant_concepts(journal_text)
            
            # Assert
            assert result == []
            mock_vector_search.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_find_relevant_concepts_error(self, concept_repository, mock_llm_service):
        """Test finding relevant concepts when vector search fails."""
        # Arrange
        journal_text = "Test text"
        
        with patch.object(concept_repository, 'vector_search') as mock_vector_search:
            mock_vector_search.side_effect = Exception("Vector search error")
            
            # Act
            result = await concept_repository.find_relevant_concepts(journal_text)
            
            # Assert
            assert result == []
    
    @pytest.mark.asyncio
    async def test_get_concept_context_success(self, concept_repository, mock_llm_service):
        """Test getting concept context for LLM prompts."""
        # Arrange
        journal_text = "I was thinking about philosophy today."
        
        with patch.object(concept_repository, 'find_relevant_concepts') as mock_find_concepts:
            mock_concepts = [
                Concept(
                    name="existentialism",
                    title="Existentialism",
                    concept="A philosophical concept that emphasizes individual existence, freedom, and choice. It explores the meaning of life and human responsibility.",
                    analysis="A philosophical concept that emphasizes individual existence, freedom, and choice. It explores the meaning of life and human responsibility.",
                    source=None,
                    summary_short="Philosophical concept about existence",
                    summary="A philosophical concept that emphasizes individual existence, freedom, and choice"
                ),
                Concept(
                    name="free will",
                    title="Free Will",
                    concept="The ability to make choices that are not determined by prior causes or divine intervention.",
                    analysis="The ability to make choices that are not determined by prior causes or divine intervention.",
                    source=None,
                    summary_short="Concept of voluntary choice",
                    summary="The ability to make voluntary choices"
                )
            ]
            mock_find_concepts.return_value = mock_concepts
            
            # Act
            result = await concept_repository.get_concept_context(journal_text, limit=3)
            
            # Assert
            assert "Relevant concepts from your knowledge base:" in result
            assert "**Existentialism**" in result
            assert "**Free Will**" in result
            assert "Philosophical concept about existence" in result
            assert "Concept of voluntary choice" in result
            assert "A philosophical concept that emphasizes individual existence" in result
            assert "The ability to make choices that are not determined by prior causes or divine intervention" in result
    
    @pytest.mark.asyncio
    async def test_get_concept_context_no_concepts(self, concept_repository, mock_llm_service):
        """Test getting concept context when no relevant concepts are found."""
        # Arrange
        journal_text = "Random text with no relevant concepts."
        
        with patch.object(concept_repository, 'find_relevant_concepts') as mock_find_concepts:
            mock_find_concepts.return_value = []
            
            # Act
            result = await concept_repository.get_concept_context(journal_text)
            
            # Assert
            assert result == "No relevant concepts found in the knowledge base."
    
    @pytest.mark.asyncio
    async def test_get_concept_context_error(self, concept_repository, mock_llm_service):
        """Test getting concept context when an error occurs."""
        # Arrange
        journal_text = "Test text"
        
        with patch.object(concept_repository, 'find_relevant_concepts') as mock_find_concepts:
            mock_find_concepts.side_effect = Exception("RAG error")
            
            # Act
            result = await concept_repository.get_concept_context(journal_text)
            
            # Assert
            assert result == "Error retrieving concept context."
    
    @pytest.mark.asyncio
    async def test_find_concept_by_name_or_title_success(self, concept_repository, mock_neo4j_connection):
        """Test finding concept by name or title."""
        # Arrange
        mock_session = mock_neo4j_connection.session_async.return_value.__aenter__.return_value
        mock_record = Mock()
        mock_record.single = AsyncMock(return_value={
            "c": {
                "name": "existentialism",
                "title": "Existentialism",
                "concept": "A philosophical concept about existence",
                "analysis": "Philosophical concept",
                "connections": [],
                "source": None,
                "summary_short": "Philosophical concept",
                "summary": "A philosophical concept about existence"
            }
        })
        mock_session.run = AsyncMock(return_value=mock_record)
        
        # Act
        result = await concept_repository.find_concept_by_name_or_title("existentialism")
        
        # Assert
        assert result is not None
        assert isinstance(result, Concept)
        assert result.name == "existentialism"
        assert result.title == "Existentialism"
    
    @pytest.mark.asyncio
    async def test_find_concept_by_name_or_title_not_found(self, concept_repository, mock_neo4j_connection):
        """Test finding concept by name or title when not found."""
        # Arrange
        mock_session = mock_neo4j_connection.session_async.return_value.__aenter__.return_value
        mock_record = Mock()
        mock_record.single = AsyncMock(return_value=None)
        mock_session.run = AsyncMock(return_value=mock_record)
        
        # Act
        result = await concept_repository.find_concept_by_name_or_title("nonexistent")
        
        # Assert
        assert result is None
    
    @pytest.mark.asyncio
    async def test_get_concept_connections_success(self, concept_repository, mock_neo4j_connection):
        """Test getting concept connections."""
        # Arrange
        concept_uuid = "concept-uuid-123"
        mock_session = mock_neo4j_connection.session_async.return_value.__aenter__.return_value
        
        async def async_iter():
            yield {
                "connected": {
                    "name": "free will",
                    "title": "Free Will",
                    "concept": "The ability to make voluntary choices",
                    "analysis": "Concept of choice",
                    "connections": [],
                    "source": None,
                    "summary_short": "Concept of choice",
                    "summary": "The ability to make voluntary choices"
                }
            }
            yield {
                "connected": {
                    "name": "determinism",
                    "title": "Determinism",
                    "concept": "The belief that all events are determined by prior causes",
                    "analysis": "Opposite of free will",
                    "connections": [],
                    "source": None,
                    "summary_short": "Opposite of free will",
                    "summary": "The belief that all events are determined by prior causes"
                }
            }
        
        mock_result = Mock()
        mock_result.__aiter__ = Mock(return_value=async_iter())
        mock_session.run = AsyncMock(return_value=mock_result)
        
        # Act
        result = await concept_repository.get_concept_connections(concept_uuid)
        
        # Assert
        assert len(result) == 2
        assert all(isinstance(concept, Concept) for concept in result)
        assert result[0].name == "free will"
        assert result[1].name == "determinism"
    
    @pytest.mark.asyncio
    async def test_get_concept_connections_empty(self, concept_repository, mock_neo4j_connection):
        """Test getting concept connections when no connections exist."""
        # Arrange
        concept_uuid = "concept-uuid-123"
        mock_session = mock_neo4j_connection.session.return_value.__enter__.return_value
        mock_session.run.return_value = []
        
        # Act
        result = await concept_repository.get_concept_connections(concept_uuid)
        
        # Assert
        assert result == []


class TestConceptRepositoryEmbeddingGeneration:
    """Test embedding generation functionality."""
    
    @pytest.mark.asyncio
    async def test_create_with_embedding(self, concept_repository, sample_concept, mock_neo4j_connection, mock_llm_service):
        """Test creating a concept with embedding generation."""
        # Arrange
        mock_session = mock_neo4j_connection.session_async.return_value.__aenter__.return_value
        mock_record = Mock()
        mock_record.single = AsyncMock(return_value={"uuid": "new-concept-uuid"})
        mock_session.run = AsyncMock(return_value=mock_record)
        
        # Act
        result_uuid = await concept_repository.create(sample_concept)
        
        # Assert
        assert result_uuid == "new-concept-uuid"
        mock_llm_service.create_embedding.assert_called_once()
        
        # Verify embedding was generated from summary
        call_args = mock_llm_service.create_embedding.call_args
        assert call_args.kwargs["text"] == "A philosophical concept that emphasizes individual existence, freedom, and choice"
    
    @pytest.mark.asyncio
    async def test_update_with_embedding_regeneration(self, concept_repository, mock_neo4j_connection, mock_llm_service):
        """Test updating a concept with embedding regeneration."""
        # Arrange
        concept_uuid = "concept-uuid-123"
        updates = {
            "summary": "Updated summary about existentialism",
            "analysis": "Updated analysis"
        }
        
        mock_session = mock_neo4j_connection.session_async.return_value.__aenter__.return_value
        mock_record = Mock()
        mock_record.single = AsyncMock(return_value={"uuid": concept_uuid})
        mock_session.run = AsyncMock(return_value=mock_record)
        
        # Act
        result_uuid = await concept_repository.update(concept_uuid, updates)
        
        # Assert
        assert result_uuid == concept_uuid
        mock_llm_service.create_embedding.assert_called_once()
        
        # Verify embedding was generated from updated summary
        call_args = mock_llm_service.create_embedding.call_args
        assert call_args.kwargs["text"] == "Updated summary about existentialism"
