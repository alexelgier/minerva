"""
Project Repository for Minerva
Handles all Project entity database operations.
"""
from datetime import datetime
from typing import List

from .base import BaseRepository
from ..models.entities import Project, ProjectStatus
from ..models.enums import EntityType


class ProjectRepository(BaseRepository[Project]):
    """Repository for Project entities with specialized project operations."""

    @property
    def entity_label(self) -> str:
        return EntityType.PROJECT.value

    @property
    def entity_class(self) -> type[Project]:
        return Project

    def find_by_status(self, status: ProjectStatus) -> List[Project]:
        """
        Find all projects with a specific status.

        Args:
            status: The status to filter projects by.

        Returns:
            A list of projects matching the status.
        """
        query = """
        MATCH (p:Project {status: $status})
        RETURN p
        ORDER BY p.target_completion ASC
        """
        with self.connection.session() as session:
            result = session.run(query, status=status.value)
            projects = []
            for record in result:
                properties = dict(record["p"])
                projects.append(self._properties_to_entity(properties))
            return projects

    def find_projects_due_soon(self, days: int = 30) -> List[Project]:
        """
        Find projects that are due within a certain number of days.

        Args:
            days: The number of days to look ahead for the due date.

        Returns:
            A list of projects due soon.
        """
        query = """
        MATCH (p:Project)
        WHERE p.target_completion >= date() 
          AND p.target_completion <= date() + duration({days: $days})
          AND NOT p.status IN ['COMPLETED', 'ARCHIVED']
        RETURN p
        ORDER BY p.target_completion ASC
        """
        with self.connection.session() as session:
            result = session.run(query, days=days)
            projects = []
            for record in result:
                properties = dict(record["p"])
                projects.append(self._properties_to_entity(properties))
            return projects

    def search_by_name_partial(self, partial_name: str) -> List[Project]:
        """
        Search for projects by partial name match (case-insensitive).

        Args:
            partial_name: Partial name to search for.

        Returns:
            List of projects with names containing the search term.
        """
        query = """
        MATCH (p:Project)
        WHERE toLower(p.name) CONTAINS toLower($partial_name)
        RETURN p
        ORDER BY p.name ASC
        """
        with self.connection.session() as session:
            result = session.run(query, partial_name=partial_name)
            projects = []
            for record in result:
                properties = dict(record["p"])
                projects.append(self._properties_to_entity(properties))
            return projects

    def get_statistics(self) -> dict:
        """
        Get statistics about projects in the database.

        Returns:
            Dictionary with project statistics.
        """
        query = """
        MATCH (p:Project)
        RETURN
            count(p) as total_projects,
            avg(p.progress) as avg_progress,
            sum(CASE WHEN p.status = 'IN_PROGRESS' THEN 1 ELSE 0 END) as in_progress,
            sum(CASE WHEN p.status = 'COMPLETED' THEN 1 ELSE 0 END) as completed,
            sum(CASE WHEN p.status = 'PLANNED' THEN 1 ELSE 0 END) as planned
        """
        with self.connection.session() as session:
            result = session.run(query)
            record = result.single()

            if record:
                return {
                    "total_projects": record["total_projects"],
                    "avg_progress": float(record["avg_progress"] or 0),
                    "in_progress_count": record["in_progress"],
                    "completed_count": record["completed"],
                    "planned_count": record["planned"],
                }

            return {
                "total_projects": 0,
                "avg_progress": 0.0,
                "in_progress_count": 0,
                "completed_count": 0,
                "planned_count": 0,
            }
