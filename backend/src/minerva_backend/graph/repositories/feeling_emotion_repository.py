"""
Feeling Repository for Minerva
Handles all Feeling entity database operations.
"""

from datetime import datetime
from typing import Any, Dict, List

from minerva_models import FeelingConcept, FeelingEmotion
from ..models.enums import EntityType
from .base import BaseRepository


class FeelingEmotionRepository(BaseRepository[FeelingEmotion]):
    """Repository for FeelingEmotion entities with specialized feeling operations."""

    @property
    def entity_label(self) -> str:
        return EntityType.FEELING_EMOTION.value

    @property
    def entity_class(self) -> type[FeelingEmotion]:
        return FeelingEmotion

    def _node_to_properties(self, node: FeelingEmotion) -> Dict[str, Any]:
        """
        Convert Pydantic node to Neo4j properties.
        Handles datetime serialization and other conversions.

        Args:
            node: Pydantic node instance

        Returns:
            Dict of properties ready for Neo4j storage
        """
        properties = node.model_dump()

        # Convert datetime objects to ISO strings for Neo4j
        for key, value in properties.items():
            if isinstance(value, datetime):
                properties[key] = value.isoformat()

        return properties

    async def find_by_date_range(
        self, start_date: datetime, end_date: datetime
    ) -> List[FeelingEmotion]:
        """
        Find all feelings within a specific date range.

        Args:
            start_date: The start of the date range
            end_date: The end of the date range

        Returns:
            List of Feeling entities within the date range
        """
        query = """
        MATCH (f:Feeling)
        WHERE f.timestamp >= $start_date AND f.timestamp <= $end_date
        RETURN f
        ORDER BY f.timestamp ASC
        """
        async with self.connection.session_async() as session:
            result = await session.run(query, start_date=start_date, end_date=end_date)
            feelings = []
            async for record in result:
                properties = dict(record["f"])
                feelings.append(self._properties_to_node(properties))
            return feelings

    async def find_by_intensity(self, intensity: int) -> List[FeelingEmotion]:
        """
        Find feelings by a specific intensity level.

        Args:
            intensity: The intensity level (1-10)

        Returns:
            List of Feeling entities with the matching intensity.
        """
        query = """
        MATCH (f:Feeling {intensity: $intensity})
        RETURN f
        ORDER BY f.timestamp DESC
        """
        async with self.connection.session_async() as session:
            result = await session.run(query, intensity=intensity)
            feelings = []
            async for record in result:
                properties = dict(record["f"])
                feelings.append(self._properties_to_node(properties))
            return feelings

    async def get_recent_feelings(self, days: int = 30) -> List[FeelingEmotion]:
        """
        Get feelings that occurred recently.

        Args:
            days: Number of days to look back

        Returns:
            List of recent Feeling entities
        """
        query = """
        MATCH (f:Feeling)
        WHERE f.timestamp >= datetime() - duration({days: $days})
        RETURN f
        ORDER BY f.timestamp DESC
        """
        async with self.connection.session_async() as session:
            result = await session.run(query, days=days)
            feelings = []
            async for record in result:
                properties = dict(record["f"])
                feelings.append(self._properties_to_node(properties))
            return feelings

    async def get_statistics(self) -> dict:
        """
        Get statistics about feelings in the database.

        Returns:
            Dictionary with feeling statistics
        """
        query = """
        MATCH (f:Feeling)
        RETURN 
            count(f) as total_feelings,
            avg(f.intensity) as avg_intensity,
            min(f.intensity) as min_intensity,
            max(f.intensity) as max_intensity
        """
        async with self.connection.session_async() as session:
            result = await session.run(query)
            record = await result.single()

            if record:
                return {
                    "total_feelings": record["total_feelings"],
                    "avg_intensity": float(record["avg_intensity"] or 0),
                    "min_intensity": record["min_intensity"],
                    "max_intensity": record["max_intensity"],
                }

            return {
                "total_feelings": 0,
                "avg_intensity": 0.0,
                "min_intensity": None,
                "max_intensity": None,
            }
