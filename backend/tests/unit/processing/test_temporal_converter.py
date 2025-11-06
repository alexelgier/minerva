"""Unit tests for custom Temporal data converter."""

import pytest
import json
from temporalio.api.common.v1 import Payload
from minerva_backend.processing.temporal_converter import (
    EntityMappingPayloadConverter, 
    CuratableMappingPayloadConverter,
    create_custom_data_converter
)
from minerva_backend.processing.models import EntityMapping, CuratableMapping
from minerva_backend.graph.models.entities import Person, Concept, EntityType
from minerva_backend.graph.models.relations import Relation, ConceptRelation, RelationshipType, ConceptRelationType
from minerva_backend.graph.models.documents import Span
from minerva_backend.prompt.extract_relationships import RelationshipContext


class TestEntityMappingPayloadConverter:
    """Test EntityMapping serialization/deserialization."""
    
    def setup_method(self):
        self.converter = EntityMappingPayloadConverter()
    
    def test_serialize_entity_mapping_with_person(self):
        """Test serialization of EntityMapping with Person entity."""
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
        
        payload = self.converter.to_payload(entity_mapping)
        assert payload is not None
        assert payload.metadata["encoding"] == b"json/entity-mapping"
        
        data = json.loads(payload.data.decode())
        assert data["entity"]["name"] == "John Doe"
        assert data["entity"]["type"] == "Person"
        assert len(data["spans"]) == 1
        assert data["spans"][0]["text"] == "John Doe"
    
    def test_deserialize_entity_mapping_with_person(self):
        """Test deserialization of EntityMapping with Person entity."""
        data = {
            "entity": {
                "name": "John Doe",
                "type": "Person",
                "summary_short": "A person",
                "summary": "A person named John Doe",
                "uuid": "test-uuid",
                "created_at": "2023-01-01T00:00:00",
                "partition": "DOMAIN"
            },
            "spans": [{
                "start": 0,
                "end": 8,
                "text": "John Doe",
                "uuid": "span-uuid",
                "created_at": "2023-01-01T00:00:00",
                "partition": "LEXICAL",
                "type": "Span"
            }]
        }
        
        payload = Payload(
            metadata={"encoding": b"json/entity-mapping"},
            data=json.dumps(data).encode()
        )
        
        result = self.converter.from_payload(payload)
        assert isinstance(result, EntityMapping)
        assert isinstance(result.entity, Person)
        assert result.entity.name == "John Doe"
        assert result.entity.type == EntityType.PERSON
        assert len(result.spans) == 1
        assert isinstance(result.spans[0], Span)
        assert result.spans[0].text == "John Doe"
    
    def test_serialize_entity_mapping_with_concept(self):
        """Test serialization of EntityMapping with Concept entity."""
        concept = Concept(
            name="Machine Learning",
            type=EntityType.CONCEPT,
            summary_short="A field of study",
            summary="Machine Learning is a field of study",
            title="Machine Learning",
            concept="The study of algorithms",
            analysis="My analysis",
            source="Wikipedia"
        )
        span = Span(
            start=0,
            end=16,
            text="Machine Learning"
        )
        entity_mapping = EntityMapping(entity=concept, spans=[span])
        
        payload = self.converter.to_payload(entity_mapping)
        assert payload is not None
        
        data = json.loads(payload.data.decode())
        assert data["entity"]["name"] == "Machine Learning"
        assert data["entity"]["type"] == "Concept"
    
    def test_deserialize_entity_mapping_with_concept(self):
        """Test deserialization of EntityMapping with Concept entity."""
        data = {
            "entity": {
                "name": "Machine Learning",
                "type": "Concept",
                "summary_short": "A field of study",
                "summary": "Machine Learning is a field of study",
                "title": "Machine Learning",
                "concept": "The study of algorithms",
                "analysis": "My analysis",
                "source": "Wikipedia",
                "uuid": "test-uuid",
                "created_at": "2023-01-01T00:00:00",
                "partition": "DOMAIN"
            },
            "spans": [{
                "start": 0,
                "end": 16,
                "text": "Machine Learning",
                "uuid": "span-uuid",
                "created_at": "2023-01-01T00:00:00",
                "partition": "LEXICAL",
                "type": "Span"
            }]
        }
        
        payload = Payload(
            metadata={"encoding": b"json/entity-mapping"},
            data=json.dumps(data).encode()
        )
        
        result = self.converter.from_payload(payload)
        assert isinstance(result, EntityMapping)
        assert isinstance(result.entity, Concept)
        assert result.entity.name == "Machine Learning"
        assert result.entity.type == EntityType.CONCEPT
    
    def test_deserialize_unknown_entity_type_raises_error(self):
        """Test that unknown entity type raises RuntimeError."""
        data = {
            "entity": {
                "name": "Unknown",
                "type": "UnknownType",
                "summary_short": "Unknown",
                "summary": "Unknown entity"
            },
            "spans": []
        }
        
        payload = Payload(
            metadata={"encoding": b"json/entity-mapping"},
            data=json.dumps(data).encode()
        )
        
        with pytest.raises(RuntimeError, match="Unknown entity type"):
            self.converter.from_payload(payload)
    
    def test_deserialize_missing_type_field_raises_error(self):
        """Test that missing type field raises RuntimeError."""
        data = {
            "entity": {
                "name": "No Type",
                "summary_short": "No type",
                "summary": "Entity without type field"
            },
            "spans": []
        }
        
        payload = Payload(
            metadata={"encoding": b"json/entity-mapping"},
            data=json.dumps(data).encode()
        )
        
        with pytest.raises(RuntimeError, match="Entity missing 'type' field"):
            self.converter.from_payload(payload)
    
    def test_serialize_non_entity_mapping_returns_none(self):
        """Test that non-EntityMapping objects return None."""
        result = self.converter.to_payload("not an entity mapping")
        assert result is None


