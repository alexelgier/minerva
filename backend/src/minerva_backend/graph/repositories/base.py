"""
Base Repository Pattern for Minerva
Provides common functionality for all entity repositories.
"""

from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any, TypeVar, Generic
from datetime import datetime
import logging

from minerva_backend.graph.db import get_connection
from minerva_backend.graph.models.base import Entity

logger = logging.getLogger(__name__)

# Generic type for entities
T = TypeVar('T', bound=Entity)


class BaseRepository(Generic[T], ABC):
    """
    Abstract base repository providing common CRUD operations.
    All entity repositories should inherit from this class.
    """

    def __init__(self):
        """Initialize repository with database connection."""
        self.connection = get_connection()

    @property
    @abstractmethod
    def entity_label(self) -> str:
        """Neo4j label for this entity type (e.g., 'Person', 'Event')."""
        pass

    @property
    @abstractmethod
    def entity_class(self) -> type[T]:
        """Pydantic model class for this entity type."""
        pass

    def _entity_to_properties(self, entity: T) -> Dict[str, Any]:
        """
        Convert Pydantic entity to Neo4j properties.
        Handles datetime serialization and other conversions.

        Args:
            entity: Pydantic entity instance

        Returns:
            Dict of properties ready for Neo4j storage
        """
        properties = entity.model_dump()

        # Convert datetime objects to ISO strings for Neo4j
        for key, value in properties.items():
            if isinstance(value, datetime):
                properties[key] = value.isoformat()

        return properties

    def _properties_to_entity(self, properties: Dict[str, Any]) -> T:
        """
        Convert Neo4j properties back to Pydantic entity.

        Args:
            properties: Dictionary from Neo4j node

        Returns:
            Pydantic entity instance
        """
        # Convert ISO datetime strings back to datetime objects
        for key, value in properties.items():
            if isinstance(value, str) and 'T' in value and key.endswith(('_at', 'timestamp', 'date')):
                try:
                    properties[key] = datetime.fromisoformat(value.replace('Z', '+00:00'))
                except ValueError:
                    # If parsing fails, keep as string
                    pass

        return self.entity_class(**properties)

    def create(self, entity: T) -> str:
        """
        Create a new entity in the database.

        Args:
            entity: Pydantic entity to create

        Returns:
            str: UUID of created entity

        Raises:
            Exception: If creation fails
        """
        properties = self._entity_to_properties(entity)

        query = f"""
        CREATE (e:{self.entity_label} $properties)
        RETURN e.uuid as uuid
        """

        with self.connection.session() as session:
            try:
                result = session.run(query, properties=properties)
                record = result.single()

                if not record:
                    raise Exception(f"Failed to create {self.entity_label}")

                entity_uuid = record["uuid"]
                logger.info(f"Created {self.entity_label}: {entity.name} (UUID: {entity_uuid})")
                return entity_uuid

            except Exception as e:
                logger.error(f"Error creating {self.entity_label}: {e}")
                raise

    def find_by_uuid(self, uuid: str) -> Optional[T]:
        """
        Find entity by UUID.

        Args:
            uuid: Entity UUID

        Returns:
            Entity instance or None if not found
        """
        query = f"MATCH (e:{self.entity_label} {{uuid: $uuid}}) RETURN e"

        with self.connection.session() as session:
            result = session.run(query, uuid=uuid)
            record = result.single()

            if record:
                properties = dict(record["e"])
                return self._properties_to_entity(properties)

            return None

    def find_by_name(self, name: str) -> Optional[T]:
        """
        Find entity by name (exact match).

        Args:
            name: Entity name

        Returns:
            Entity instance or None if not found
        """
        query = f"MATCH (e:{self.entity_label} {{name: $name}}) RETURN e"

        with self.connection.session() as session:
            result = session.run(query, name=name)
            record = result.single()

            if record:
                properties = dict(record["e"])
                return self._properties_to_entity(properties)

            return None

    def list_all(self, limit: int = 100, offset: int = 0) -> List[T]:
        """
        List all entities with pagination.

        Args:
            limit: Maximum number of entities to return
            offset: Number of entities to skip

        Returns:
            List of entity instances
        """
        query = f"""
        MATCH (e:{self.entity_label})
        RETURN e
        ORDER BY e.created_at DESC
        SKIP $offset LIMIT $limit
        """

        with self.connection.session() as session:
            result = session.run(query, offset=offset, limit=limit)
            entities = []

            for record in result:
                properties = dict(record["e"])
                entities.append(self._properties_to_entity(properties))

            return entities

    def update(self, uuid: str, updates: Dict[str, Any]) -> bool:
        """
        Update entity properties.

        Args:
            uuid: Entity UUID
            updates: Dictionary of properties to update

        Returns:
            bool: True if update succeeded
        """
        # Add updated timestamp
        updates['updated_at'] = datetime.now().isoformat()

        query = f"""
        MATCH (e:{self.entity_label} {{uuid: $uuid}})
        SET e += $updates
        RETURN e.uuid as uuid
        """

        with self.connection.session() as session:
            try:
                result = session.run(query, uuid=uuid, updates=updates)
                record = result.single()
                success = record is not None

                if success:
                    logger.info(f"Updated {self.entity_label}: {uuid}")

                return success

            except Exception as e:
                logger.error(f"Error updating {self.entity_label} {uuid}: {e}")
                return False

    def delete(self, uuid: str) -> bool:
        """
        Delete entity and all its relationships.

        Args:
            uuid: Entity UUID

        Returns:
            bool: True if deletion succeeded
        """
        query = f"""
        MATCH (e:{self.entity_label} {{uuid: $uuid}})
        DETACH DELETE e
        RETURN count(e) as deleted
        """

        with self.connection.session() as session:
            try:
                result = session.run(query, uuid=uuid)
                record = result.single()
                success = record["deleted"] > 0

                if success:
                    logger.info(f"Deleted {self.entity_label}: {uuid}")

                return success

            except Exception as e:
                logger.error(f"Error deleting {self.entity_label} {uuid}: {e}")
                return False

    def count(self) -> int:
        """
        Count total number of entities of this type.

        Returns:
            int: Total count
        """
        query = f"MATCH (e:{self.entity_label}) RETURN count(e) as count"

        with self.connection.session() as session:
            result = session.run(query)
            record = result.single()
            return record["count"] if record else 0

    def search_by_text(self, search_term: str, limit: int = 50) -> List[T]:
        """
        Search entities by text across string properties.

        Args:
            search_term: Text to search for
            limit: Maximum results to return

        Returns:
            List of matching entities
        """
        query = f"""
        MATCH (e:{self.entity_label})
        WHERE any(prop in keys(e) WHERE toString(e[prop]) CONTAINS $search_term)
        RETURN e
        ORDER BY e.created_at DESC
        LIMIT $limit
        """

        with self.connection.session() as session:
            result = session.run(query, search_term=search_term, limit=limit)
            entities = []

            for record in result:
                properties = dict(record["e"])
                entities.append(self._properties_to_entity(properties))

            return entities

    def exists(self, uuid: str) -> bool:
        """
        Check if entity exists by UUID.

        Args:
            uuid: Entity UUID

        Returns:
            bool: True if entity exists
        """
        query = f"MATCH (e:{self.entity_label} {{uuid: $uuid}}) RETURN count(e) > 0 as exists"

        with self.connection.session() as session:
            result = session.run(query, uuid=uuid)
            record = result.single()
            return record["exists"] if record else False
