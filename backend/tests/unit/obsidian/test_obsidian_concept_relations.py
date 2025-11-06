"""
Unit tests for concept relations functionality in ObsidianService.

These tests focus on the parsing, validation, and processing of concept relations
without requiring actual database connections or file system operations.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from dataclasses import dataclass


@pytest.fixture
def obsidian_service(test_container):
    """Create real ObsidianService with mocked dependencies."""
    from minerva_backend.obsidian.obsidian_service import ObsidianService
    
    return ObsidianService(
        vault_path="/tmp/minerva_test_vault",  # Test-specific vault path
        llm_service=test_container.llm_service(),  # Mocked dependency
        concept_repository=test_container.concept_repository()  # Mocked dependency
    )
from typing import Dict, List, Any

from minerva_backend.obsidian.obsidian_service import (
    ObsidianService,
    SyncResult,
    RELATION_MAP,
    CONCEPT_RELATIONS_KEY
)


class TestSyncResult:
    """Test cases for SyncResult dataclass."""
    
    def test_sync_result_creation(self):
        """Test SyncResult can be created with all required fields."""
        result = SyncResult(
            total_files=10,
            parsed=8,
            created=5,
            updated=3,
            unchanged=2,
            errors=2,
            errors_list=["Error 1", "Error 2"],
            missing_concepts=["Missing1", "Missing2"],
            broken_notes=["broken1.md"],
            relations_created=15,
            relations_updated=5,
            relations_deleted=3,
            self_connections_removed=2,
            inconsistent_relations=["Concept A: Self-connection found"]
        )
        
        assert result.total_files == 10
        assert result.parsed == 8
        assert result.created == 5
        assert result.updated == 3
        assert result.errors == 2
        assert len(result.errors_list) == 2
        assert len(result.missing_concepts) == 2
        assert len(result.broken_notes) == 1
        assert result.relations_created == 15
        assert result.relations_updated == 5
        assert result.relations_deleted == 3
        assert result.self_connections_removed == 2
        assert len(result.inconsistent_relations) == 1


class TestRelationMapping:
    """Test cases for relation mapping constants."""
    
    def test_relation_map_structure(self):
        """Test that RELATION_MAP has correct structure."""
        assert isinstance(RELATION_MAP, dict)
        assert len(RELATION_MAP) == 9
        
        # Test that all values are tuples of length 2
        for relation_type, (forward, reverse) in RELATION_MAP.items():
            assert isinstance(relation_type, str)
            assert isinstance(forward, str)
            assert isinstance(reverse, str)
            assert len(forward) > 0
            assert len(reverse) > 0
    
    def test_relation_map_symmetric_relations(self):
        """Test that symmetric relations have matching forward and reverse types."""
        symmetric_relations = ["OPPOSES", "SIMILAR_TO", "RELATES_TO"]
        
        for relation_type in symmetric_relations:
            forward, reverse = RELATION_MAP[relation_type]
            assert forward == reverse, f"{relation_type} should be symmetric"
    
    def test_relation_map_asymmetric_relations(self):
        """Test that asymmetric relations have different forward and reverse types."""
        asymmetric_relations = ["GENERALIZES", "SPECIFIC_OF", "PART_OF", "HAS_PART", "SUPPORTS", "SUPPORTED_BY"]
        
        for relation_type in asymmetric_relations:
            forward, reverse = RELATION_MAP[relation_type]
            assert forward != reverse, f"{relation_type} should be asymmetric"


class TestConexionesParsing:
    """Test cases for parsing Conexiones sections."""
    
    def test_parse_empty_content(self, obsidian_service):
        """Test parsing empty content returns empty dict."""
        result = obsidian_service.parse_conexiones_section("")
        assert result == {}
    
    def test_parse_none_content(self, obsidian_service):
        """Test parsing None content returns empty dict."""
        result = obsidian_service.parse_conexiones_section(None)
        assert result == {}
    
    def test_parse_single_relation(self, obsidian_service):
        """Test parsing a single relation."""
        content = "- GENERALIZES: [[Deep Learning]]"
        result = obsidian_service.parse_conexiones_section(content)
        
        expected = {"GENERALIZES": ["Deep Learning"]}
        assert result == expected
    
    def test_parse_multiple_concepts_same_relation(self, obsidian_service):
        """Test parsing multiple concepts for the same relation type."""
        content = "- GENERALIZES: [[Deep Learning]], [[Neural Networks]]"
        result = obsidian_service.parse_conexiones_section(content)
        
        expected = {"GENERALIZES": ["Deep Learning", "Neural Networks"]}
        assert result == expected
    
    def test_parse_multiple_relation_types(self, obsidian_service):
        """Test parsing multiple different relation types."""
        content = """
        - GENERALIZES: [[Deep Learning]]
        - PART_OF: [[Artificial Intelligence]]
        - OPPOSES: [[Traditional Programming]]
        """
        result = obsidian_service.parse_conexiones_section(content)
        
        expected = {
            "GENERALIZES": ["Deep Learning"],
            "PART_OF": ["Artificial Intelligence"],
            "OPPOSES": ["Traditional Programming"]
        }
        assert result == expected
    
    def test_parse_invalid_relation_type(self, obsidian_service):
        """Test that invalid relation types are ignored."""
        content = "- INVALID_TYPE: [[Some Concept]]"
        result = obsidian_service.parse_conexiones_section(content)
        
        assert result == {}
    
    def test_parse_malformed_lines(self, obsidian_service):
        """Test that malformed lines are ignored."""
        content = """
        - GENERALIZES: [[Deep Learning]]
        - No colon here
        - PART_OF: [[AI]]
        - Another malformed line
        """
        result = obsidian_service.parse_conexiones_section(content)
        
        expected = {
            "GENERALIZES": ["Deep Learning"],
            "PART_OF": ["AI"]
        }
        assert result == expected
    
    def test_parse_empty_links(self, obsidian_service):
        """Test that lines with no valid links are ignored."""
        content = "- GENERALIZES: No links here"
        result = obsidian_service.parse_conexiones_section(content)
        
        assert result == {"GENERALIZES": []}
    
    def test_parse_whitespace_handling(self, obsidian_service):
        """Test that whitespace is handled correctly."""
        content = "  -  GENERALIZES  :  [[Deep Learning]]  ,  [[Neural Networks]]  "
        result = obsidian_service.parse_conexiones_section(content)
        
        expected = {"GENERALIZES": ["Deep Learning", "Neural Networks"]}
        assert result == expected


class TestRelationValidation:
    """Test cases for relation validation."""
    
    def setup_method(self):
        """Set up test fixtures."""
        # Service will be obtained from test_container in individual test methods
        pass
    
    def test_validate_no_self_connections(self, obsidian_service):
        """Test validation with no self-connections."""
        relations = {
            "GENERALIZES": ["Deep Learning", "Neural Networks"],
            "PART_OF": ["Artificial Intelligence"]
        }
        result = obsidian_service.validate_relation_consistency("Machine Learning", relations)
        
        assert result == []
    
    def test_validate_self_connections_detected(self, obsidian_service):
        """Test that self-connections are detected."""
        relations = {
            "GENERALIZES": ["Deep Learning", "Machine Learning"],  # Self-connection
            "PART_OF": ["Artificial Intelligence"]
        }
        result = obsidian_service.validate_relation_consistency("Machine Learning", relations)
        
        assert len(result) == 1
        assert "Self-connection found" in result[0]
        assert "Machine Learning" in result[0]
    
    def test_validate_multiple_self_connections(self, obsidian_service):
        """Test detection of multiple self-connections."""
        relations = {
            "GENERALIZES": ["Machine Learning"],  # Self-connection
            "PART_OF": ["Machine Learning"],      # Self-connection
            "OPPOSES": ["Traditional Programming"]
        }
        result = obsidian_service.validate_relation_consistency("Machine Learning", relations)
        
        assert len(result) == 2
        assert all("Self-connection found" in inconsistency for inconsistency in result)
    
    def test_validate_empty_relations(self, obsidian_service):
        """Test validation with empty relations."""
        relations = {}
        result = obsidian_service.validate_relation_consistency("Machine Learning", relations)
        
        assert result == []
    
    def test_validate_invalid_relation_types(self, obsidian_service):
        """Test validation with invalid relation types."""
        relations = {
            "INVALID_TYPE": ["Some Concept"],
            "GENERALIZES": ["Deep Learning"]
        }
        result = obsidian_service.validate_relation_consistency("Machine Learning", relations)
        
        # Should only validate the valid relation type
        assert result == []


class TestConexionesSectionUpdate:
    """Test cases for updating Conexiones sections."""
    
    def setup_method(self):
        """Set up test fixtures."""
        # Service will be obtained from test_container in individual test methods
        pass
    
    @patch('builtins.open', create=True)
    @patch('os.path.exists')
    def test_update_conexiones_section_success(self, mock_exists, mock_open, obsidian_service):
        """Test successful update of Conexiones section."""
        mock_exists.return_value = True
        
        # Mock file content
        mock_file_content = """# Test Concept

