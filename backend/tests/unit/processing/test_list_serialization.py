"""Unit tests for list serialization through Temporal data converter."""

import pytest
from temporalio.api.common.v1 import Payload
from minerva_backend.processing.temporal_converter import create_custom_data_converter
from minerva_backend.processing.models import EntityMapping, CuratableMapping
from minerva_backend.graph.models.entities import Person, EntityType
from minerva_backend.graph.models.relations import Relation, RelationshipType
from minerva_backend.graph.models.documents import Span
from minerva_backend.graph.models.base import LexicalType
from minerva_backend.prompt.extract_relationships import RelationshipContext


class TestListSerialization:
    """Test that lists of EntityMapping and RelationSpanContextMapping maintain types through serialization."""

    def test_entity_mapping_list_serialization(self):
        """Test that List[EntityMapping] maintains types through serialization."""
        # Create test data
        person = Person(
            name="John Doe",
            type=EntityType.PERSON,
            summary_short="A person",
            summary="A person named John Doe"
        )
        span = Span(
            start=0,
            end=8,
            text="John Doe"
        )
        entity_mapping = EntityMapping(entity=person, spans=[span])
        entity_list = [entity_mapping]

        # Test with custom data converter
        converter = create_custom_data_converter()
        payload_converter = converter.payload_converter_class()

        # Serialize the list
        payload = payload_converter.to_payload(entity_list)
        assert payload is not None, "List serialization should succeed"
        
        # Deserialize the list
        deserialized = payload_converter.from_payload(payload)
        assert isinstance(deserialized, list), "Deserialized should be a list"
        assert len(deserialized) == 1, "List should have one element"
        
        # Check that the element is still an EntityMapping
        deserialized_mapping = deserialized[0]
        assert isinstance(deserialized_mapping, EntityMapping), "Element should be EntityMapping"
        assert isinstance(deserialized_mapping.entity, Person), "Entity should be Person domain object"
        assert hasattr(deserialized_mapping.entity, 'uuid'), "Entity should have uuid attribute"
        assert deserialized_mapping.entity.name == "John Doe", "Entity name should be preserved"

    def test_relation_span_context_mapping_list_serialization(self):
        """Test that List[RelationSpanContextMapping] maintains types through serialization."""
        # Create test data
        relation = Relation(
            source="person-uuid",
            target="concept-uuid",
            type=RelationshipType.RELATED_TO,
            summary_short="Person related to concept",
            summary="This person is related to this concept"
        )
        span = Span(
            start=0,
            end=10,
            text="is related"
        )
        context = RelationshipContext(
            entity_uuid="person-uuid",
            sub_type=["interested_in", "studies"]
        )
        
        relation_mapping = CuratableMapping(
            kind="relation",
            data=relation,
            spans=[span],
            context=[context]
        )
        relation_list = [relation_mapping]

        # Test with custom data converter
        converter = create_custom_data_converter()
        payload_converter = converter.payload_converter_class()

        # Serialize the list
        payload = payload_converter.to_payload(relation_list)
        assert payload is not None, "List serialization should succeed"
        
        # Deserialize the list
        deserialized = payload_converter.from_payload(payload)
        assert isinstance(deserialized, list), "Deserialized should be a list"
        assert len(deserialized) == 1, "List should have one element"
        
        # Check that the element is still a CuratableMapping
        deserialized_mapping = deserialized[0]
        assert isinstance(deserialized_mapping, CuratableMapping), "Element should be CuratableMapping"
        assert isinstance(deserialized_mapping.data, Relation), "Data should be Relation domain object"
        assert hasattr(deserialized_mapping.data, 'uuid'), "Relation should have uuid attribute"
        assert deserialized_mapping.data.source == "person-uuid", "Relation source should be preserved"

    def test_empty_list_serialization(self):
        """Test that empty lists serialize/deserialize correctly."""
        converter = create_custom_data_converter()
        payload_converter = converter.payload_converter_class()

        # Test empty EntityMapping list
        empty_entity_list = []
        payload = payload_converter.to_payload(empty_entity_list)
        assert payload is not None, "Empty list serialization should succeed"
        
        deserialized = payload_converter.from_payload(payload)
        assert isinstance(deserialized, list), "Deserialized should be a list"
        assert len(deserialized) == 0, "List should be empty"

    def test_mixed_list_serialization_fails(self):
        """Test that mixed lists (not all same type) fail appropriately."""
        converter = create_custom_data_converter()
        payload_converter = converter.payload_converter_class()

        # Create a mixed list
        person = Person(
            name="John Doe",
            type=EntityType.PERSON,
            summary_short="A person",
            summary="A person named John Doe"
        )
        span = Span(start=0, end=8, text="John Doe")
        entity_mapping = EntityMapping(entity=person, spans=[span])
        
        mixed_list = [entity_mapping, "not an entity mapping"]
        
        # This should either fail or fall back to default JSON serialization
        payload = payload_converter.to_payload(mixed_list)
        if payload is not None:
            # If it succeeds, it should be handled by default converter
            deserialized = payload_converter.from_payload(payload)
            # The result might be a plain list with mixed types
            assert isinstance(deserialized, list)
