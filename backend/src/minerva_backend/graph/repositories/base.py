"""
Base Repository Pattern for Minerva
Provides common functionality for all node repositories.
"""

import logging
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict, Generic, List, Optional, TypeVar

import neo4j

from minerva_backend.graph.db import Neo4jConnection
from minerva_models import Node
from minerva_backend.processing.llm_service import LLMService

logger = logging.getLogger(__name__)

# Generic type for nodes
T = TypeVar("T", bound=Node)


class BaseRepository(Generic[T], ABC):
    """
    Abstract base repository providing common CRUD operations.
    All node repositories should inherit from this class.
    """

    def __init__(self, connection: Neo4jConnection, llm_service: LLMService):
        """Initialize repository with database connection and LLM service."""
        self.connection = connection
        self.llm_service = llm_service

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
            if (
                isinstance(value, str)
                and "T" in value
                and key.endswith(("_at", "timestamp", "date"))
            ):
                try:
                    properties[key] = datetime.fromisoformat(
                        value.replace("Z", "+00:00")
                    )
                except ValueError:
                    # If parsing fails, keep as string
                    pass
            elif isinstance(value, neo4j.time.Date):
                properties[key] = value.to_native()  # gives datetime.date
            elif isinstance(value, neo4j.time.DateTime):
                properties[key] = value.to_native()  # gives datetime.datetime

        return self.entity_class(**properties)

    async def create(self, node: T) -> str:
        """
        Create a new node in the database with embedding generation.

        Args:
            node: Pydantic node to create

        Returns:
            str: UUID of created node

        Raises:
            Exception: If creation fails
        """
        # Ensure node has embedding before saving
        node = await self._ensure_embedding(node)
        properties = self._node_to_properties(node)

        query = f"""
        CREATE (e:{self.entity_label} $properties)
        RETURN e.uuid as uuid
        """

        async with self.connection.session_async() as session:
            try:
                result = await session.run(query, properties=properties)
                record = await result.single()

                if not record:
                    raise Exception(f"Failed to create {self.entity_label}")

                node_uuid = record["uuid"]
                log_name = getattr(node, "name", getattr(node, "title", node_uuid))
                logger.info(
                    f"Created {self.entity_label}: {log_name} (UUID: {node_uuid})"
                )
                return node_uuid

            except Exception as e:
                logger.error(f"Error creating {self.entity_label}: {e}")
                raise

    async def find_by_uuid(self, uuid: str) -> Optional[T]:
        """
        Find node by UUID.

        Args:
            uuid: Node UUID

        Returns:
            Node instance or None if not found
        """
        query = f"MATCH (e:{self.entity_label} {{uuid: $uuid}}) RETURN e"

        async with self.connection.session_async() as session:
            result = await session.run(query, uuid=uuid)
            record = await result.single()

            if record:
                properties = dict(record["e"])
                return self._properties_to_node(properties)

            return None

    async def list_all(self, limit: int = 100, offset: int = 0) -> List[T]:
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

        async with self.connection.session_async() as session:
            result = await session.run(query, offset=offset, limit=limit)
            nodes = []

            async for record in result:
                properties = dict(record["e"])
                nodes.append(self._properties_to_node(properties))

            return nodes

    async def update(self, uuid: str, updates: Dict[str, Any]) -> Optional[str]:
        """
        Update node properties with embedding regeneration if summary changed.

        Args:
            uuid: Node UUID
            updates: Dictionary of properties to update

        Returns:
            Optional[str]: UUID if update succeeded, None otherwise
        """
        # Add updated timestamp
        updates["updated_at"] = datetime.now().isoformat()

        # If summary is being updated, regenerate embedding
        if "summary" in updates and updates["summary"]:
            try:
                new_embedding = await self._generate_embedding(updates["summary"])
                updates["embedding"] = new_embedding
                logger.debug(f"Regenerated embedding for {self.entity_label}: {uuid}")
            except Exception as e:
                logger.warning(f"Failed to regenerate embedding for {uuid}: {e}")

        query = f"""
        MATCH (e:{self.entity_label} {{uuid: $uuid}})
        SET e += $updates
        RETURN e.uuid as uuid
        """

        async with self.connection.session_async() as session:
            try:
                result = await session.run(query, uuid=uuid, updates=updates)
                record = await result.single()
                if record and record.get("uuid"):
                    logger.info(f"Updated {self.entity_label}: {uuid}")
                    return record["uuid"]
                return None
            except Exception as e:
                logger.error(f"Error updating {self.entity_label} {uuid}: {e}")
                return None

    async def delete(self, uuid: str) -> bool:
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

        async with self.connection.session_async() as session:
            try:
                result = await session.run(query, uuid=uuid)
                record = await result.single()
                success = record["deleted"] > 0

                if success:
                    logger.info(f"Deleted {self.entity_label}: {uuid}")

                return success

            except Exception as e:
                logger.error(f"Error deleting {self.entity_label} {uuid}: {e}")
                return False

    async def count(self) -> int:
        """
        Count total number of nodes of this type.

        Returns:
            int: Total count
        """
        query = f"MATCH (e:{self.entity_label}) RETURN count(e) as count"

        async with self.connection.session_async() as session:
            result = await session.run(query)
            record = await result.single()
            return record["count"] if record else 0

    async def search_by_text(self, search_term: str, limit: int = 50) -> List[T]:
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

        async with self.connection.session_async() as session:
            result = await session.run(query, search_term=search_term, limit=limit)
            nodes = []

            async for record in result:
                properties = dict(record["e"])
                nodes.append(self._properties_to_node(properties))

            return nodes

    async def exists(self, uuid: str) -> bool:
        """
        Check if node exists by UUID.

        Args:
            uuid: Node UUID

        Returns:
            bool: True if node exists
        """
        query = f"MATCH (e:{self.entity_label} {{uuid: $uuid}}) RETURN count(e) > 0 as exists"

        async with self.connection.session_async() as session:
            result = await session.run(query, uuid=uuid)
            record = await result.single()
            return record["exists"] if record else False

    async def _generate_embedding(self, text: str) -> List[float]:
        """
        Generate embedding for text using LLM service.

        Args:
            text: Text to generate embedding for

        Returns:
            List of float values representing the embedding
        """
        try:
            # Use a simple embedding model - you can adjust this
            embedding = await self.llm_service.create_embedding(text=text)
            return embedding
        except Exception as e:
            logger.error(f"Failed to generate embedding: {e}")
            return []

    async def _ensure_embedding(self, node: T) -> T:
        """
        Ensure node has an embedding. Generate one if missing.

        Args:
            node: Node to ensure has embedding

        Returns:
            Node with embedding (generated if missing)
        """
        if node.embedding is None or len(node.embedding) == 0:
            # Generate embedding from summary
            summary_text = getattr(node, "summary", "")
            if summary_text:
                node.embedding = await self._generate_embedding(summary_text)
                logger.debug(
                    f"Generated embedding for {self.entity_label}: {node.name}"
                )
            else:
                logger.warning(
                    f"No summary available for embedding generation: {node.name}"
                )

        return node

    async def vector_search(
        self, query_text: str, limit: int = 10, threshold: float = 0.7
    ) -> List[T]:
        """
        Search for similar nodes using vector similarity.

        Args:
            query_text: Text to search for
            limit: Maximum number of results
            threshold: Minimum similarity threshold (0.0-1.0)

        Returns:
            List of similar nodes
        """
        try:
            # Generate embedding for query text
            query_embedding = await self._generate_embedding(query_text)
            if not query_embedding:
                logger.warning("Failed to generate embedding for vector search")
                return []

            # Use Neo4j async vector search
            results = await self.connection.vector_search(
                label=self.entity_label,
                query_embedding=query_embedding,
                limit=limit,
                threshold=threshold,
            )

            # Convert results to entity objects
            nodes = []
            for record in results:
                node_properties = dict(record["node"])
                node = self._properties_to_node(node_properties)
                nodes.append(node)

            return nodes

        except Exception as e:
            logger.error(f"Vector search failed: {e}")
            return []

    async def find_similar(self, node: T, limit: int = 5) -> List[T]:
        """
        Find nodes similar to the given node.

        Args:
            node: Node to find similar nodes for
            limit: Maximum number of similar nodes

        Returns:
            List of similar nodes
        """
        if not node.embedding:
            logger.warning(f"No embedding available for similarity search: {node.name}")
            return []

        try:
            # Use Neo4j async vector search with the node's embedding
            results = await self.connection.vector_search(
                label=self.entity_label,
                query_embedding=node.embedding,
                limit=limit + 1,  # +1 to exclude the node itself
                threshold=0.7,
            )

            # Convert results to entity objects and filter out the node itself
            nodes = []
            for record in results:
                node_properties = dict(record["node"])
                if node_properties.get("uuid") != node.uuid:  # Exclude the node itself
                    similar_node = self._properties_to_node(node_properties)
                    nodes.append(similar_node)
                    if len(nodes) >= limit:
                        break

            return nodes

        except Exception as e:
            logger.error(f"Similarity search failed: {e}")
            return []
