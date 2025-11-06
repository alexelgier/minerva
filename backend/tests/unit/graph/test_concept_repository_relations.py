"""
Unit tests for concept relation methods in ConceptRepository.

These tests focus on the concept relation CRUD operations without requiring
actual database connections.
"""

import pytest
from unittest.mock import Mock, MagicMock, patch, AsyncMock
from typing import List, Dict, Any

from minerva_backend.graph.repositories.concept_repository import ConceptRepository


class TestConceptRepositoryRelations:
    """Test cases for concept relation methods in ConceptRepository."""
    
    def setup_method(self):
        """Set up test fixtures."""
        from unittest.mock import AsyncMock
        
        self.mock_connection = Mock()
        self.mock_session = AsyncMock()
        self.mock_llm_service = Mock()
        # Properly mock the async context manager
        mock_context_manager = AsyncMock()
        mock_context_manager.__aenter__ = AsyncMock(return_value=self.mock_session)
        mock_context_manager.__aexit__ = AsyncMock(return_value=None)
        self.mock_connection.session_async = Mock(return_value=mock_context_manager)
        self.repository = ConceptRepository(self.mock_connection, self.mock_llm_service)
    
    @pytest.mark.asyncio
    async def test_create_concept_relation_success(self):
        """Test successful creation of concept relation."""
        # Mock successful database operation
        mock_record = Mock()
        mock_record.single = AsyncMock(return_value={"r": "relation_object"})
        self.mock_session.run = AsyncMock(return_value=mock_record)
        
        result = await self.repository.create_concept_relation("uuid1", "uuid2", "GENERALIZES")
        
        assert result is True
        self.mock_session.run.assert_called_once()
        
        # Verify the query was called with correct parameters
        call_args = self.mock_session.run.call_args
        assert "source_uuid" in call_args[1]
        assert "target_uuid" in call_args[1]
        assert call_args[1]["source_uuid"] == "uuid1"
        assert call_args[1]["target_uuid"] == "uuid2"
    
    @pytest.mark.asyncio
    async def test_create_concept_relation_failure(self):
        """Test handling of concept relation creation failure."""
        # Mock failed database operation
        mock_record = Mock()
        mock_record.single = AsyncMock(return_value=None)
        self.mock_session.run = AsyncMock(return_value=mock_record)
        
        result = await self.repository.create_concept_relation("uuid1", "uuid2", "GENERALIZES")
        
        assert result is False
    
    @pytest.mark.asyncio
    async def test_create_concept_relation_exception(self):
        """Test handling of exceptions during concept relation creation."""
        # Mock exception during database operation
        self.mock_session.run = AsyncMock(side_effect=Exception("Database error"))
        
        result = await self.repository.create_concept_relation("uuid1", "uuid2", "GENERALIZES")
        
        assert result is False
    
    @pytest.mark.asyncio
    async def test_get_concept_relations_success(self):
        """Test successful retrieval of concept relations."""
        # Mock successful database operation
        mock_record1 = Mock()
        mock_record1.__getitem__ = Mock(side_effect=lambda key: {"target_uuid": "uuid2", "relation_type": "GENERALIZES"}[key])
        
        mock_record2 = Mock()
        mock_record2.__getitem__ = Mock(side_effect=lambda key: {"target_uuid": "uuid3", "relation_type": "PART_OF"}[key])
        
        async def async_iter():
            yield mock_record1
            yield mock_record2
        
        mock_result = Mock()
        mock_result.__aiter__ = Mock(return_value=async_iter())
        self.mock_session.run = AsyncMock(return_value=mock_result)
        
        result = await self.repository.get_concept_relations("uuid1")
        
        assert len(result) == 2
        assert result[0]["target_uuid"] == "uuid2"
        assert result[0]["relation_type"] == "GENERALIZES"
        assert result[1]["target_uuid"] == "uuid3"
        assert result[1]["relation_type"] == "PART_OF"
    
    @pytest.mark.asyncio
    async def test_get_concept_relations_empty(self):
        """Test retrieval of concept relations when none exist."""
        # Mock empty result
        mock_result = Mock()
        mock_result.__iter__ = Mock(return_value=iter([]))
        self.mock_session.run = AsyncMock(return_value=mock_result)
        
        result = await self.repository.get_concept_relations("uuid1")
        
        assert result == []
    
    @pytest.mark.asyncio
    async def test_get_concept_relations_exception(self):
        """Test handling of exceptions during concept relations retrieval."""
        # Mock exception during database operation
        self.mock_session.run = AsyncMock(side_effect=Exception("Database error"))
        
        result = await self.repository.get_concept_relations("uuid1")
        
        assert result == []
    
    @pytest.mark.asyncio
    async def test_delete_concept_relation_success(self):
        """Test successful deletion of concept relation."""
        # Mock successful database operation
        mock_record = Mock()
        mock_record.single = AsyncMock(return_value={"deleted": 1})
        self.mock_session.run = AsyncMock(return_value=mock_record)
        
        result = await self.repository.delete_concept_relation("uuid1", "uuid2", "GENERALIZES")
        
        assert result is True
        self.mock_session.run.assert_called_once()
        
        # Verify the query was called with correct parameters
        call_args = self.mock_session.run.call_args
        assert "source_uuid" in call_args[1]
        assert "target_uuid" in call_args[1]
        assert call_args[1]["source_uuid"] == "uuid1"
        assert call_args[1]["target_uuid"] == "uuid2"
    
    @pytest.mark.asyncio
    async def test_delete_concept_relation_not_found(self):
        """Test deletion of concept relation that doesn't exist."""
        # Mock database operation returning no deleted records
        mock_record = Mock()
        mock_record.single = AsyncMock(return_value={"deleted": 0})
        self.mock_session.run = AsyncMock(return_value=mock_record)
        
        result = await self.repository.delete_concept_relation("uuid1", "uuid2", "GENERALIZES")
        
        assert result is False
    
    @pytest.mark.asyncio
    async def test_delete_concept_relation_exception(self):
        """Test handling of exceptions during concept relation deletion."""
        # Mock exception during database operation
        self.mock_session.run = AsyncMock(side_effect=Exception("Database error"))
        
        result = await self.repository.delete_concept_relation("uuid1", "uuid2", "GENERALIZES")
        
        assert result is False
    
    @pytest.mark.asyncio
    async def test_create_concept_relation_query_structure(self):
        """Test that the create query has the correct structure."""
        mock_record = Mock()
        mock_record.single = AsyncMock(return_value={"r": "relation_object"})
        self.mock_session.run = AsyncMock(return_value=mock_record)
        
        await self.repository.create_concept_relation("uuid1", "uuid2", "GENERALIZES")
        
        # Get the query that was executed
        call_args = self.mock_session.run.call_args
        query = call_args[0][0]
        
        # Verify query structure
        assert "MATCH (source:Concept {uuid: $source_uuid})" in query
        assert "MATCH (target:Concept {uuid: $target_uuid})" in query
        assert "MERGE (source)-[r:GENERALIZES]->(target)" in query
        assert "RETURN r" in query
    
    @pytest.mark.asyncio
    async def test_get_concept_relations_query_structure(self):
        """Test that the get relations query has the correct structure."""
        mock_result = Mock()
        mock_result.__iter__ = Mock(return_value=iter([]))
        self.mock_session.run = AsyncMock(return_value=mock_result)
        
        await self.repository.get_concept_relations("uuid1")
        
        # Get the query that was executed
        call_args = self.mock_session.run.call_args
        query = call_args[0][0]
        
        # Verify query structure
        assert "MATCH (c:Concept {uuid: $concept_uuid})-[r]->(target:Concept)" in query
        assert "RETURN target.uuid as target_uuid, type(r) as relation_type" in query
    
    @pytest.mark.asyncio
    async def test_delete_concept_relation_query_structure(self):
        """Test that the delete query has the correct structure."""
        mock_record = Mock()
        mock_record.single = AsyncMock(return_value={"deleted": 1})
        self.mock_session.run = AsyncMock(return_value=mock_record)
        
        await self.repository.delete_concept_relation("uuid1", "uuid2", "GENERALIZES")
        
        # Get the query that was executed
        call_args = self.mock_session.run.call_args
        query = call_args[0][0]
        
        # Verify query structure
        assert "MATCH (source:Concept {uuid: $source_uuid})-[r:GENERALIZES]->(target:Concept {uuid: $target_uuid})" in query
        assert "DELETE r" in query
        assert "RETURN count(r) as deleted" in query


