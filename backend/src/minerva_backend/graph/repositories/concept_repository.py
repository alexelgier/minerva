import logging
from typing import Any, Dict, List

from minerva_models import Concept
from ..models.enums import EntityType
from .base import BaseRepository

logger = logging.getLogger(__name__)


class ConceptRepository(BaseRepository[Concept]):
    """Repository for Concept entities with specialized concept operations."""

    @property
    def entity_label(self) -> str:
        return EntityType.CONCEPT.value

    @property
    def entity_class(self) -> type[Concept]:
        return Concept

    async def search_by_title_partial(self, partial_title: str) -> List[Concept]:
        """
        Search for concepts by partial title match (case-insensitive).

        Args:
            partial_title: Partial title to search for

        Returns:
            List of concepts with titles containing the search term
        """
        query = """
        MATCH (c:Concept)
        WHERE toLower(c.title) CONTAINS toLower($partial_title)
        RETURN c
        ORDER BY c.title ASC
        """

        async with self.connection.session_async() as session:
            result = await session.run(query, partial_title=partial_title)
            concepts = []

            async for record in result:
                properties = dict(record["c"])
                concepts.append(self._properties_to_node(properties))

            return concepts

    async def get_concepts_with_recent_mentions(self, days: int = 30) -> List[Concept]:
        """
        Get concepts that have been mentioned recently.
        Note: This requires relationships to JournalEntry entities.

        Args:
            days: Number of days to look back

        Returns:
            List of recently mentioned concepts
        """
        query = """
        MATCH (c:Concept)-[:MENTIONED_IN]->(j:JournalEntry)
        WHERE j.date >= date() - duration({days: $days})
        RETURN c, count(j) as mention_count
        ORDER BY mention_count DESC, c.title ASC
        """

        async with self.connection.session_async() as session:
            result = await session.run(query, days=days)
            concepts = []

            async for record in result:
                properties = dict(record["c"])
                concept = self._properties_to_node(properties)
                concepts.append(concept)

            return concepts

    async def get_statistics(self) -> dict:
        """
        Get statistics about concepts in the database.

        Returns:
            Dictionary with concept statistics
        """
        query = """
        MATCH (c:Concept)
        OPTIONAL MATCH (c)-[:MENTIONED_IN]->(j:JournalEntry)
        RETURN 
            count(DISTINCT c) as total_concepts,
            count(DISTINCT j) as total_mentions,
            avg(size((c)-[:MENTIONED_IN]->())) as avg_mentions_per_concept
        """

        async with self.connection.session_async() as session:
            result = await session.run(query)
            record = await result.single()

            if record:
                return {
                    "total_concepts": record["total_concepts"],
                    "total_mentions": record["total_mentions"],
                    "avg_mentions_per_concept": float(
                        record["avg_mentions_per_concept"] or 0
                    ),
                }

            return {
                "total_concepts": 0,
                "total_mentions": 0,
                "avg_mentions_per_concept": 0.0,
            }

    async def find_relevant_concepts(
        self, journal_text: str, limit: int = 5
    ) -> List[Concept]:
        """
        Find concepts relevant to the given journal text using vector similarity.

        Args:
            journal_text: Text from journal entry to find relevant concepts for
            limit: Maximum number of relevant concepts to return

        Returns:
            List of relevant concepts ordered by similarity
        """
        try:
            # Use vector search to find similar concepts
            relevant_concepts = await self.vector_search(
                query_text=journal_text,
                limit=limit,
                threshold=0.6,  # Lower threshold for concept discovery
            )

            logger.info(
                f"Found {len(relevant_concepts)} relevant concepts for journal text"
            )
            return relevant_concepts

        except Exception as e:
            logger.error(f"Failed to find relevant concepts: {e}")
            return []

    async def get_concept_context(self, journal_text: str, limit: int = 3) -> str:
        """
        Get context string of relevant concepts for LLM prompts.

        Args:
            journal_text: Text from journal entry
            limit: Maximum number of concepts to include in context

        Returns:
            Formatted string with concept context for LLM
        """
        try:
            relevant_concepts = await self.find_relevant_concepts(journal_text, limit)

            if not relevant_concepts:
                return "No relevant concepts found in the knowledge base."

            context_parts = []
            for i, concept in enumerate(relevant_concepts, 1):
                context_parts.append(
                    f"{i}. **{concept.title}** (UUID: {concept.uuid})\n"
                    f"   Summary: {concept.summary_short}\n"
                    f"   Analysis: {concept.analysis[:200]}{'...' if len(concept.analysis) > 200 else ''}"
                )

            context = "Relevant concepts from your knowledge base:\n\n" + "\n\n".join(
                context_parts
            )
            return context

        except Exception as e:
            logger.error(f"Failed to get concept context: {e}")
            return "Error retrieving concept context."

    async def find_concept_by_name_or_title(self, name: str) -> Concept | None:
        """
        Find a concept by exact name or title match.

        Args:
            name: Name or title to search for

        Returns:
            Concept if found, None otherwise
        """
        query = """
        MATCH (c:Concept)
        WHERE c.name = $name OR c.title = $name
        RETURN c
        LIMIT 1
        """

        async with self.connection.session_async() as session:
            result = await session.run(query, name=name)
            record = await result.single()

            if record:
                properties = dict(record["c"])
                return self._properties_to_node(properties)

            return None

    async def get_concept_connections(self, concept_uuid: str) -> List[Concept]:
        """
        Get concepts that are connected to the given concept via relationships.

        Args:
            concept_uuid: UUID of the concept to get connections for

        Returns:
            List of connected concepts
        """
        query = """
        MATCH (c:Concept {uuid: $concept_uuid})-[r]-(connected:Concept)
        RETURN DISTINCT connected
        """

        async with self.connection.session_async() as session:
            result = await session.run(query, concept_uuid=concept_uuid)
            connected_concepts = []

            async for record in result:
                properties = dict(record["connected"])
                concept = self._properties_to_node(properties)
                connected_concepts.append(concept)

            return connected_concepts

    async def create_concept_relation(
        self, source_uuid: str, target_uuid: str, relation_type: str
    ) -> bool:
        """
        Create a concept relation edge in Neo4j.

        Args:
            source_uuid: UUID of source concept
            target_uuid: UUID of target concept
            relation_type: Type of relation to create

        Returns:
            True if successful, False otherwise
        """
        query = f"""
        MATCH (source:Concept {{uuid: $source_uuid}})
        MATCH (target:Concept {{uuid: $target_uuid}})
        MERGE (source)-[r:{relation_type}]->(target)
        RETURN r
        """

        async with self.connection.session_async() as session:
            try:
                result = await session.run(
                    query, source_uuid=source_uuid, target_uuid=target_uuid
                )
                record = await result.single()
                success = record is not None

                if success:
                    logger.info(
                        f"Created concept relation: {source_uuid} -[:{relation_type}]-> {target_uuid}"
                    )
                else:
                    logger.warning(
                        f"Failed to create concept relation: {source_uuid} -[:{relation_type}]-> {target_uuid}"
                    )

                return success

            except Exception as e:
                logger.error(
                    f"Error creating concept relation {source_uuid} -[:{relation_type}]-> {target_uuid}: {e}"
                )
                return False

    async def get_concept_relations(self, concept_uuid: str) -> List[Dict[str, Any]]:
        """
        Get all relations for a concept.

        Args:
            concept_uuid: UUID of the concept

        Returns:
            List of relation dictionaries with target_uuid and relation_type
        """
        query = """
        MATCH (c:Concept {uuid: $concept_uuid})-[r]->(target:Concept)
        RETURN target.uuid as target_uuid, type(r) as relation_type
        """

        async with self.connection.session_async() as session:
            try:
                result = await session.run(query, concept_uuid=concept_uuid)
                relations = []

                async for record in result:
                    relations.append(
                        {
                            "target_uuid": record["target_uuid"],
                            "relation_type": record["relation_type"],
                        }
                    )

                return relations

            except Exception as e:
                logger.error(f"Error getting concept relations for {concept_uuid}: {e}")
                return []

    async def delete_concept_relation(
        self, source_uuid: str, target_uuid: str, relation_type: str
    ) -> bool:
        """
        Delete a concept relation edge.

        Args:
            source_uuid: UUID of source concept
            target_uuid: UUID of target concept
            relation_type: Type of relation to delete

        Returns:
            True if successful, False otherwise
        """
        query = f"""
        MATCH (source:Concept {{uuid: $source_uuid}})-[r:{relation_type}]->(target:Concept {{uuid: $target_uuid}})
        DELETE r
        RETURN count(r) as deleted
        """

        async with self.connection.session_async() as session:
            try:
                result = await session.run(
                    query, source_uuid=source_uuid, target_uuid=target_uuid
                )
                record = await result.single()
                success = record["deleted"] > 0

                if success:
                    logger.info(
                        f"Deleted concept relation: {source_uuid} -[:{relation_type}]-> {target_uuid}"
                    )
                else:
                    logger.warning(
                        f"Concept relation not found: {source_uuid} -[:{relation_type}]-> {target_uuid}"
                    )

                return success

            except Exception as e:
                logger.error(
                    f"Error deleting concept relation {source_uuid} -[:{relation_type}]-> {target_uuid}: {e}"
                )
                return False
