from datetime import date
from typing import Any, Dict, List, Tuple

from minerva_backend.graph.db import Neo4jConnection
from minerva_backend.graph.models.documents import JournalEntry, Span
from minerva_backend.graph.models.entities import Entity
from minerva_backend.graph.models.relations import Relation
from minerva_backend.graph.repositories.concept_repository import ConceptRepository
from minerva_backend.graph.repositories.emotion_repository import EmotionRepository
from minerva_backend.graph.repositories.event_repository import EventRepository
from minerva_backend.graph.repositories.feeling_repository import FeelingRepository
from minerva_backend.graph.repositories.journal_entry_repository import (
    JournalEntryRepository,
)
from minerva_backend.graph.repositories.person_repository import PersonRepository
from minerva_backend.graph.repositories.project_repository import ProjectRepository
from minerva_backend.graph.repositories.resource_repository import ResourceRepository
from minerva_backend.graph.repositories.temporal_repository import TemporalRepository
from minerva_backend.processing.models import EntitySpanMapping, RelationSpanContextMapping
from minerva_backend.prompt.extract_relationships import RelationshipContext


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
        self.person_repository = PersonRepository(self.connection)
        self.emotion_repository = EmotionRepository(self.connection)
        self.event_repository = EventRepository(self.connection)
        self.project_repository = ProjectRepository(self.connection)
        self.concept_repository = ConceptRepository(self.connection)
        self.resource_repository = ResourceRepository(self.connection)
        self.feeling_repository = FeelingRepository(self.connection)
        self.journal_entry_repository = JournalEntryRepository(self.connection)
        self.temporal_repository = TemporalRepository(self.connection)

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
        # Create lexical nodes from journal text.
        # Ensure time tree has corresponding nodes
        day_uuid = self.temporal_repository.ensure_day_in_time_tree(journal_entry.date)
        journal_uuid = self.journal_entry_repository.create(journal_entry)

        self.journal_entry_repository.connect_to_day(journal_uuid, day_uuid)
        return journal_uuid

    def get_database_stats(self) -> Dict[str, Any]:
        """
        Retrieves statistics about the database.

        Returns:
            A dictionary with database statistics.
        """
        return self.connection.get_database_stats()
