"""
Repository for FeelingConcept entities.

This module provides specialized database operations for FeelingConcept entities,
including CRUD operations and feeling-specific queries.
"""

from datetime import datetime
from typing import Any, Dict, List

from ..models.entities import FeelingConcept
from ..models.enums import EntityType
from .base import BaseRepository


class FeelingConceptRepository(BaseRepository[FeelingConcept]):
    """Repository for FeelingConcept entities with specialized feeling operations."""

    @property
    def entity_label(self) -> str:
        return EntityType.FEELING_CONCEPT.value

    @property
    def entity_class(self) -> type[FeelingConcept]:
        return FeelingConcept

    def _node_to_properties(self, node: FeelingConcept) -> Dict[str, Any]:
        """
        Convert Pydantic node to Neo4j properties.
        Handles datetime serialization and other conversions.

        Args:
            node: The FeelingConcept node to convert

        Returns:
            Dictionary of properties suitable for Neo4j
        """
        properties = node.model_dump(exclude_none=True)

        # Convert datetime to ISO string for Neo4j
        if "timestamp" in properties and isinstance(properties["timestamp"], datetime):
            properties["timestamp"] = properties["timestamp"].isoformat()

        return properties

    def _properties_to_node(self, properties: Dict[str, Any]) -> FeelingConcept:
        """
        Convert Neo4j properties to Pydantic node.
        Handles datetime deserialization and other conversions.

        Args:
            properties: Dictionary of properties from Neo4j

        Returns:
            FeelingConcept node
        """
        # Convert ISO string back to datetime
        if "timestamp" in properties and isinstance(properties["timestamp"], str):
            properties["timestamp"] = datetime.fromisoformat(properties["timestamp"])

        return FeelingConcept(**properties)

    async def get_feelings_by_person(self, person_uuid: str) -> List[FeelingConcept]:
        """Get all feelings for a specific person."""
        query = """
        MATCH (f:FeelingConcept)-[:FEELS_ABOUT]->(p:Person)
        WHERE p.uuid = $person_uuid
        RETURN f
        """
        return await self._execute_query(query, person_uuid=person_uuid)

    async def get_feelings_by_concept(self, concept_uuid: str) -> List[FeelingConcept]:
        """Get all feelings about a specific concept."""
        query = """
        MATCH (f:FeelingConcept)-[:FEELS_ABOUT]->(c:Concept)
        WHERE c.uuid = $concept_uuid
        RETURN f
        """
        return await self._execute_query(query, concept_uuid=concept_uuid)

    async def get_feelings_by_person_and_concept(
        self, person_uuid: str, concept_uuid: str
    ) -> List[FeelingConcept]:
        """Get feelings for a specific person about a specific concept."""
        query = """
        MATCH (f:FeelingConcept)-[:FEELS_ABOUT]->(p:Person)
        MATCH (f)-[:FEELS_ABOUT]->(c:Concept)
        WHERE p.uuid = $person_uuid AND c.uuid = $concept_uuid
        RETURN f
        """
        return await self._execute_query(
            query, person_uuid=person_uuid, concept_uuid=concept_uuid
        )