class TestConceptRepositoryRelationTypes:
    """Test cases for different relation types in ConceptRepository."""
    
    def setup_method(self):
        """Set up test fixtures."""
        from unittest.mock import AsyncMock
        
        self.mock_connection = Mock()
        self.mock_session = AsyncMock()
        self.mock_llm_service = Mock()
        # Properly mock the async context manager
        mock_context_manager = AsyncMock()
        mock_context_manager.__aenter__ = AsyncMock(return_value=self.mock_session)
        mock_context_manager.__aexit__ = AsyncMock(return_value=None)
        self.mock_connection.session_async = Mock(return_value=mock_context_manager)
        self.repository = ConceptRepository(self.mock_connection, self.mock_llm_service)
    
    @pytest.mark.parametrize("relation_type", [
        "GENERALIZES",
        "SPECIFIC_OF", 
        "PART_OF",
        "HAS_PART",
        "SUPPORTS",
        "SUPPORTED_BY",
        "OPPOSES",
        "SIMILAR_TO",
        "RELATES_TO"
    ])
    @pytest.mark.asyncio
    async def test_create_different_relation_types(self, relation_type):
        """Test creation of different relation types."""
        mock_record = Mock()
        mock_record.single = AsyncMock(return_value={"r": "relation_object"})
        self.mock_session.run = AsyncMock(return_value=mock_record)
        
        result = await self.repository.create_concept_relation("uuid1", "uuid2", relation_type)
        
        assert result is True
        
        # Verify the query contains the correct relation type
        call_args = self.mock_session.run.call_args
        query = call_args[0][0]
        assert f"MERGE (source)-[r:{relation_type}]->(target)" in query
    
    @pytest.mark.parametrize("relation_type", [
        "GENERALIZES",
        "SPECIFIC_OF", 
        "PART_OF",
        "HAS_PART",
        "SUPPORTS",
        "SUPPORTED_BY",
        "OPPOSES",
        "SIMILAR_TO",
        "RELATES_TO"
    ])
    @pytest.mark.asyncio
    async def test_delete_different_relation_types(self, relation_type):
        """Test deletion of different relation types."""
        mock_record = Mock()
        mock_record.single = AsyncMock(return_value={"deleted": 1})
        self.mock_session.run = AsyncMock(return_value=mock_record)
        
        result = await self.repository.delete_concept_relation("uuid1", "uuid2", relation_type)
        
        assert result is True
        
        # Verify the query contains the correct relation type
        call_args = self.mock_session.run.call_args
        query = call_args[0][0]
        assert f"MATCH (source:Concept {{uuid: $source_uuid}})-[r:{relation_type}]->(target:Concept {{uuid: $target_uuid}})" in query


if __name__ == "__main__":
    pytest.main([__file__])
