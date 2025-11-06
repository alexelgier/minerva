"""
Unit tests for relationship processor.

Tests the RelationshipProcessor class and its refactored methods.
"""

import pytest
from unittest.mock import Mock, AsyncMock
from minerva_backend.processing.extraction.relationship_processor import RelationshipProcessor
from minerva_backend.processing.extraction.context import ExtractionContext
from minerva_backend.processing.models import EntityMapping, CuratableMapping
from minerva_backend.graph.models.entities import Person, Place
from minerva_backend.graph.models.documents import JournalEntry, Span
from minerva_backend.graph.models.relations import Relation
from minerva_backend.prompt.extract_relationships import Relationships


class TestRelationshipProcessor:
    """Test RelationshipProcessor functionality."""

    @pytest.fixture
    def processor(self):
        """Create RelationshipProcessor with mocked dependencies."""
        processor = RelationshipProcessor(
            llm_service=Mock(),
            entity_repositories={},
            span_service=Mock(),
            obsidian_service=Mock()
        )
        return processor

    @pytest.fixture
    def sample_journal_entry(self):
        """Create sample journal entry."""
        return JournalEntry(
            uuid="journal-1",
            date="2024-01-15",
            text="John went to the park with Sarah.",
            entry_text="John went to the park with Sarah."
        )

    @pytest.fixture
    def sample_entities(self):
        """Create sample entities."""
        return [
            EntityMapping(
                entity=Person(
                    uuid="person-1",
                    name="John",
                    summary="A person",
                    summary_short="Person"
                ),
                spans=[]
            ),
            EntityMapping(
                entity=Place(
                    uuid="place-1", 
                    name="park",
                    summary="A location",
                    summary_short="Location"
                ),
                spans=[]
            ),
            EntityMapping(
                entity=Person(
                    uuid="person-2",
                    name="Sarah", 
                    summary="Another person",
                    summary_short="Person"
                ),
                spans=[]
            )
        ]

    @pytest.fixture
    def sample_context(self, sample_journal_entry, sample_entities):
        """Create sample extraction context."""
        context = ExtractionContext(
            journal_entry=sample_journal_entry,
            obsidian_entities={},
            kg_service=Mock()
        )
        context.extracted_entities = sample_entities
        return context

    def test_entity_type_property(self, processor):
        """Test entity_type property."""
        assert processor.entity_type == "Relationship"

    @pytest.mark.asyncio
    async def test_process_no_entities(self, processor):
        """Test process with no extracted entities."""
        context = ExtractionContext(
            journal_entry=Mock(),
            obsidian_entities={},
            kg_service=Mock()
        )
        context.extracted_entities = []
        
        result = await processor.process(context)
        
        assert result == []

    @pytest.mark.asyncio
    async def test_process_with_entities(self, processor, sample_context):
        """Test process with extracted entities."""
        # Mock LLM response
        mock_llm_response = {
            "relationships": [
                {
                    "source": "person-1",
                    "target": "place-1", 
                    "type": "RELATED_TO",
                    "proposed_types": ["VISITED"],
                    "summary_short": "John visited park",
                    "summary": "John visited the park",
                    "spans": ["0:4"],
                    "context": None
                }
            ]
        }
        processor.llm_service.generate = AsyncMock(return_value=mock_llm_response)
        # Create proper Span objects
        span = Span(
            uuid="span-1",
            text="John",
            start=0,
            end=4
        )
        processor.span_service.hydrate_spans_for_text = Mock(return_value=[span])

        result = await processor.process(sample_context)

        assert len(result) == 1
        assert isinstance(result[0], CuratableMapping)
        assert result[0].data.source == "person-1"
        assert result[0].data.target == "place-1"
        assert result[0].data.type == "RELATED_TO"
        assert result[0].data.proposed_types == ["VISITED"]

    @pytest.mark.asyncio
    async def test_process_invalid_uuids(self, processor, sample_context):
        """Test process with invalid UUIDs in relationships."""
        # Mock LLM response with invalid UUID
        mock_llm_response = {
            "relationships": [
                {
                    "source": "invalid-uuid",
                    "target": "place-1",
                    "type": "RELATED_TO",
                    "proposed_types": ["VISITED"],
                    "summary_short": "Invalid relationship",
                    "summary": "Invalid relationship",
                    "spans": ["0:4"],
                    "context": None
                }
            ]
        }
        processor.llm_service.generate = AsyncMock(return_value=mock_llm_response)

        result = await processor.process(sample_context)

        # Should return empty list due to invalid UUID
        assert result == []

    def test_build_entity_context(self, processor, sample_entities):
        """Test building entity context string."""
        result = processor._build_entity_context(sample_entities)
        
        assert "John (EntityType.PERSON)" in result
        assert "park (EntityType.PLACE)" in result
        assert "Sarah (EntityType.PERSON)" in result
        assert "person-1" in result
        assert "place-1" in result
        assert "person-2" in result

    def test_create_entity_map(self, processor, sample_entities):
        """Test creating entity map."""
        result = processor._create_entity_map(sample_entities)
        
        assert "person-1" in result
        assert "place-1" in result
        assert "person-2" in result
        assert result["person-1"].name == "John"
        assert result["place-1"].name == "park"
        assert result["person-2"].name == "Sarah"

    def test_validate_relationship_uuids_valid(self, processor):
        """Test validating relationship with valid UUIDs."""
        mock_rel = Mock()
        mock_rel.source = "person-1"
        mock_rel.target = "place-1"
        mock_rel.context = None
        
        entity_map = {"person-1": Mock(), "place-1": Mock()}
        
        result = processor._validate_relationship_uuids(mock_rel, entity_map)
        assert result is True

    def test_validate_relationship_uuids_invalid(self, processor):
        """Test validating relationship with invalid UUIDs."""
        mock_rel = Mock()
        mock_rel.source = "invalid-uuid"
        mock_rel.target = "place-1"
        mock_rel.context = None
        
        entity_map = {"person-1": Mock(), "place-1": Mock()}
        
        result = processor._validate_relationship_uuids(mock_rel, entity_map)
        assert result is False

    def test_validate_relationship_uuids_with_context(self, processor):
        """Test validating relationship with context entities."""
        mock_rel = Mock()
        mock_rel.source = "person-1"
        mock_rel.target = "place-1"
        mock_context = Mock()
        mock_context.entity_uuid = "person-2"
        mock_rel.context = [mock_context]
        
        entity_map = {"person-1": Mock(), "place-1": Mock(), "person-2": Mock()}
        
        result = processor._validate_relationship_uuids(mock_rel, entity_map)
        assert result is True

    def test_validate_relationship_uuids_invalid_context(self, processor):
        """Test validating relationship with invalid context UUIDs."""
        mock_rel = Mock()
        mock_rel.source = "person-1"
        mock_rel.target = "place-1"
        mock_context = Mock()
        mock_context.entity_uuid = "invalid-context-uuid"
        mock_rel.context = [mock_context]
        
        entity_map = {"person-1": Mock(), "place-1": Mock()}
        
        result = processor._validate_relationship_uuids(mock_rel, entity_map)
        assert result is False

    def test_create_relation_from_detected(self, processor):
        """Test creating Relation from detected relationship."""
        mock_rel = Mock()
        mock_rel.model_dump.return_value = {
            "source": "person-1",
            "target": "place-1",
            "type": "RELATED_TO",
            "proposed_types": ["VISITED"],
            "summary_short": "John visited park",
            "summary": "John visited the park"
        }
        
        result = processor._create_relation_from_detected(mock_rel)
        
        assert isinstance(result, Relation)
        assert result.source == "person-1"
        assert result.target == "place-1"
        assert result.type == "RELATED_TO"
        assert result.proposed_types == ["VISITED"]
        assert result.summary_short == "John visited park"
        assert result.summary == "John visited the park"

    def test_hydrate_relationship_spans_with_spans(self, processor):
        """Test hydrating relationship spans when spans exist."""
        mock_rel = Mock()
        mock_rel.spans = [{"start": 0, "end": 4}]
        processor.span_service.hydrate_spans_for_text = Mock(return_value=["span1"])
        
        result = processor._hydrate_relationship_spans(mock_rel, "John went to the park")
        
        assert result == ["span1"]
        processor.span_service.hydrate_spans_for_text.assert_called_once_with(
            [{"start": 0, "end": 4}], "John went to the park"
        )

    def test_hydrate_relationship_spans_no_spans(self, processor):
        """Test hydrating relationship spans when no spans exist."""
        mock_rel = Mock()
        mock_rel.spans = None
        
        result = processor._hydrate_relationship_spans(mock_rel, "John went to the park")
        
        assert result == []
        processor.span_service.hydrate_spans_for_text.assert_not_called()

    def test_process_detected_relationships(self, processor):
        """Test processing detected relationships."""
        mock_rel1 = Mock()
        mock_rel1.source = "person-1"
        mock_rel1.target = "place-1"
        mock_rel1.context = None
        mock_rel1.spans = [{"start": 0, "end": 4}]
        mock_rel1.model_dump.return_value = {
            "source": "person-1",
            "target": "place-1",
            "type": "RELATED_TO",
            "proposed_types": ["VISITED"],
            "summary_short": "John visited park",
            "summary": "John visited the park"
        }
        
        mock_rel2 = Mock()
        mock_rel2.source = "invalid-uuid"
        mock_rel2.target = "place-1"
        mock_rel2.context = None
        mock_rel2.spans = None
        mock_rel2.model_dump.return_value = {
            "source": "invalid-uuid",
            "target": "place-1",
            "type": "RELATED_TO",
            "proposed_types": ["VISITED"],
            "summary_short": "Invalid relationship",
            "summary": "Invalid relationship"
        }
        
        detected_relationships = [mock_rel1, mock_rel2]
        entity_map = {"person-1": Mock(), "place-1": Mock()}
        # Create proper Span objects
        span = Span(
            uuid="span-1",
            text="John",
            start=0,
            end=4
        )
        processor.span_service.hydrate_spans_for_text = Mock(return_value=[span])
        
        result = processor._process_detected_relationships(
            detected_relationships, entity_map, "John went to the park"
        )
        
        # Should only process the valid relationship
        assert len(result) == 1
        assert isinstance(result[0], CuratableMapping)
        assert result[0].data.source == "person-1"
        assert result[0].data.target == "place-1"
