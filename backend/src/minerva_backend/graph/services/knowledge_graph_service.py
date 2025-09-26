from typing import Any, Dict, List

from minerva_backend.graph.db import Neo4jConnection
from minerva_backend.graph.models.documents import JournalEntry
from minerva_backend.graph.models.entities import EntityType
from minerva_backend.graph.repositories.base import BaseRepository
from minerva_backend.graph.repositories.concept_repository import ConceptRepository
from minerva_backend.graph.repositories.consumable_repository import ConsumableRepository
from minerva_backend.graph.repositories.content_repository import ContentRepository
from minerva_backend.graph.repositories.emotion_repository import EmotionRepository
from minerva_backend.graph.repositories.event_repository import EventRepository
from minerva_backend.graph.repositories.feeling_repository import FeelingRepository
from minerva_backend.graph.repositories.journal_entry_repository import (
    JournalEntryRepository,
)
from minerva_backend.graph.repositories.person_repository import PersonRepository
from minerva_backend.graph.repositories.place_repository import PlaceRepository
from minerva_backend.graph.repositories.project_repository import ProjectRepository
from minerva_backend.graph.repositories.relation_repository import RelationRepository
from minerva_backend.graph.repositories.temporal_repository import TemporalRepository
from minerva_backend.graph.services.lexical_utils import build_and_insert_lexical_tree, SpanIndex
from minerva_backend.obsidian.obsidian_service import ObsidianService
from minerva_backend.processing.models import EntitySpanMapping, RelationSpanContextMapping


class KnowledgeGraphService:
    """
    Service layer for high-level knowledge graph operations.
    Combines repository actions into complex workflows.
    """

    def __init__(self, connection: Neo4jConnection, emotions_dict: Dict[str, str]):
        """
        Initializes the service with a database connection and all repositories.
        """
        self.connection = connection
        self.journal_entry_repository = JournalEntryRepository(self.connection)
        self.temporal_repository = TemporalRepository(self.connection)
        self.relation_repository = RelationRepository(self.connection)
        self.entity_repositories: Dict[str, BaseRepository] = {
            'Person': PersonRepository(self.connection),
            'Feeling': FeelingRepository(self.connection),
            'Emotion': EmotionRepository(self.connection),
            'Event': EventRepository(self.connection),
            'Project': ProjectRepository(self.connection),
            'Concept': ConceptRepository(self.connection),
            'Content': ContentRepository(self.connection),
            'Consumable': ConsumableRepository(self.connection),
            'Place': PlaceRepository(self.connection),
        }
        self.obsidian_service = ObsidianService()
        self.emotions_dict = emotions_dict

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
        node_day = []
        node_mentions = []

        # Create journal node
        journal_uuid = self.journal_entry_repository.create(journal_entry)

        # Create lexical nodes from journal text
        span_index: SpanIndex = build_and_insert_lexical_tree(self.connection, journal_entry)
        chunk_uuids = [x[1] for x in span_index]

        # Link journal and chunks to day
        node_day.append(journal_uuid)
        node_day.extend(chunk_uuids)

        # Create Entity and Mentions
        for e in entities:
            entity = e.entity
            spans = e.spans
            if entity.type == EntityType.EMOTION:
                # Map emotion name to standard emotion if possible
                mapped_name = self.emotions_dict.get(entity.name.lower())
                if mapped_name:
                    entity.name = mapped_name
            else:
                # Create/Update Entity
                # TODO figure out if entity is linked to journal date (or other?)
                if self.entity_repositories[entity.type].exists(entity.uuid):
                    entity_uuid = self.entity_repositories[entity.type].update(entity.uuid,
                                                                               entity.model_dump(exclude_unset=True,
                                                                                                 exclude_defaults=True))
                else:
                    entity_uuid = self.entity_repositories[entity.type].create(entity)
                # Update Obsidian YAML metadata with entity information (summary merging should already be done)
                self.obsidian_service.update_link(entity.name, {"entity_id": entity_uuid, "entity_type": entity.type,
                                                                "short_summary": entity.summary_short})
            for span in spans:
                found_chunks = span_index.query_containing(span.start, span.end)
                for chunk in found_chunks:
                    # Entity span is in chunk, add mention
                    node_mentions.append((chunk[2], entity_uuid))

        # Create Relationship edge, ReifiedRelationship node, context relations and Mentions
        for r in relationships:
            relationship = r.relation
            spans = r.spans
            context = r.context
            # Create RELATED_TO edge and RELATION node
            relationship_uuid = self.relation_repository.create_full_relationship(relationship)
            for span in spans:
                found_chunks = span_index.query_containing(span.start, span.end)
                for chunk in found_chunks:
                    # Relation span is in chunk, add mention
                    node_mentions.append((chunk[2], relationship_uuid))
            if context and len(context) > 0:
                for entity in context:
                    # Create subsequent RELATED_TO for reified relation
                    self.relation_repository.create_edge_only(relationship_uuid, entity.entity_uuid, entity.sub_type)

        # TODO Batch previous insertions
        # Create MENTIONS
        mentions_created = self.relation_repository.create_mentions_batch(node_mentions)

        # Ensure time tree has corresponding nodes and link nodes
        self.temporal_repository.link_nodes_to_day_batch(node_day, journal_entry.date)

        return journal_uuid

    def get_database_stats(self) -> Dict[str, Any]:
        """
        Retrieves statistics about the database.

        Returns:
            A dictionary with database statistics.
        """
        return self.connection.get_database_stats()
