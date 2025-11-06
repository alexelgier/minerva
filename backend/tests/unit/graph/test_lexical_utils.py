"""
Unit tests for lexical utilities.

Tests the lexical tree building and chunk insertion functionality.
"""

import pytest
from unittest.mock import Mock, MagicMock, AsyncMock
from datetime import datetime
from minerva_backend.graph.services.lexical_utils import (
    _prepare_chunk_data,
    _separate_relationships_by_type,
    _log_creation_stats,
    _create_chunks,
    _create_relationships,
    _create_contains_relationships,
    _create_has_chunk_relationships,
    _create_sibling_relationships,
    _insert_chunks_and_relationships,
    build_and_insert_lexical_tree,
    SpanIndex
)
from minerva_backend.graph.models.documents import Chunk
from minerva_backend.graph.models.base import PartitionType, LexicalType


class TestLexicalUtils:
    """Test lexical utility functions."""

    @pytest.fixture
    def sample_chunks(self):
        """Create sample chunks for testing."""
        return [
            Chunk(
                uuid="chunk-1",
                text="This is the first chunk.",
                type=LexicalType.CHUNK.value,
                partition=PartitionType.LEXICAL.value,
                created_at=datetime(2024, 1, 15, 10, 0, 0)
            ),
            Chunk(
                uuid="chunk-2", 
                text="This is the second chunk.",
                type=LexicalType.CHUNK.value,
                partition=PartitionType.LEXICAL.value,
                created_at=datetime(2024, 1, 15, 10, 1, 0)
            )
        ]

    @pytest.fixture
    def sample_relationships(self):
        """Create sample relationships for testing."""
        return [
            {"type": "CONTAINS", "parent": "parent-1", "child": "chunk-1"},
            {"type": "CONTAINS", "parent": "parent-1", "child": "chunk-2"},
            {"type": "NEXT_SIBLING", "parent": "chunk-1", "child": "chunk-2"},
            {"type": "HAS_CHUNK", "parent": "journal-1", "child": "chunk-1"},
            {"type": "HAS_CHUNK", "parent": "journal-1", "child": "chunk-2"},
        ]

    def test_prepare_chunk_data(self, sample_chunks):
        """Test preparing chunk data for Cypher insertion."""
        result = _prepare_chunk_data(sample_chunks)
        
        assert len(result) == 2
        assert result[0]["uuid"] == "chunk-1"
        assert result[0]["text"] == "This is the first chunk."
        assert result[0]["type"] == LexicalType.CHUNK.value
        assert result[0]["partition"] == PartitionType.LEXICAL.value
        assert result[0]["created_at"] == "2024-01-15T10:00:00"
        
        assert result[1]["uuid"] == "chunk-2"
        assert result[1]["text"] == "This is the second chunk."
        assert result[1]["created_at"] == "2024-01-15T10:01:00"

    def test_separate_relationships_by_type(self, sample_relationships):
        """Test separating relationships by type."""
        result = _separate_relationships_by_type(sample_relationships)
        
        assert len(result["contains"]) == 2
        assert len(result["sibling"]) == 1
        assert len(result["has_chunk"]) == 2
        
        assert result["contains"][0]["type"] == "CONTAINS"
        assert result["sibling"][0]["type"] == "NEXT_SIBLING"
        assert result["has_chunk"][0]["type"] == "HAS_CHUNK"

    def test_separate_relationships_empty(self):
        """Test separating empty relationships list."""
        result = _separate_relationships_by_type([])
        
        assert len(result["contains"]) == 0
        assert len(result["sibling"]) == 0
        assert len(result["has_chunk"]) == 0

    def test_log_creation_stats(self, sample_chunks, sample_relationships, capsys):
        """Test logging creation statistics."""
        relationship_groups = _separate_relationships_by_type(sample_relationships)
        _log_creation_stats(sample_chunks, relationship_groups)
        
        captured = capsys.readouterr()
        assert "Creating 2 chunks" in captured.out
        assert "Creating 2 CONTAINS relationships" in captured.out
        assert "Creating 1 NEXT_SIBLING relationships" in captured.out
        assert "Creating 2 HAS_CHUNK relationships" in captured.out

    @pytest.mark.asyncio
    async def test_create_chunks(self, sample_chunks):
        """Test creating chunks in the database."""
        mock_session = AsyncMock()
        mock_result = Mock()
        mock_consume = Mock()
        mock_consume.return_value.counters.nodes_created = 2
        mock_result.consume = mock_consume
        mock_session.run.return_value = mock_result
        
        chunk_data = _prepare_chunk_data(sample_chunks)
        await _create_chunks(mock_session, chunk_data)
        
        # Verify session.run was called with correct query
        mock_session.run.assert_called_once()
        call_args = mock_session.run.call_args
        assert "UNWIND $chunks AS c" in call_args[0][0]
        assert "CREATE (:Chunk" in call_args[0][0]
        assert call_args[1]["chunks"] == chunk_data
        
        # Verify consume was called
        mock_consume.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_contains_relationships(self, sample_relationships):
        """Test creating CONTAINS relationships."""
        mock_session = AsyncMock()
        mock_result = Mock()
        mock_consume = Mock()
        mock_consume.return_value.counters.relationships_created = 2
        mock_result.consume = mock_consume
        mock_session.run.return_value = mock_result
        
        contains_rels = [r for r in sample_relationships if r["type"] == "CONTAINS"]
        await _create_contains_relationships(mock_session, contains_rels)
        
        # Verify session.run was called with correct query
        mock_session.run.assert_called_once()
        call_args = mock_session.run.call_args
        assert "UNWIND $contains_rels AS rel" in call_args[0][0]
        assert "CREATE (parent)-[:CONTAINS]->(child)" in call_args[0][0]
        assert call_args[1]["contains_rels"] == contains_rels

    @pytest.mark.asyncio
    async def test_create_contains_relationships_empty(self):
        """Test creating CONTAINS relationships with empty list."""
        mock_session = AsyncMock()
        await _create_contains_relationships(mock_session, [])
        
        # Should not call session.run for empty list
        mock_session.run.assert_not_called()

    @pytest.mark.asyncio
    async def test_create_has_chunk_relationships(self, sample_relationships):
        """Test creating HAS_CHUNK relationships."""
        mock_session = AsyncMock()
        mock_result = Mock()
        mock_consume = Mock()
        mock_consume.return_value.counters.relationships_created = 2
        mock_result.consume = mock_consume
        mock_session.run.return_value = mock_result
        
        has_chunk_rels = [r for r in sample_relationships if r["type"] == "HAS_CHUNK"]
        await _create_has_chunk_relationships(mock_session, has_chunk_rels)
        
        # Verify session.run was called with correct query
        mock_session.run.assert_called_once()
        call_args = mock_session.run.call_args
        assert "UNWIND $has_chunk_rels AS rel" in call_args[0][0]
        assert "CREATE (parent)-[:HAS_CHUNK]->(child)" in call_args[0][0]
        assert call_args[1]["has_chunk_rels"] == has_chunk_rels

    @pytest.mark.asyncio
    async def test_create_sibling_relationships(self, sample_relationships):
        """Test creating NEXT_SIBLING relationships."""
        mock_session = AsyncMock()
        mock_result = Mock()
        mock_consume = Mock()
        mock_consume.return_value.counters.relationships_created = 1
        mock_result.consume = mock_consume
        mock_session.run.return_value = mock_result
        
        sibling_rels = [r for r in sample_relationships if r["type"] == "NEXT_SIBLING"]
        await _create_sibling_relationships(mock_session, sibling_rels)
        
        # Verify session.run was called with correct query
        mock_session.run.assert_called_once()
        call_args = mock_session.run.call_args
        assert "UNWIND $sibling_rels AS rel" in call_args[0][0]
        assert "CREATE (a)-[:NEXT_SIBLING]->(b)" in call_args[0][0]
        assert call_args[1]["sibling_rels"] == sibling_rels

    @pytest.mark.asyncio
    async def test_create_relationships(self, sample_relationships):
        """Test creating all relationship types."""
        mock_session = AsyncMock()
        mock_result = Mock()
        mock_consume = Mock()
        mock_consume.return_value.counters.relationships_created = 1
        mock_result.consume = mock_consume
        mock_session.run.return_value = mock_result

        relationship_groups = _separate_relationships_by_type(sample_relationships)
        await _create_relationships(mock_session, relationship_groups)

        # Should call session.run for each relationship type
        assert mock_session.run.call_count == 3

    @pytest.mark.asyncio
    async def test_insert_chunks_and_relationships(self, sample_chunks, sample_relationships):
        """Test the main function that orchestrates chunk and relationship creation."""
        mock_connection = Mock()
        mock_session = AsyncMock()

        # Create a proper async context manager mock
        mock_context_manager = AsyncMock()
        mock_context_manager.__aenter__ = AsyncMock(return_value=mock_session)
        mock_context_manager.__aexit__ = AsyncMock(return_value=None)
        mock_connection.session_async = Mock(return_value=mock_context_manager)

        mock_result = Mock()
        mock_consume = Mock()
        mock_consume.return_value.counters.nodes_created = 2
        mock_consume.return_value.counters.relationships_created = 5
        mock_result.consume = mock_consume
        mock_session.run.return_value = mock_result

        await _insert_chunks_and_relationships(mock_connection, sample_chunks, sample_relationships)

        # Verify connection.session_async was called
        mock_connection.session_async.assert_called_once()
        
        # Verify session.run was called multiple times (chunks + relationships)
        assert mock_session.run.call_count >= 4  # 1 for chunks + 3 for relationship types


class TestSpanIndex:
    """Test SpanIndex functionality."""

    def test_span_index_creation(self):
        """Test creating a SpanIndex."""
        span_index = SpanIndex()
        assert len(span_index) == 0

    def test_span_index_add_span(self):
        """Test adding spans to SpanIndex."""
        span_index = SpanIndex()
        span_index.add_span(0, 10, "chunk-1")
        assert len(span_index) == 1

    def test_span_index_query_containing(self):
        """Test querying spans that contain a position."""
        span_index = SpanIndex()
        span_index.add_span(0, 10, "chunk-1")
        span_index.add_span(5, 15, "chunk-2")
        
        results = span_index.query_containing(7, 8)
        assert len(results) == 2  # Both spans contain position 7-8
        
        results = span_index.query_containing(12, 13)
        assert len(results) == 1  # Only second span contains position 12-13