## Conexiones
- GENERALIZES: [[Deep Learning]]

## Analysis
Some analysis here.
"""
        
        mock_file = MagicMock()
        mock_file.read.return_value = mock_file_content
        mock_file.__enter__.return_value = mock_file
        mock_open.return_value = mock_file
        
        relations = {"PART_OF": ["Artificial Intelligence"]}
        result = obsidian_service.update_conexiones_section("/test/path.md", relations)
        
        assert result is True
        mock_file.write.assert_called_once()
    
    @patch('builtins.open', create=True)
    @patch('os.path.exists')
    def test_update_conexiones_section_no_conexiones(self, mock_exists, mock_open, obsidian_service):
        """Test update when no Conexiones section exists."""
        mock_exists.return_value = True
        
        # Mock file content without Conexiones section
        mock_file_content = """# Test Concept

## Analysis
Some analysis here.
"""
        
        mock_file = MagicMock()
        mock_file.read.return_value = mock_file_content
        mock_file.__enter__.return_value = mock_file
        mock_open.return_value = mock_file
        
        relations = {"PART_OF": ["Artificial Intelligence"]}
        result = obsidian_service.update_conexiones_section("/test/path.md", relations)
        
        assert result is False
    
    @patch('builtins.open', create=True)
    @patch('os.path.exists')
    def test_update_conexiones_section_merge_existing(self, mock_exists, mock_open, obsidian_service):
        """Test that new relations are merged with existing ones."""
        mock_exists.return_value = True
        
        # Mock file content with existing relations
        mock_file_content = """# Test Concept

