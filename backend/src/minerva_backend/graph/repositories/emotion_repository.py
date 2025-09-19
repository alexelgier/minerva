"""
Emotion Repository for Minerva
Handles all Emotion entity database operations.
"""

from typing import List

from .base import BaseRepository
from ..models.entities import Emotion
from ..models.enums import EntityType


class EmotionRepository(BaseRepository[Emotion]):
    """Repository for Emotion entities with specialized emotion operations."""

    @property
    def entity_label(self) -> str:
        return EntityType.EMOTION.value

    @property
    def entity_class(self) -> type[Emotion]:
        return Emotion

    def search_by_name_partial(self, partial_name: str) -> List[Emotion]:
        """
        Search for emotions by partial name match (case-insensitive).

        Args:
            partial_name: Partial name to search for

        Returns:
            List of emotions with names containing the search term
        """
        query = """
        MATCH (e:Emotion)
        WHERE toLower(e.name) CONTAINS toLower($partial_name)
        RETURN e
        ORDER BY e.name ASC
        """

        with self.connection.session() as session:
            result = session.run(query, partial_name=partial_name)
            emotions = []

            for record in result:
                properties = dict(record["e"])
                emotions.append(self._properties_to_node(properties))

            return emotions

    def get_recently_felt_emotions(self, days: int = 30) -> List[Emotion]:
        """
        Get emotions that have been felt recently.
        Note: This requires relationships through Feeling entities.

        Args:
            days: Number of days to look back

        Returns:
            List of recently felt emotions
        """
        query = """
        MATCH (e:Emotion)<-[:IS_EMOTION]-(f:Feeling)
        WHERE f.timestamp >= datetime() - duration({days: $days})
        RETURN e, count(f) as feeling_count
        ORDER BY feeling_count DESC, e.name ASC
        """

        with self.connection.session() as session:
            result = session.run(query, days=days)
            emotions = []

            for record in result:
                properties = dict(record["e"])
                emotion = self._properties_to_node(properties)
                emotions.append(emotion)

            return emotions

    def get_statistics(self) -> dict:
        """
        Get statistics about emotions in the database.

        Returns:
            Dictionary with emotion statistics
        """
        query = """
        MATCH (e:Emotion)
        OPTIONAL MATCH (e)<-[:IS_EMOTION]-(f:Feeling)
        RETURN 
            count(DISTINCT e) as total_emotions,
            count(DISTINCT f) as total_feelings,
            avg(size((e)<-[:IS_EMOTION]-())) as avg_feelings_per_emotion
        """

        with self.connection.session() as session:
            result = session.run(query)
            record = result.single()

            if record:
                return {
                    "total_emotions": record["total_emotions"],
                    "total_feelings": record["total_feelings"],
                    "avg_feelings_per_emotion": float(record["avg_feelings_per_emotion"] or 0)
                }

            return {
                "total_emotions": 0,
                "total_feelings": 0,
                "avg_feelings_per_emotion": 0.0
            }
