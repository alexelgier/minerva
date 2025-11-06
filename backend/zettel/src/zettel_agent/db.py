"""Neo4j database connection manager and query functions for zettel_agent."""

from __future__ import annotations

from contextlib import asynccontextmanager
from datetime import datetime
from typing import Any, AsyncContextManager, Dict, List, Type, TypeVar

import neo4j
from neo4j import AsyncDriver, AsyncGraphDatabase, AsyncSession
from pydantic import BaseModel

from minerva_models import Content, Person, Concept, Quote

T = TypeVar("T")


class Neo4jConnectionManager:
    """
    Simple Neo4j connection manager following Neo4j driver best practices.
    One driver instance for app lifetime, with session context management.
    """

    def __init__(self, uri: str, user: str, password: str):
        """Initialize connection parameters. Driver created on first use."""
        self.uri = uri
        self.auth = (user, password)
        self.driver: AsyncDriver | None = None

    async def initialize(self) -> None:
        """Create the async driver (lazy initialization pattern)."""
        if self.driver is None:
            self.driver = AsyncGraphDatabase.driver(self.uri, auth=self.auth)

    @asynccontextmanager
    async def session(self, database: str | None = None) -> AsyncContextManager[AsyncSession]:
        """Async context manager for sessions (recommended pattern)."""
        if self.driver is None:
            await self.initialize()
        async with self.driver.session(database=database) as session:
            yield session

    async def close(self) -> None:
        """Close the driver and cleanup (call at app shutdown)."""
        if self.driver:
            await self.driver.close()
            self.driver = None


def serialize_model(model: BaseModel) -> Dict[str, Any]:
    """
    Convert Pydantic model to Neo4j-compatible dict.
    Converts datetime objects to ISO strings for Neo4j storage.
    """
    properties = model.model_dump()
    for key, value in properties.items():
        if isinstance(value, datetime):
            properties[key] = value.isoformat()
    return properties


def deserialize_to_model(data: Dict[str, Any], model_class: Type[T]) -> T:
    """
    Convert Neo4j result dict to Pydantic model.
    Handles Neo4j time objects and ISO datetime strings.
    """
    # Convert Neo4j time objects
    for key, value in data.items():
        if isinstance(value, neo4j.time.DateTime):
            data[key] = value.to_native()
        elif isinstance(value, neo4j.time.Date):
            data[key] = value.to_native()
        elif isinstance(value, str) and "T" in value and key.endswith(("_at", "timestamp", "date")):
            try:
                data[key] = datetime.fromisoformat(value.replace("Z", "+00:00"))
            except ValueError:
                pass
    return model_class(**data)


async def search_person_by_name(
    session: AsyncSession,
    partial_name: str
) -> List[Person]:
    """Search persons by partial name match."""
    query = """
    MATCH (p:Person)
    WHERE toLower(p.name) CONTAINS toLower($partial_name)
    RETURN p
    ORDER BY p.name ASC
    """
    result = await session.run(query, partial_name=partial_name)
    persons = []
    async for record in result:
        properties = dict(record["p"])
        persons.append(deserialize_to_model(properties, Person))
    return persons


async def create_person(session: AsyncSession, person: Person) -> str:
    """Create Person node, return UUID."""
    query = "CREATE (p:Person $properties) RETURN p.uuid as uuid"
    properties = serialize_model(person)
    result = await session.run(query, properties=properties)
    record = await result.single()
    if not record:
        raise Exception("Failed to create Person")
    return record["uuid"]


async def create_content(session: AsyncSession, content: Content) -> str:
    """Create Content node, return UUID."""
    query = "CREATE (c:Content $properties) RETURN c.uuid as uuid"
    properties = serialize_model(content)
    result = await session.run(query, properties=properties)
    record = await result.single()
    if not record:
        raise Exception("Failed to create Content")
    return record["uuid"]


async def create_authored_by_relationship(
    session: AsyncSession,
    author_uuid: str,
    content_uuid: str
) -> None:
    """Create AUTHORED_BY relationship between Person and Content."""
    query = """
    MATCH (p:Person {uuid: $author_uuid})
    MATCH (c:Content {uuid: $content_uuid})
    CREATE (p)-[:AUTHORED_BY]->(c)
    """
    await session.run(query, author_uuid=author_uuid, content_uuid=content_uuid)


async def create_quotes_for_content(
    session: AsyncSession,
    quotes: List[Quote],
    content_uuid: str
) -> List[str]:
    """Create Quote nodes and QUOTED_IN relationships, return list of UUIDs."""
    if not quotes:
        return []

    quote_properties = [serialize_model(quote) for quote in quotes]
    query = """
    MATCH (c:Content {uuid: $content_uuid})
    UNWIND $quotes AS quote_props
    CREATE (q:Quote)
    SET q = quote_props
    CREATE (q)-[:QUOTED_IN]->(c)
    RETURN q.uuid as uuid
    ORDER BY q.created_at DESC
    """
    result = await session.run(query, content_uuid=content_uuid, quotes=quote_properties)
    uuids = []
    async for record in result:
        uuids.append(record["uuid"])
    return uuids