## Conexiones
- GENERALIZES: [[Deep Learning]]

## Analysis
Some analysis here.
"""
        
        mock_file = MagicMock()
        mock_file.read.return_value = mock_file_content
        mock_file.__enter__.return_value = mock_file
        mock_open.return_value = mock_file
        
        relations = {"GENERALIZES": ["Neural Networks"]}  # Add to existing
        
        result = obsidian_service.update_conexiones_section("/test/path.md", relations)
        
        assert result is True
        mock_file.write.assert_called_once()
        
        # Check that the written content includes both concepts
        written_content = mock_file.write.call_args[0][0]
        assert "[[Deep Learning]]" in written_content
        assert "[[Neural Networks]]" in written_content
    
    def test_update_conexiones_section_file_error(self, obsidian_service):
        """Test handling of file errors."""
        relations = {"PART_OF": ["Artificial Intelligence"]}
        result = obsidian_service.update_conexiones_section("/nonexistent/path.md", relations)
        
        assert result is False


class TestConceptRelationProcessing:
    """Test cases for concept relation processing logic."""
    
    def setup_method(self):
        """Set up test fixtures."""
        # Service will be obtained from test_container in individual test methods
        pass
    
    @pytest.mark.asyncio
    async def test_create_concept_edge_success(self, obsidian_service):
        """Test successful creation of concept edge."""
        # Mock the async method to return a coroutine that resolves to True
        async def mock_create_concept_relation(*args, **kwargs):
            return True
        obsidian_service.concept_repository.create_concept_relation = mock_create_concept_relation
        
        result = await obsidian_service._create_concept_edge(
            "uuid1", "uuid2", "GENERALIZES"
        )
        
        assert result is True
    
    @pytest.mark.asyncio
    async def test_create_concept_edge_failure(self, obsidian_service):
        """Test handling of concept edge creation failure."""
        # Mock the async method to return a coroutine that resolves to False
        async def mock_create_concept_relation(*args, **kwargs):
            return False
        obsidian_service.concept_repository.create_concept_relation = mock_create_concept_relation
        
        result = await obsidian_service._create_concept_edge(
            "uuid1", "uuid2", "GENERALIZES"
        )
        
        assert result is False
    
    @patch.object(ObsidianService, '_build_cache')
    @patch.object(ObsidianService, '_parse_yaml_frontmatter')
    @patch.object(ObsidianService, 'update_link')
    def test_update_concept_relations_frontmatter_success(self, mock_update_link, mock_parse_yaml, mock_build_cache, obsidian_service):
        """Test successful update of concept relations frontmatter."""
        mock_build_cache.return_value = {"Test Concept": "/test/path.md"}
        mock_parse_yaml.return_value = {"entity_id": "uuid1"}
        
        obsidian_service._update_concept_relations_frontmatter(
            "Test Concept", "Target Concept", "GENERALIZES", "uuid1", "uuid2"
        )
        
        mock_update_link.assert_called_once()
        call_args = mock_update_link.call_args[0]
        assert call_args[0] == "Test Concept"
        assert CONCEPT_RELATIONS_KEY in call_args[1]
        assert "GENERALIZES" in call_args[1][CONCEPT_RELATIONS_KEY]
        assert "uuid2" in call_args[1][CONCEPT_RELATIONS_KEY]["GENERALIZES"]
    
    @patch.object(ObsidianService, '_build_cache')
    def test_update_concept_relations_frontmatter_concept_not_found(self, mock_build_cache, obsidian_service):
        """Test handling when concept file is not found."""
        mock_build_cache.return_value = {}
        
        # Should not raise an exception
        obsidian_service._update_concept_relations_frontmatter(
            "Nonexistent Concept", "Target Concept", "GENERALIZES", "uuid1", "uuid2"
        )
    
    @patch.object(ObsidianService, 'update_conexiones_section')
    def test_update_conexiones_with_relation_success(self, mock_update_conexiones, obsidian_service):
        """Test successful update of Conexiones section with relation."""
        mock_update_conexiones.return_value = True
        
        obsidian_service._update_conexiones_with_relation(
            "Test Concept", "Target Concept", "GENERALIZES", "/test/path.md"
        )
        
        mock_update_conexiones.assert_called_once_with("/test/path.md", {"GENERALIZES": ["Target Concept"]})
    
    @patch.object(ObsidianService, 'update_conexiones_section')
    def test_update_conexiones_with_relation_failure(self, mock_update_conexiones, obsidian_service):
        """Test handling of Conexiones section update failure."""
        mock_update_conexiones.return_value = False
        
        # Should not raise an exception
        obsidian_service._update_conexiones_with_relation(
            "Test Concept", "Target Concept", "GENERALIZES", "/test/path.md"
        )


class TestRelationBidirectionalLogic:
    """Test cases for bidirectional relation logic."""
    
    def test_relation_mapping_bidirectional(self):
        """Test that relation mapping correctly handles bidirectional relationships."""
        # Test asymmetric relations
        assert RELATION_MAP["GENERALIZES"] == ("GENERALIZES", "SPECIFIC_OF")
        assert RELATION_MAP["SPECIFIC_OF"] == ("SPECIFIC_OF", "GENERALIZES")
        
        # Test symmetric relations
        assert RELATION_MAP["OPPOSES"] == ("OPPOSES", "OPPOSES")
        assert RELATION_MAP["SIMILAR_TO"] == ("SIMILAR_TO", "SIMILAR_TO")
    
    def test_relation_consistency_validation(self, obsidian_service):
        """Test that relation consistency validation works correctly."""
        # Test with valid relations
        valid_relations = {
            "GENERALIZES": ["Deep Learning"],
            "PART_OF": ["Artificial Intelligence"]
        }
        inconsistencies = obsidian_service.validate_relation_consistency("Machine Learning", valid_relations)
        assert len(inconsistencies) == 0
        
        # Test with self-connections
        invalid_relations = {
            "GENERALIZES": ["Machine Learning"],  # Self-connection
            "PART_OF": ["Artificial Intelligence"]
        }
        inconsistencies = obsidian_service.validate_relation_consistency("Machine Learning", invalid_relations)
        assert len(inconsistencies) == 1
        assert "Self-connection found" in inconsistencies[0]


if __name__ == "__main__":
    pytest.main([__file__])
