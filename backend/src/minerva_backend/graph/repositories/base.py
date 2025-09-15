"""
Base Repository Pattern for Minerva
Provides common functionality for all node repositories.
"""

from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any, TypeVar, Generic
from datetime import datetime
import logging

from minerva_backend.graph.db import Neo4jConnection
from minerva_backend.graph.models.base import Node

logger = logging.getLogger(__name__)

# Generic type for nodes
T = TypeVar('T', bound=Node)


class BaseRepository(Generic[T], ABC):
    """
    Abstract base repository providing common CRUD operations.
    All node repositories should inherit from this class.
    """

    def __init__(self, connection: Neo4jConnection):
        """Initialize repository with database connection."""
        self.connection = connection

    @property
    @abstractmethod
    def entity_label(self) -> str:
        """Neo4j label for this node type (e.g., 'Person', 'Event')."""
        pass

    @property
    @abstractmethod
    def entity_class(self) -> type[T]:
        """Pydantic model class for this node type."""
        pass

    def _node_to_properties(self, node: T) -> Dict[str, Any]:
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

    def _properties_to_node(self, properties: Dict[str, Any]) -> T:
        """
        Convert Neo4j properties back to Pydantic node.

        Args:
            properties: Dictionary from Neo4j node

        Returns:
            Pydantic node instance
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

    def create(self, node: T) -> str:
        """
        Create a new node in the database.

        Args:
            node: Pydantic node to create

        Returns:
            str: UUID of created node

        Raises:
            Exception: If creation fails
        """
        properties = self._node_to_properties(node)

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

                node_uuid = record["uuid"]
                log_name = getattr(node, 'name', getattr(node, 'title', node_uuid))
                logger.info(f"Created {self.entity_label}: {log_name} (UUID: {node_uuid})")
                return node_uuid

            except Exception as e:
                logger.error(f"Error creating {self.entity_label}: {e}")
                raise

    def find_by_uuid(self, uuid: str) -> Optional[T]:
        """
        Find node by UUID.

        Args:
            uuid: Node UUID

        Returns:
            Node instance or None if not found
        """
        query = f"MATCH (e:{self.entity_label} {{uuid: $uuid}}) RETURN e"

        with self.connection.session() as session:
            result = session.run(query, uuid=uuid)
            record = result.single()

            if record:
                properties = dict(record["e"])
                return self._properties_to_node(properties)

            return None

    def list_all(self, limit: int = 100, offset: int = 0) -> List[T]:
        """
        List all nodes with pagination.

        Args:
            limit: Maximum number of nodes to return
            offset: Number of nodes to skip

        Returns:
            List of node instances
        """
        query = f"""
        MATCH (e:{self.entity_label})
        RETURN e
        ORDER BY e.created_at DESC
        SKIP $offset LIMIT $limit
        """

        with self.connection.session() as session:
            result = session.run(query, offset=offset, limit=limit)
            nodes = []

            for record in result:
                properties = dict(record["e"])
                nodes.append(self._properties_to_node(properties))

            return nodes

    def update(self, uuid: str, updates: Dict[str, Any]) -> bool:
        """
        Update node properties.

        Args:
            uuid: Node UUID
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
        Delete node and all its relationships.

        Args:
            uuid: Node UUID

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
        Count total number of nodes of this type.

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
        Search nodes by text across string properties.

        Args:
            search_term: Text to search for
            limit: Maximum results to return

        Returns:
            List of matching nodes
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
            nodes = []

            for record in result:
                properties = dict(record["e"])
                nodes.append(self._properties_to_node(properties))

            return nodes

    def exists(self, uuid: str) -> bool:
        """
        Check if node exists by UUID.

        Args:
            uuid: Node UUID

        Returns:
            bool: True if node exists
        """
        query = f"MATCH (e:{self.entity_label} {{uuid: $uuid}}) RETURN count(e) > 0 as exists"

        with self.connection.session() as session:
            result = session.run(query, uuid=uuid)
            record = result.single()
            return record["exists"] if record else False
