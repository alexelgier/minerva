"""
Concept Repository for Minerva
Handles all Concept entity database operations.
"""

from typing import List

from .base import BaseRepository
from ..models.entities import Concept
from ..models.enums import EntityType


class ConceptRepository(BaseRepository[Concept]):
    """Repository for Concept entities with specialized concept operations."""

    @property
    def entity_label(self) -> str:
        return EntityType.CONCEPT.value

    @property
    def entity_class(self) -> type[Concept]:
        return Concept

    def search_by_title_partial(self, partial_title: str) -> List[Concept]:
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

        with self.connection.session() as session:
            result = session.run(query, partial_title=partial_title)
            concepts = []

            for record in result:
                properties = dict(record["c"])
                concepts.append(self._properties_to_entity(properties))

            return concepts

    def get_concepts_with_recent_mentions(self, days: int = 30) -> List[Concept]:
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

        with self.connection.session() as session:
            result = session.run(query, days=days)
            concepts = []

            for record in result:
                properties = dict(record["c"])
                concept = self._properties_to_entity(properties)
                concepts.append(concept)

            return concepts

    def get_statistics(self) -> dict:
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

        with self.connection.session() as session:
            result = session.run(query)
            record = result.single()

            if record:
                return {
                    "total_concepts": record["total_concepts"],
                    "total_mentions": record["total_mentions"],
                    "avg_mentions_per_concept": float(record["avg_mentions_per_concept"] or 0)
                }

            return {
                "total_concepts": 0,
                "total_mentions": 0,
                "avg_mentions_per_concept": 0.0
            }