class TestCuratableMappingPayloadConverter:
    """Test CuratableMapping serialization/deserialization."""
    
    def setup_method(self):
        self.converter = CuratableMappingPayloadConverter()
    
    def test_serialize_relation_span_context_mapping(self):
        """Test serialization of RelationSpanContextMapping."""
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
        
        mapping = CuratableMapping(
            kind="relation",
            data=relation,
            spans=[span],
            context=[context]
        )
        
        payload = self.converter.to_payload(mapping)
        assert payload is not None
        assert payload.metadata["encoding"] == b"json/curatable-mapping"
        
        data = json.loads(payload.data.decode())
        assert data["kind"] == "relation"
        assert data["data"]["source"] == "person-uuid"
        assert data["data"]["type"] == "RELATED_TO"
        assert len(data["spans"]) == 1
        assert len(data["context"]) == 1
    
    def test_deserialize_curatable_mapping(self):
        """Test deserialization of CuratableMapping."""
        data = {
            "kind": "relation",
            "data": {
                "source": "person-uuid",
                "target": "concept-uuid",
                "type": "RELATED_TO",
                "summary_short": "Person related to concept",
                "summary": "This person is related to this concept",
                "uuid": "relation-uuid",
                "created_at": "2023-01-01T00:00:00",
                "partition": "DOMAIN"
            },
            "spans": [{
                "start": 0,
                "end": 10,
                "text": "is related",
                "uuid": "span-uuid",
                "created_at": "2023-01-01T00:00:00",
                "partition": "LEXICAL",
                "type": "Span"
            }],
            "context": [{
                "entity_uuid": "person-uuid",
                "sub_type": ["interested_in", "studies"]
            }]
        }
        
        payload = Payload(
            metadata={"encoding": b"json/curatable-mapping"},
            data=json.dumps(data).encode()
        )
        
        result = self.converter.from_payload(payload)
        assert isinstance(result, CuratableMapping)
        assert isinstance(result.data, Relation)
        assert result.data.source == "person-uuid"
        assert result.data.type == RelationshipType.RELATED_TO
        assert len(result.spans) == 1
        assert isinstance(result.spans[0], Span)
        assert len(result.context) == 1
        assert isinstance(result.context[0], RelationshipContext)
    
    def test_deserialize_concept_relation(self):
        """Test deserialization of ConceptRelation."""
        data = {
            "kind": "concept_relation",
            "data": {
                "source": "concept1-uuid",
                "target": "concept2-uuid",
                "type": "GENERALIZES",
                "summary_short": "Concept1 generalizes concept2",
                "summary": "Concept1 is a generalization of concept2",
                "uuid": "relation-uuid",
                "created_at": "2023-01-01T00:00:00",
                "partition": "DOMAIN"
            },
            "spans": [],
            "context": []
        }
        
        payload = Payload(
            metadata={"encoding": b"json/curatable-mapping"},
            data=json.dumps(data).encode()
        )
        
        result = self.converter.from_payload(payload)
        assert isinstance(result, CuratableMapping)
        assert isinstance(result.data, ConceptRelation)
        assert result.data.type == ConceptRelationType.GENERALIZES
    
    def test_deserialize_unknown_kind_raises_error(self):
        """Test that unknown kind raises RuntimeError."""
        data = {
            "kind": "unknown_kind",
            "data": {
                "source": "person-uuid",
                "target": "concept-uuid",
                "summary_short": "No type",
                "summary": "Relation without type field"
            },
            "spans": [],
            "context": []
        }
        
        payload = Payload(
            metadata={"encoding": b"json/curatable-mapping"},
            data=json.dumps(data).encode()
        )
        
        with pytest.raises(RuntimeError, match="Unknown kind: unknown_kind"):
            self.converter.from_payload(payload)
    
    def test_serialize_non_curatable_mapping_returns_none(self):
        """Test that non-CuratableMapping objects return None."""
        result = self.converter.to_payload("not a curatable mapping")
        assert result is None


class TestCustomDataConverter:
    """Test the custom data converter creation."""
    
    def test_create_custom_data_converter(self):
        """Test that custom data converter can be created."""
        converter = create_custom_data_converter()
        assert converter is not None
        assert converter.payload_converter is not None
