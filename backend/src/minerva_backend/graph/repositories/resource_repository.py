"""
Resource Repository for Minerva
Handles all Resource entity database operations.
"""
from typing import List

from .base import BaseRepository
from ..models.entities import Resource
from ..models.enums import ResourceType, ResourceStatus, EntityType


class ResourceRepository(BaseRepository[Resource]):
    """Repository for Resource entities with specialized resource operations."""

    @property
    def entity_label(self) -> str:
        return EntityType.RESOURCE.value

    @property
    def entity_class(self) -> type[Resource]:
        return Resource

    def find_by_category(self, category: ResourceType) -> List[Resource]:
        """
        Find all resources in a specific category.

        Args:
            category: Category to search for

        Returns:
            List of Resource entities with matching category
        """
        query = """
        MATCH (r:Resource {category: $category})
        RETURN r
        ORDER BY r.title ASC
        """

        with self.connection.session() as session:
            result = session.run(query, category=category.value)
            resources = []

            for record in result:
                properties = dict(record["r"])
                resources.append(self._properties_to_entity(properties))

            return resources

    def find_by_status(self, status: ResourceStatus) -> List[Resource]:
        """
        Find all resources with a specific status.

        Args:
            status: The status to filter resources by.

        Returns:
            A list of resources matching the status.
        """
        query = """
        MATCH (r:Resource {status: $status})
        RETURN r
        ORDER BY r.title ASC
        """
        with self.connection.session() as session:
            result = session.run(query, status=status.value)
            resources = []
            for record in result:
                properties = dict(record["r"])
                resources.append(self._properties_to_entity(properties))
            return resources

    def find_by_author(self, author: str) -> List[Resource]:
        """
        Find all resources by a specific author.

        Args:
            author: The author to search for.

        Returns:
            A list of resources by the given author.
        """
        query = """
        MATCH (r:Resource)
        WHERE toLower(r.author) = toLower($author)
        RETURN r
        ORDER BY r.title ASC
        """
        with self.connection.session() as session:
            result = session.run(query, author=author)
            resources = []
            for record in result:
                properties = dict(record["r"])
                resources.append(self._properties_to_entity(properties))
            return resources

    def search_by_title_partial(self, partial_title: str) -> List[Resource]:
        """
        Search for resources by partial title match (case-insensitive).

        Args:
            partial_title: Partial title to search for.

        Returns:
            List of resources with titles containing the search term.
        """
        query = """
        MATCH (r:Resource)
        WHERE toLower(r.title) CONTAINS toLower($partial_title)
        RETURN r
        ORDER BY r.title ASC
        """
        with self.connection.session() as session:
            result = session.run(query, partial_title=partial_title)
            resources = []
            for record in result:
                properties = dict(record["r"])
                resources.append(self._properties_to_entity(properties))
            return resources

    def get_statistics(self) -> dict:
        """
        Get statistics about resources in the database.

        Returns:
            Dictionary with resource statistics.
        """
        query = """
        MATCH (r:Resource)
        RETURN
            count(r) as total_resources,
            count(DISTINCT r.category) as unique_categories,
            count(DISTINCT r.author) as unique_authors,
            sum(CASE WHEN r.status = 'PENDING' THEN 1 ELSE 0 END) as pending,
            sum(CASE WHEN r.status = 'IN_PROGRESS' THEN 1 ELSE 0 END) as in_progress,
            sum(CASE WHEN r.status = 'COMPLETED' THEN 1 ELSE 0 END) as completed
        """
        with self.connection.session() as session:
            result = session.run(query)
            record = result.single()

            if record:
                return {
                    "total_resources": record["total_resources"],
                    "unique_categories": record["unique_categories"],
                    "unique_authors": record["unique_authors"],
                    "pending_count": record["pending"],
                    "in_progress_count": record["in_progress"],
                    "completed_count": record["completed"],
                }

            return {
                "total_resources": 0,
                "unique_categories": 0,
                "unique_authors": 0,
                "pending_count": 0,
                "in_progress_count": 0,
                "completed_count": 0,
            }
