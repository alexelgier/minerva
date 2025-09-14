"""
Person Repository for Minerva
Handles all Person entity database operations.
"""

from typing import List

from .base import BaseRepository
from ..models.entities import Person
from ..models.enums import EntityType


class PersonRepository(BaseRepository[Person]):
    """Repository for Person entities with specialized person operations."""

    @property
    def entity_label(self) -> str:
        return EntityType.PERSON.value

    @property
    def entity_class(self) -> type[Person]:
        return Person

    def find_by_occupation(self, occupation: str) -> List[Person]:
        """
        Find all persons with a specific occupation.

        Args:
            occupation: Occupation to search for

        Returns:
            List of Person entities with matching occupation
        """
        query = """
        MATCH (p:Person {occupation: $occupation})
        RETURN p
        ORDER BY p.name ASC
        """

        with self.connection.session() as session:
            result = session.run(query, occupation=occupation)
            persons = []

            for record in result:
                properties = dict(record["p"])
                persons.append(self._properties_to_entity(properties))

            return persons

    def find_by_birth_year(self, year: int) -> List[Person]:
        """
        Find all persons born in a specific year.

        Args:
            year: Birth year

        Returns:
            List of Person entities born in that year
        """
        query = """
        MATCH (p:Person)
        WHERE p.birth_date IS NOT NULL 
        AND date(p.birth_date).year = $year
        RETURN p
        ORDER BY p.birth_date ASC
        """

        with self.connection.session() as session:
            result = session.run(query, year=year)
            persons = []

            for record in result:
                properties = dict(record["p"])
                persons.append(self._properties_to_entity(properties))

            return persons

    def get_persons_with_recent_mentions(self, days: int = 30) -> List[Person]:
        """
        Get persons who have been mentioned recently.
        Note: This requires relationships to JournalEntry entities.

        Args:
            days: Number of days to look back

        Returns:
            List of recently mentioned persons
        """
        query = """
        MATCH (p:Person)-[:MENTIONED_IN]->(j:JournalEntry)
        WHERE j.date >= date() - duration({days: $days})
        RETURN p, count(j) as mention_count
        ORDER BY mention_count DESC, p.name ASC
        """

        with self.connection.session() as session:
            result = session.run(query, days=days)
            persons = []

            for record in result:
                properties = dict(record["p"])
                person = self._properties_to_entity(properties)
                # You could add mention_count as a dynamic property if needed
                persons.append(person)

            return persons

    def search_by_name_partial(self, partial_name: str) -> List[Person]:
        """
        Search for persons by partial name match (case-insensitive).

        Args:
            partial_name: Partial name to search for

        Returns:
            List of persons with names containing the search term
        """
        query = """
        MATCH (p:Person)
        WHERE toLower(p.name) CONTAINS toLower($partial_name)
        RETURN p
        ORDER BY p.name ASC
        """

        with self.connection.session() as session:
            result = session.run(query, partial_name=partial_name)
            persons = []

            for record in result:
                properties = dict(record["p"])
                persons.append(self._properties_to_entity(properties))

            return persons

    def get_statistics(self) -> dict:
        """
        Get statistics about persons in the database.

        Returns:
            Dictionary with person statistics
        """
        query = """
        MATCH (p:Person)
        OPTIONAL MATCH (p)-[:MENTIONED_IN]->(j:JournalEntry)
        RETURN 
            count(DISTINCT p) as total_persons,
            count(DISTINCT j) as total_mentions,
            count(DISTINCT p.occupation) as unique_occupations,
            avg(size((p)-[:MENTIONED_IN]->())) as avg_mentions_per_person
        """

        with self.connection.session() as session:
            result = session.run(query)
            record = result.single()

            if record:
                return {
                    "total_persons": record["total_persons"],
                    "total_mentions": record["total_mentions"],
                    "unique_occupations": record["unique_occupations"],
                    "avg_mentions_per_person": float(record["avg_mentions_per_person"] or 0)
                }

            return {
                "total_persons": 0,
                "total_mentions": 0,
                "unique_occupations": 0,
                "avg_mentions_per_person": 0.0
            }
