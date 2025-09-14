"""
Event Repository for Minerva
Handles all Event entity database operations.
"""

from datetime import datetime
from typing import List

from .base import BaseRepository
from ..models.entities import Event
from ..models.enums import EntityType


class EventRepository(BaseRepository[Event]):
    """Repository for Event entities with specialized event operations."""

    @property
    def entity_label(self) -> str:
        return EntityType.EVENT.value

    @property
    def entity_class(self) -> type[Event]:
        return Event

    def find_by_category(self, category: str) -> List[Event]:
        """
        Find all events in a specific category.

        Args:
            category: Category to search for

        Returns:
            List of Event entities with matching category
        """
        query = """
        MATCH (e:Event {category: $category})
        RETURN e
        ORDER BY e.date DESC
        """

        with self.connection.session() as session:
            result = session.run(query, category=category)
            events = []

            for record in result:
                properties = dict(record["e"])
                events.append(self._properties_to_entity(properties))

            return events

    def find_by_date_range(self, start_date: datetime, end_date: datetime) -> List[Event]:
        """
        Find all events within a specific date range.

        Args:
            start_date: The start of the date range
            end_date: The end of the date range

        Returns:
            List of Event entities within the date range
        """
        query = """
        MATCH (e:Event)
        WHERE e.date >= $start_date AND e.date <= $end_date
        RETURN e
        ORDER BY e.date ASC
        """

        with self.connection.session() as session:
            result = session.run(query, start_date=start_date, end_date=end_date)
            events = []

            for record in result:
                properties = dict(record["e"])
                events.append(self._properties_to_entity(properties))

            return events
            
    def find_by_location(self, location: str) -> List[Event]:
        """
        Find all events that occurred at a specific location.

        Args:
            location: Location to search for

        Returns:
            List of Event entities with matching location
        """
        query = """
        MATCH (e:Event)
        WHERE toLower(e.location) = toLower($location)
        RETURN e
        ORDER BY e.date DESC
        """

        with self.connection.session() as session:
            result = session.run(query, location=location)
            events = []

            for record in result:
                properties = dict(record["e"])
                events.append(self._properties_to_entity(properties))

            return events

    def search_by_name_partial(self, partial_name: str) -> List[Event]:
        """
        Search for events by partial name match (case-insensitive).

        Args:
            partial_name: Partial name to search for

        Returns:
            List of events with names containing the search term
        """
        query = """
        MATCH (e:Event)
        WHERE toLower(e.name) CONTAINS toLower($partial_name)
        RETURN e
        ORDER BY e.name ASC
        """

        with self.connection.session() as session:
            result = session.run(query, partial_name=partial_name)
            events = []

            for record in result:
                properties = dict(record["e"])
                events.append(self._properties_to_entity(properties))

            return events

    def get_statistics(self) -> dict:
        """
        Get statistics about events in the database.

        Returns:
            Dictionary with event statistics
        """
        query = """
        MATCH (e:Event)
        RETURN 
            count(e) as total_events,
            count(DISTINCT e.category) as unique_categories,
            count(DISTINCT e.location) as unique_locations
        """

        with self.connection.session() as session:
            result = session.run(query)
            record = result.single()

            if record:
                return {
                    "total_events": record["total_events"],
                    "unique_categories": record["unique_categories"],
                    "unique_locations": record["unique_locations"],
                }

            return {
                "total_events": 0,
                "unique_categories": 0,
                "unique_locations": 0,
            }
