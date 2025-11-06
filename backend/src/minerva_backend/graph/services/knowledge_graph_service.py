from typing import Any, Dict, List, Optional

from minerva_backend.graph.db import Neo4jConnection
from minerva_models import JournalEntry, EntityType
from minerva_backend.graph.repositories.base import BaseRepository
from minerva_backend.graph.repositories.journal_entry_repository import (
    JournalEntryRepository,
)
from minerva_backend.graph.repositories.relation_repository import RelationRepository
from minerva_backend.graph.repositories.temporal_repository import TemporalRepository
from minerva_backend.graph.services.lexical_utils import (
    SpanIndex,
    build_and_insert_lexical_tree,
)
from minerva_backend.obsidian.frontmatter_constants import (
    ENTITY_ID_KEY,
    ENTITY_TYPE_KEY,
    SHORT_SUMMARY_KEY,
    SUMMARY_KEY,
)
from minerva_backend.obsidian.obsidian_service import ObsidianService
from minerva_backend.processing.llm_service import LLMService
from minerva_backend.processing.models import CuratableMapping, EntityMapping


class KnowledgeGraphService:
    """
    Service layer for high-level knowledge graph operations.
    Combines repository actions into complex workflows.
    """

    def __init__(
        self,
        connection: Neo4jConnection,
        llm_service: LLMService,
        emotions_dict: Dict[str, str],
        obsidian_service: ObsidianService,
        journal_entry_repository: JournalEntryRepository,
        temporal_repository: TemporalRepository,
        relation_repository: RelationRepository,
        entity_repositories: Dict[str, BaseRepository],
    ):
        """
        Initializes the service with injected dependencies.
        """
        print(
            f"KnowledgeGraphService initialized with llm_service: {llm_service is not None}"
        )
        self.connection = connection
        self.llm_service = llm_service
        self.journal_entry_repository = journal_entry_repository
        self.temporal_repository = temporal_repository
        self.relation_repository = relation_repository
        self.entity_repositories = entity_repositories
        self.obsidian_service = obsidian_service
        self.emotions_dict = emotions_dict

    async def add_journal_entry(
        self,
        journal_entry: JournalEntry,
        entities: List[EntityMapping],
        relationships: List[CuratableMapping],
    ) -> str:
        """


        Args:
            journal_entry: The JournalEntry object to add.
            entities: Entities extracted with their corresponding spans.
            relationships: Relationships extracted with their corresponding spans and context entities.

        Returns:
            The UUID of the created journal entry.
        """
        node_day = []
        node_mentions: list[tuple[str, str]] = []

        # Create journal node
        journal_uuid = await self.journal_entry_repository.create(journal_entry)

        # Create lexical nodes from journal text
        span_index: Optional[SpanIndex] = await build_and_insert_lexical_tree(
            self.connection, journal_entry
        )
        chunk_uuids = [x[1] for x in span_index] if span_index else []

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
                    entity_uuid = await self.entity_repositories[entity.type].update(
                        entity.uuid,
                        entity.model_dump(exclude_unset=True, exclude_defaults=True),
                    )
                else:
                    entity_uuid = await self.entity_repositories[entity.type].create(
                        entity
                    )
                # Update Obsidian YAML metadata with entity information (summary merging should already be done)
                self.obsidian_service.update_link(
                    entity.name,
                    {
                        ENTITY_ID_KEY: entity_uuid,
                        ENTITY_TYPE_KEY: entity.type,
                        SHORT_SUMMARY_KEY: entity.summary_short,
                        SUMMARY_KEY: entity.summary,
                    },
                )
            for span in spans:
                found_chunks = (
                    span_index.query_containing(span.start, span.end)
                    if span_index
                    else []
                )
                for chunk in found_chunks:
                    # Entity span is in chunk, add mention
                    if entity_uuid and isinstance(chunk[2], str):
                        node_mentions.append((chunk[2], entity_uuid))

        # Create Relationship edge, ReifiedRelationship node, context relations and Mentions
        for r in relationships:
            relationship = r.data
            spans = r.spans
            context = r.context
            # Create RELATED_TO edge and RELATION node
            relationship_uuid = await self.relation_repository.create_full_relationship(
                relationship
            )
            for span in spans:
                found_chunks = (
                    span_index.query_containing(span.start, span.end)
                    if span_index
                    else []
                )
                for chunk in found_chunks:
                    # Relation span is in chunk, add mention
                    if relationship_uuid and isinstance(chunk[2], str):
                        node_mentions.append((chunk[2], relationship_uuid))
            if context and len(context) > 0:
                for relationship_context in context:
                    # Create subsequent RELATED_TO for reified relation
                    await self.relation_repository.create_edge_only(
                        relationship_uuid,
                        relationship_context.entity_uuid,
                        relationship_context.sub_type,
                    )

        # TODO Batch previous insertions
        # Create MENTIONS
        mentions_created = await self.relation_repository.create_mentions_batch(
            node_mentions
        )

        # Ensure time tree has corresponding nodes and link nodes
        await self.temporal_repository.link_nodes_to_day_batch(
            node_day, journal_entry.date
        )

        return journal_uuid

    def get_database_stats(self) -> Dict[str, Any]:
        """
        Retrieves statistics about the database.

        Returns:
            A dictionary with database statistics.
        """
        return self.connection.get_database_stats()
