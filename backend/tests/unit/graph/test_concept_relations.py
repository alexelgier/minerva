"""
Unit tests for concept relation models.

Tests ConceptRelationType and ConceptRelation models.
"""

import pytest
from pydantic import ValidationError

from minerva_backend.graph.models.relations import ConceptRelationType, ConceptRelation


class TestConceptRelationType:
    """Test ConceptRelationType enum."""
    
    def test_enum_values(self):
        """Test that all expected relation types are present."""
        expected_types = [
            "GENERALIZES",
            "SPECIFIC_OF", 
            "PART_OF",
            "HAS_PART",
            "SUPPORTS",
            "SUPPORTED_BY",
            "OPPOSES",
            "SIMILAR_TO",
            "RELATES_TO"
        ]
        
        for relation_type in expected_types:
            assert hasattr(ConceptRelationType, relation_type)
            assert getattr(ConceptRelationType, relation_type) == relation_type
    
    def test_enum_string_representation(self):
        """Test string representation of enum values."""
        assert str(ConceptRelationType.GENERALIZES) == "ConceptRelationType.GENERALIZES"
        assert str(ConceptRelationType.OPPOSES) == "ConceptRelationType.OPPOSES"
        assert str(ConceptRelationType.RELATES_TO) == "ConceptRelationType.RELATES_TO"
    
    def test_enum_comparison(self):
        """Test enum value comparison."""
        assert ConceptRelationType.GENERALIZES == "GENERALIZES"
        assert ConceptRelationType.OPPOSES != "GENERALIZES"
        assert ConceptRelationType.RELATES_TO == ConceptRelationType.RELATES_TO


class TestConceptRelation:
    """Test ConceptRelation model."""
    
    def test_valid_concept_relation(self):
        """Test creating a valid concept relation."""
        relation = ConceptRelation(
            source="source-uuid-123",
            target="target-uuid-456",
            type=ConceptRelationType.GENERALIZES,
            summary_short="Concept relation",
            summary="A generalizes relationship between concepts"
        )
        
        assert relation.source == "source-uuid-123"
        assert relation.target == "target-uuid-456"
        assert relation.type == ConceptRelationType.GENERALIZES
        assert relation.summary_short == "Concept relation"
        assert relation.summary == "A generalizes relationship between concepts"
    
    def test_concept_relation_with_all_fields(self):
        """Test creating a concept relation with all fields."""
        relation = ConceptRelation(
            source="source-uuid-123",
            target="target-uuid-456",
            type=ConceptRelationType.SUPPORTS,
            summary_short="Support relation",
            summary="A supports relationship between concepts",
            embedding=[0.1, 0.2, 0.3]
        )
        
        assert relation.source == "source-uuid-123"
        assert relation.target == "target-uuid-456"
        assert relation.type == ConceptRelationType.SUPPORTS
        assert relation.summary_short == "Support relation"
        assert relation.summary == "A supports relationship between concepts"
        assert relation.partition == "DOMAIN"  # Partition is always DOMAIN for ConceptRelation
        assert relation.embedding == [0.1, 0.2, 0.3]
    
    def test_concept_relation_with_defaults(self):
        """Test creating a concept relation with default values."""
        relation = ConceptRelation(
            source="source-uuid-123",
            target="target-uuid-456",
            type=ConceptRelationType.RELATES_TO,
            summary_short="Related concepts",
            summary="Concepts that are related to each other"
        )
        
        assert relation.partition == "DOMAIN"  # Partition is always DOMAIN for ConceptRelation
        assert relation.embedding is None
    
    def test_concept_relation_validation_error_missing_required(self):
        """Test that missing required fields raise validation error."""
        with pytest.raises(ValidationError):
            ConceptRelation(
                source="source-uuid-123",
                # Missing required fields
            )
    
    def test_concept_relation_validation_error_invalid_type(self):
        """Test that invalid relation type raises validation error."""
        with pytest.raises(ValidationError):
            ConceptRelation(
                source="source-uuid-123",
                target="target-uuid-456",
                type="INVALID_TYPE",  # Invalid relation type
                summary_short="Invalid relation",
                summary="This should fail validation"
            )
    
    def test_concept_relation_validation_error_empty_strings(self):
        """Test that empty strings for required fields raise validation error."""
        with pytest.raises(ValidationError):
            ConceptRelation(
                source="",  # Empty string
                target="target-uuid-456",
                type=ConceptRelationType.GENERALIZES,
                summary_short="Empty source",
                summary="This should fail validation"
            )
    
    def test_concept_relation_different_types(self):
        """Test creating relations with different relation types."""
        relation_types = [
            ConceptRelationType.GENERALIZES,
            ConceptRelationType.SPECIFIC_OF,
            ConceptRelationType.PART_OF,
            ConceptRelationType.HAS_PART,
            ConceptRelationType.SUPPORTS,
            ConceptRelationType.SUPPORTED_BY,
            ConceptRelationType.OPPOSES,
            ConceptRelationType.SIMILAR_TO,
            ConceptRelationType.RELATES_TO
        ]
        
        for relation_type in relation_types:
            relation = ConceptRelation(
                source="source-uuid-123",
                target="target-uuid-456",
                type=relation_type,
                summary_short=f"{relation_type} relation",
                summary=f"A {relation_type} relationship between concepts"
            )
            
            assert relation.type == relation_type
            assert relation.summary_short == f"{relation_type} relation"
    
    def test_concept_relation_inheritance(self):
        """Test that ConceptRelation inherits from Relation."""
        relation = ConceptRelation(
            source="source-uuid-123",
            target="target-uuid-456",
            type=ConceptRelationType.GENERALIZES,
            summary_short="Test relation",
            summary="A test relationship"
        )
        
        # Should have all Relation fields
        assert hasattr(relation, 'source')
        assert hasattr(relation, 'target')
        assert hasattr(relation, 'summary_short')
        assert hasattr(relation, 'summary')
        assert hasattr(relation, 'partition')
        assert hasattr(relation, 'embedding')
        
        # Should have ConceptRelation specific field
        assert hasattr(relation, 'type')
    
    def test_concept_relation_serialization(self):
        """Test that ConceptRelation can be serialized to dict."""
        relation = ConceptRelation(
            source="source-uuid-123",
            target="target-uuid-456",
            type=ConceptRelationType.GENERALIZES,
            summary_short="Test relation",
            summary="A test relationship"
        )
        
        relation_dict = relation.model_dump()
        
        assert isinstance(relation_dict, dict)
        assert relation_dict['source'] == "source-uuid-123"
        assert relation_dict['target'] == "target-uuid-456"
        assert relation_dict['type'] == "GENERALIZES"
        assert relation_dict['summary_short'] == "Test relation"
        assert relation_dict['summary'] == "A test relationship"
    
    def test_concept_relation_from_dict(self):
        """Test creating ConceptRelation from dictionary."""
        relation_data = {
            "source": "source-uuid-123",
            "target": "target-uuid-456",
            "type": "GENERALIZES",
            "summary_short": "Test relation",
            "summary": "A test relationship"
        }
        
        relation = ConceptRelation(**relation_data)
        
        assert relation.source == "source-uuid-123"
        assert relation.target == "target-uuid-456"
        assert relation.type == ConceptRelationType.GENERALIZES
        assert relation.summary_short == "Test relation"
        assert relation.summary == "A test relationship"