async def find_content_by_uuid(session: AsyncSession, content_uuid: str) -> Content | None:
    """Find Content node by UUID."""
    query = "MATCH (c:Content {uuid: $uuid}) RETURN c"
    result = await session.run(query, uuid=content_uuid)
    record = await result.single()
    if record:
        properties = dict(record["c"])
        return deserialize_to_model(properties, Content)
    return None


async def find_quotes_by_content(session: AsyncSession, content_uuid: str) -> List[Quote]:
    """Find all quotes linked to a specific content."""
    query = """
    MATCH (q:Quote)-[:QUOTED_IN]->(c:Content {uuid: $content_uuid})
    RETURN q
    ORDER BY q.created_at DESC
    """
    result = await session.run(query, content_uuid=content_uuid)
    quotes = []
    async for record in result:
        properties = dict(record["q"])
        # Exclude embedding field to improve performance
        properties.pop("embedding", None)
        quotes.append(deserialize_to_model(properties, Quote))
    return quotes


async def find_quote_by_uuid(session: AsyncSession, quote_uuid: str) -> Quote | None:
    """Find Quote node by UUID."""
    query = "MATCH (q:Quote {uuid: $uuid}) RETURN q"
    result = await session.run(query, uuid=quote_uuid)
    record = await result.single()
    if record:
        properties = dict(record["q"])
        properties.pop("embedding", None)
        return deserialize_to_model(properties, Quote)
    return None


async def get_unprocessed_quotes(
    session: AsyncSession,
    content_uuid: str,
    processed_uuids: List[str],
    limit: int | None = None
) -> List[Quote]:
    """
    Get quotes for content that haven't been processed yet.
    
    Args:
        session: Neo4j session
        content_uuid: UUID of the content
        processed_uuids: List of quote UUIDs that have already been processed
        limit: Optional limit on number of quotes to return
    
    Returns:
        List of unprocessed Quote objects
    """
    if not processed_uuids:
        # If no processed quotes, get all quotes for content
        query = """
        MATCH (q:Quote)-[:QUOTED_IN]->(c:Content {uuid: $content_uuid})
        RETURN q
        ORDER BY q.created_at DESC
        """
        params = {"content_uuid": content_uuid}
    else:
        query = """
        MATCH (q:Quote)-[:QUOTED_IN]->(c:Content {uuid: $content_uuid})
        WHERE NOT q.uuid IN $processed_uuids
        RETURN q
        ORDER BY q.created_at DESC
        """
        params = {"content_uuid": content_uuid, "processed_uuids": processed_uuids}
    
    if limit:
        query += f" LIMIT {limit}"
    
    result = await session.run(query, **params)
    quotes = []
    async for record in result:
        properties = dict(record["q"])
        properties.pop("embedding", None)
        quotes.append(deserialize_to_model(properties, Quote))
    return quotes


async def find_concept_by_uuid(session: AsyncSession, concept_uuid: str) -> Concept | None:
    """Find Concept node by UUID."""
    query = "MATCH (c:Concept {uuid: $uuid}) RETURN c"
    result = await session.run(query, uuid=concept_uuid)
    record = await result.single()
    if record:
        properties = dict(record["c"])
        return deserialize_to_model(properties, Concept)
    return None


async def vector_search_concepts(
    session: AsyncSession,
    query_embedding: List[float],
    limit: int = 10,
    threshold: float = 0.7
) -> List[Concept]:
    """
    Vector search for Concepts using embedding similarity.
    
    Args:
        session: Neo4j session
        query_embedding: Query embedding vector
        limit: Maximum number of results
        threshold: Minimum similarity threshold (0.0-1.0)
    
    Returns:
        List of Concept objects ordered by similarity
    """
    query = """
    CALL db.index.vector.queryNodes('concept_embeddings_index', $limit, $query_embedding)
    YIELD node, score
    WHERE score >= $threshold
    RETURN node, score
    ORDER BY score DESC
    """
    result = await session.run(
        query,
        query_embedding=query_embedding,
        limit=limit,
        threshold=threshold
    )
    concepts = []
    async for record in result:
        properties = dict(record["node"])
        concept = deserialize_to_model(properties, Concept)
        concepts.append(concept)
    return concepts


def get_neo4j_connection_manager() -> Neo4jConnectionManager:
    """Factory to create configured connection manager."""
    return Neo4jConnectionManager(
        uri="bolt://localhost:7687",
        user="neo4j",
        password="Alxe342!"
    )
