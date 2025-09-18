from typing import Any, Dict, List, Tuple, Type

from minerva_backend.graph.db import Neo4jConnection
from minerva_backend.graph.models.documents import JournalEntry
from minerva_backend.graph.models.entities import Person, Feeling, Emotion, Event, Project, Concept, Content, \
    Consumable, Place, Entity
from minerva_backend.graph.repositories.base import BaseRepository
from minerva_backend.graph.repositories.concept_repository import ConceptRepository
from minerva_backend.graph.repositories.consumable_repository import ConsumableRepository
from minerva_backend.graph.repositories.emotion_repository import EmotionRepository
from minerva_backend.graph.repositories.event_repository import EventRepository
from minerva_backend.graph.repositories.feeling_repository import FeelingRepository
from minerva_backend.graph.repositories.journal_entry_repository import (
    JournalEntryRepository,
)
from minerva_backend.graph.repositories.person_repository import PersonRepository
from minerva_backend.graph.repositories.place_repository import PlaceRepository
from minerva_backend.graph.repositories.project_repository import ProjectRepository
from minerva_backend.graph.repositories.content_repository import ContentRepository
from minerva_backend.graph.repositories.temporal_repository import TemporalRepository
from minerva_backend.graph.services.lexical_utils import build_and_insert_lexical_tree
from minerva_backend.processing.models import EntitySpanMapping, RelationSpanContextMapping


class KnowledgeGraphService:
    """
    Service layer for high-level knowledge graph operations.
    Combines repository actions into complex workflows.
    """

    def __init__(self, connection: Neo4jConnection):
        """
        Initializes the service with a database connection and all repositories.
        """
        self.connection = connection
        self.journal_entry_repository = JournalEntryRepository(self.connection)
        self.temporal_repository = TemporalRepository(self.connection)
        self.entity_repositories: Dict[Type[Entity], BaseRepository] = {
            Person: PersonRepository(self.connection),
            Feeling: FeelingRepository(self.connection),
            Emotion: EmotionRepository(self.connection),
            Event: EventRepository(self.connection),
            Project: ProjectRepository(self.connection),
            Concept: ConceptRepository(self.connection),
            Content: ContentRepository(self.connection),
            Consumable: ConsumableRepository(self.connection),
            Place: PlaceRepository(self.connection),
        }

    def add_journal_entry(self, journal_entry: JournalEntry,
                          entities: List[EntitySpanMapping],
                          relationships: List[RelationSpanContextMapping]) -> str:
        """


        Args:
            journal_entry: The JournalEntry object to add.
            entities: Entities extracted with their corresponding spans.
            relationships: Relationships extracted with their corresponding spans and context entities.

        Returns:
            The UUID of the created journal entry.
        """
        # Ensure time tree has corresponding nodes
        journal_uuid = self.journal_entry_repository.create(journal_entry)
        day_uuid = self.temporal_repository.link_node_to_day(journal_uuid, journal_entry.date)

        # Create lexical nodes from journal text.
        spans_dict: Dict[Tuple[int, int], str] = build_and_insert_lexical_tree(self.connection, journal_entry)

        # Create Entity Mentions

        node_mentions = []
        for e in entities:
            entity = e.entity
            spans = e.spans
            entity_uuid = self.entity_repositories[type(entity)].create(entity)
            for span in spans:
                for chunk_span in spans_dict:
                    if span.start >= chunk_span[0] and span.end <= chunk_span[1]:
                        # span is in chunk
                        node_mentions.append((entity_uuid, spans_dict[chunk_span]))

        for r in relationships:
            relationship = r.relation
            spans = r.spans
            context = r.context
            # create relationship and reifiedrelationship
            for span in spans:
                for chunk_span in spans_dict:
                    if span.start >= chunk_span[0] and span.end <= chunk_span[1]:
                        # span is in chunk
                        node_mentions.append((reifiedrelationship.relationship.uuid, spans_dict[chunk_span]))
            for entity in relationship_s_c.context:
                # handle subsequent relations for reified relation
                entity.entity_uuid
                entity.sub_type

        # Create Relation Mentions

        return journal_uuid

    def get_database_stats(self) -> Dict[str, Any]:
        """
        Retrieves statistics about the database.

        Returns:
            A dictionary with database statistics.
        """
        return self.connection.get_database_stats()
