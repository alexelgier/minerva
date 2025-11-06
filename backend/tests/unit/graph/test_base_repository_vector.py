"""
Unit tests for BaseRepository vector search functionality.

Tests the vector search methods with mocked dependencies.
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime

from minerva_backend.graph.models.entities import Concept
from minerva_backend.graph.repositories.base import BaseRepository
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
    
    # Mock async vector search
    mock.vector_search = AsyncMock()
    
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
        analysis="A philosophical concept about individual existence and freedom",
        concept="Test concept content",
        source=None,
        summary_short="Philosophical concept about existence",
        summary="A philosophical concept that emphasizes individual existence, freedom, and choice"
    )


class TestVectorSearchMethods:
    """Test vector search functionality."""
    
    @pytest.mark.asyncio
    async def test_vector_search_success(self, concept_repository, mock_neo4j_connection, mock_llm_service):
        """Test successful vector search."""
        # Arrange
        query_text = "philosophy and existence"
        mock_embedding = [0.1, 0.2, 0.3] * 512
        
        # Mock Neo4j vector search results
        mock_records = [
            {
                "node": {
                    "uuid": "concept-uuid-1",
                    "name": "existentialism",
                    "title": "Existentialism",
                    "concept": "A philosophical concept about existence",
                    "analysis": "Philosophical concept",
                    "connections": [],
                    "source": None,
                    "summary_short": "Philosophical concept",
                    "summary": "A philosophical concept about existence",
                    "embedding": mock_embedding
                }
            },
            {
                "node": {
                    "uuid": "concept-uuid-2",
                    "name": "free will",
                    "title": "Free Will",
                    "concept": "The ability to make voluntary choices",
                    "analysis": "Concept of choice",
                    "connections": [],
                    "source": None,
                    "summary_short": "Concept of choice",
                    "summary": "The ability to make voluntary choices",
                    "embedding": mock_embedding
                }
            }
        ]
        
        mock_neo4j_connection.vector_search = AsyncMock(return_value=mock_records)
        
        # Act
        result = await concept_repository.vector_search(query_text, limit=5, threshold=0.7)
        
        # Assert
        assert len(result) == 2
        assert all(isinstance(concept, Concept) for concept in result)
        assert result[0].name == "existentialism"
        assert result[1].name == "free will"
        
        # Verify LLM service was called to generate embedding
        mock_llm_service.create_embedding.assert_called_once_with(text=query_text)
        
        # Verify Neo4j vector search was called
        mock_neo4j_connection.vector_search.assert_called_once()
        call_args = mock_neo4j_connection.vector_search.call_args
        assert call_args.kwargs["label"] == "Concept"
        assert call_args.kwargs["limit"] == 5
        assert call_args.kwargs["threshold"] == 0.7
        assert isinstance(call_args.kwargs["query_embedding"], list)
        assert len(call_args.kwargs["query_embedding"]) > 0
    
    @pytest.mark.asyncio
    async def test_vector_search_empty_results(self, concept_repository, mock_neo4j_connection, mock_llm_service):
        """Test vector search with empty results."""
        # Arrange
        query_text = "nonexistent concept"
        mock_embedding = [0.1, 0.2, 0.3] * 512
        
        mock_neo4j_connection.vector_search.return_value = []
        
        # Act
        result = await concept_repository.vector_search(query_text)
        
        # Assert
        assert result == []
        mock_llm_service.create_embedding.assert_called_once()
        mock_neo4j_connection.vector_search.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_vector_search_embedding_error(self, concept_repository, mock_llm_service):
        """Test vector search when embedding generation fails."""
        # Arrange
        query_text = "test query"
        mock_llm_service.create_embedding.side_effect = Exception("Embedding error")
        
        # Act
        result = await concept_repository.vector_search(query_text)
        
        # Assert
        assert result == []
        mock_llm_service.create_embedding.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_vector_search_neo4j_error(self, concept_repository, mock_neo4j_connection, mock_llm_service):
        """Test vector search when Neo4j search fails."""
        # Arrange
        query_text = "test query"
        mock_embedding = [0.1, 0.2, 0.3] * 512
        
        mock_neo4j_connection.vector_search.side_effect = Exception("Neo4j error")
        
        # Act
        result = await concept_repository.vector_search(query_text)
        
        # Assert
        assert result == []
        mock_llm_service.create_embedding.assert_called_once()
        mock_neo4j_connection.vector_search.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_find_similar_success(self, concept_repository, mock_neo4j_connection, mock_llm_service):
        """Test find_similar method."""
        # Arrange
        target_concept = Concept(
            name="existentialism",
            title="Existentialism",
            analysis="Philosophical concept",
            concept="Test concept content",
            source=None,
            summary_short="Philosophical concept",
            summary="A philosophical concept about existence",
            embedding=[0.1, 0.2, 0.3] * 512
        )
        
        mock_records = [
            {
                "node": {
                    "uuid": "concept-uuid-1",
                    "name": "free will",
                    "title": "Free Will",
                    "concept": "The ability to make voluntary choices",
                    "analysis": "Concept of choice",
                    "connections": [],
                    "source": None,
                    "summary_short": "Concept of choice",
                    "summary": "The ability to make voluntary choices",
                    "embedding": [0.1, 0.2, 0.3] * 512
                }
            }
        ]
        
        mock_neo4j_connection.vector_search = AsyncMock(return_value=mock_records)
        
        # Act
        result = await concept_repository.find_similar(target_concept, limit=3)
        
        # Assert
        assert len(result) == 1
        assert result[0].name == "free will"
        
        # Verify Neo4j vector search was called with target concept's embedding 
        mock_neo4j_connection.vector_search.assert_called_once_with(
            label="Concept",
            query_embedding=target_concept.embedding,
            limit=4,  # limit + 1 to exclude the node itself
            threshold=0.7
        )
    
    @pytest.mark.asyncio
    async def test_find_similar_no_embedding(self, concept_repository, mock_llm_service):
        """Test find_similar when target concept has no embedding."""
        # Arrange
        target_concept = Concept(
            name="existentialism",
            title="Existentialism",
            analysis="Philosophical concept",
            concept="Test concept content",
            source=None,
            summary_short="Philosophical concept",
            summary="A philosophical concept about existence",
            embedding=None  # No embedding
        )
        
        # Act
        result = await concept_repository.find_similar(target_concept)
        
        # Assert
        assert result == []
        # Should not call Neo4j vector search when no embedding


class TestEmbeddingGenerationMethods:
    """Test embedding generation functionality."""
    
    @pytest.mark.asyncio
    async def test_generate_embedding_success(self, concept_repository, mock_llm_service):
        """Test successful embedding generation."""
        # Arrange
        text = "A philosophical concept about existence"
        mock_embedding = [0.1, 0.2, 0.3] * 512
        mock_llm_service.create_embedding.return_value = mock_embedding
        
        # Act
        result = await concept_repository._generate_embedding(text)
        
        # Assert
        assert result == mock_embedding
        mock_llm_service.create_embedding.assert_called_once_with(text=text)
    
    @pytest.mark.asyncio
    async def test_generate_embedding_error(self, concept_repository, mock_llm_service):
        """Test embedding generation when LLM service fails."""
        # Arrange
        text = "Test text"
        mock_llm_service.create_embedding.side_effect = Exception("LLM error")
        
        # Act
        result = await concept_repository._generate_embedding(text)
        
        # Assert
        assert result == []
        mock_llm_service.create_embedding.assert_called_once_with(text=text)
    
    @pytest.mark.asyncio
    async def test_ensure_embedding_with_existing(self, concept_repository, sample_concept, mock_llm_service):
        """Test ensure_embedding when concept already has embedding."""
        # Arrange
        sample_concept.embedding = [0.1, 0.2, 0.3] * 512
        
        # Act
        result = await concept_repository._ensure_embedding(sample_concept)
        
        # Assert
        assert result == sample_concept
        assert result.embedding == [0.1, 0.2, 0.3] * 512
        # Should not call LLM service when embedding already exists
        mock_llm_service.create_embedding.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_ensure_embedding_without_existing(self, concept_repository, sample_concept, mock_llm_service):
        """Test ensure_embedding when concept has no embedding."""
        # Arrange
        sample_concept.embedding = None
        mock_embedding = [0.1, 0.2, 0.3] * 512
        mock_llm_service.create_embedding.return_value = mock_embedding
        
        # Act
        result = await concept_repository._ensure_embedding(sample_concept)
        
        # Assert
        assert result == sample_concept
        assert result.embedding == mock_embedding
        mock_llm_service.create_embedding.assert_called_once_with(text=sample_concept.summary)
    
    @pytest.mark.asyncio
    async def test_ensure_embedding_generation_error(self, concept_repository, sample_concept, mock_llm_service):
        """Test ensure_embedding when embedding generation fails."""
        # Arrange
        sample_concept.embedding = None
        mock_llm_service.create_embedding.side_effect = Exception("LLM error")
        
        # Act
        result = await concept_repository._ensure_embedding(sample_concept)
        
        # Assert
        assert result == sample_concept
        assert result.embedding == []
        mock_llm_service.create_embedding.assert_called_once_with(text=sample_concept.summary)


class TestCreateAndUpdateWithEmbeddings:
    """Test create and update methods with embedding generation."""
    
    @pytest.mark.asyncio
    async def test_create_with_embedding_generation(self, concept_repository, sample_concept, mock_neo4j_connection, mock_llm_service):
        """Test creating a concept with embedding generation."""
        # Arrange
        sample_concept.embedding = None  # No existing embedding
        mock_embedding = [0.1, 0.2, 0.3] * 512
        mock_llm_service.create_embedding.return_value = mock_embedding
        
        mock_session = mock_neo4j_connection.session_async.return_value.__aenter__.return_value
        mock_record = Mock()
        mock_record.single = AsyncMock(return_value={"uuid": "new-concept-uuid"})
        mock_session.run = AsyncMock(return_value=mock_record)
        
        # Act
        result_uuid = await concept_repository.create(sample_concept)
        
        # Assert
        assert result_uuid == "new-concept-uuid"
        mock_llm_service.create_embedding.assert_called_once_with(text=sample_concept.summary)
        
        # Verify the concept was modified with embedding
        assert sample_concept.embedding == mock_embedding
    
    @pytest.mark.asyncio
    async def test_update_with_embedding_regeneration(self, concept_repository, mock_neo4j_connection, mock_llm_service):
        """Test updating a concept with embedding regeneration."""
        # Arrange
        concept_uuid = "concept-uuid-123"
        updates = {
            "summary": "Updated summary about existentialism",
            "analysis": "Updated analysis"
        }
        mock_embedding = [0.1, 0.2, 0.3] * 512
        mock_llm_service.create_embedding.return_value = mock_embedding
        
        mock_session = mock_neo4j_connection.session_async.return_value.__aenter__.return_value
        mock_record = Mock()
        mock_record.single = AsyncMock(return_value={"uuid": concept_uuid})
        mock_session.run = AsyncMock(return_value=mock_record)
        
        # Act
        result_uuid = await concept_repository.update(concept_uuid, updates)
        
        # Assert
        assert result_uuid == concept_uuid
        mock_llm_service.create_embedding.assert_called_once_with(text=updates["summary"])
        
        # Verify embedding was added to updates
        assert "embedding" in updates
        assert updates["embedding"] == mock_embedding
    
    @pytest.mark.asyncio
    async def test_update_without_summary_change(self, concept_repository, mock_neo4j_connection, mock_llm_service):
        """Test updating a concept without summary change (no embedding regeneration)."""
        # Arrange
        concept_uuid = "concept-uuid-123"
        updates = {
            "analysis": "Updated analysis only",
            "connections": ["New Connection"]
        }
        
        mock_session = mock_neo4j_connection.session_async.return_value.__aenter__.return_value
        mock_record = Mock()
        mock_record.single = AsyncMock(return_value={"uuid": concept_uuid})
        mock_session.run = AsyncMock(return_value=mock_record)
        
        # Act
        result_uuid = await concept_repository.update(concept_uuid, updates)
        
        # Assert
        assert result_uuid == concept_uuid
        # Should not call LLM service when summary is not updated
        mock_llm_service.create_embedding.assert_not_called()
        assert "embedding" not in updates
