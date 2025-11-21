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
    Uses lazy initialization to create the driver on first use.
    
    Example:
        ```python
        manager = Neo4jConnectionManager(
            uri="bolt://localhost:7687",
            user="neo4j",
            password="password"
        )
        async with manager.session() as session:
            result = await session.run("MATCH (n) RETURN count(n)")
        await manager.close()
        ```
    """

    def __init__(self, uri: str, user: str, password: str):
        """
        Initialize connection parameters. Driver created on first use.
        
        Args:
            uri: Neo4j connection URI (e.g., "bolt://localhost:7687")
            user: Neo4j username
            password: Neo4j password
        """
        self.uri = uri
        self.auth = (user, password)
        self.driver: AsyncDriver | None = None

    async def initialize(self) -> None:
        """
        Create the async driver (lazy initialization pattern).
        
        This method is called automatically on first session creation.
        Can be called manually to initialize the driver early.
        """
        if self.driver is None:
            self.driver = AsyncGraphDatabase.driver(self.uri, auth=self.auth)

    @asynccontextmanager
    async def session(self, database: str | None = None) -> AsyncContextManager[AsyncSession]:
        """
        Async context manager for sessions (recommended pattern).
        
        Args:
            database: Database name (defaults to "neo4j" if None)
            
        Yields:
            AsyncSession: Neo4j async session
            
        Example:
            ```python
            async with manager.session() as session:
                result = await session.run("MATCH (n) RETURN n")
            ```
        """
        if self.driver is None:
            await self.initialize()
        async with self.driver.session(database=database) as session:
            yield session

    async def close(self) -> None:
        """
        Close the driver and cleanup (call at app shutdown).
        
        This should be called when the application is shutting down
        to properly close the Neo4j driver connection.
        """
        if self.driver:
            await self.driver.close()
            self.driver = None


def serialize_model(model: BaseModel) -> Dict[str, Any]:
    """
    Convert Pydantic model to Neo4j-compatible dict.
    
    Converts datetime objects to ISO strings for Neo4j storage.
    All other fields are passed through as-is.
    
    Args:
        model: Pydantic model to serialize
        
    Returns:
        Dictionary with datetime objects converted to ISO strings
        
    Example:
        ```python
        from minerva_models import Content
        from datetime import datetime
        
        content = Content(title="Test", created_at=datetime.now())
        properties = serialize_model(content)
        # properties["created_at"] is now an ISO string
        ```
    """
    properties = model.model_dump()
    for key, value in properties.items():
        if isinstance(value, datetime):
            properties[key] = value.isoformat()
    return properties


def deserialize_to_model(data: Dict[str, Any], model_class: Type[T]) -> T:
    """
    Convert Neo4j result dict to Pydantic model.
    
    Handles Neo4j time objects and ISO datetime strings by converting
    them to Python datetime objects. Fields ending with "_at", "timestamp",
    or "date" are automatically parsed from ISO strings.
    
    Args:
        data: Dictionary from Neo4j result record
        model_class: Pydantic model class to deserialize to
        
    Returns:
        Instance of the model class
        
    Example:
        ```python
        from minerva_models import Content
        
        record = {
            "uuid": "123",
            "title": "Test",
            "created_at": "2024-01-01T00:00:00"
        }
        content = deserialize_to_model(record, Content)
        # content.created_at is now a datetime object
        ```
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
    """
    Search persons by partial name match (case-insensitive).
    
    Args:
        session: Neo4j session
        partial_name: Partial name to search for (case-insensitive)
        
    Returns:
        List of matching Person objects, ordered by name ascending
        
    Example:
        ```python
        async with connection_manager.session() as session:
            persons = await search_person_by_name(session, "Lenin")
            # Returns all persons with "Lenin" in their name
        ```
    """
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
    """
    Create Person node in Neo4j, return UUID.
    
    Args:
        session: Neo4j session
        person: Person object to create
        
    Returns:
        UUID of the created Person node
        
    Raises:
        Exception: If creation fails (no record returned)
        
    Example:
        ```python
        person = Person(name="Vladimir Lenin", occupation="Author")
        async with connection_manager.session() as session:
            uuid = await create_person(session, person)
        ```
    """
    query = "CREATE (p:Person $properties) RETURN p.uuid as uuid"
    properties = serialize_model(person)
    result = await session.run(query, properties=properties)
    record = await result.single()
    if not record:
        raise Exception("Failed to create Person")
    return record["uuid"]


async def update_person(session: AsyncSession, person_uuid: str, person: Person) -> None:
    """
    Update Person node in Neo4j with new properties.
    
    Args:
        session: Neo4j session
        person_uuid: UUID of the Person to update
        person: Person object with updated properties
        
    Example:
        ```python
        person = Person(name="Vladimir Lenin", occupation="Revolutionary", summary="...")
        async with connection_manager.session() as session:
            await update_person(session, person_uuid, person)
        ```
    """
    query = """
    MATCH (p:Person {uuid: $person_uuid})
    SET p += $properties
    RETURN p
    """
    properties = serialize_model(person)
    # Remove uuid from properties as it shouldn't be updated
    properties.pop("uuid", None)
    result = await session.run(query, person_uuid=person_uuid, properties=properties)
    record = await result.single()
    if not record:
        raise Exception(f"Failed to update Person with uuid: {person_uuid}")


async def create_content(session: AsyncSession, content: Content) -> str:
    """
    Create Content node in Neo4j, return UUID.
    
    Args:
        session: Neo4j session
        content: Content object to create
        
    Returns:
        UUID of the created Content node
        
    Raises:
        Exception: If creation fails (no record returned)
        
    Example:
        ```python
        content = Content(title="Book Title", author="Author")
        async with connection_manager.session() as session:
            uuid = await create_content(session, content)
        ```
    """
    query = "CREATE (c:Content $properties) RETURN c.uuid as uuid"
    properties = serialize_model(content)
    result = await session.run(query, properties=properties)
    record = await result.single()
    if not record:
        raise Exception("Failed to create Content")
    return record["uuid"]


async def update_content(session: AsyncSession, content_uuid: str, content: Content) -> None:
    """
    Update Content node in Neo4j with new properties.
    
    Args:
        session: Neo4j session
        content_uuid: UUID of the Content to update
        content: Content object with updated properties
        
    Example:
        ```python
        content = Content(title="Book Title", summary="Updated summary", ...)
        async with connection_manager.session() as session:
            await update_content(session, content_uuid, content)
        ```
    """
    query = """
    MATCH (c:Content {uuid: $content_uuid})
    SET c += $properties
    RETURN c
    """
    properties = serialize_model(content)
    # Remove uuid from properties as it shouldn't be updated
    properties.pop("uuid", None)
    result = await session.run(query, content_uuid=content_uuid, properties=properties)
    record = await result.single()
    if not record:
        raise Exception(f"Failed to update Content with uuid: {content_uuid}")


async def create_authored_by_relationship(
    session: AsyncSession,
    author_uuid: str,
    content_uuid: str
) -> None:
    """
    Create AUTHORED_BY relationship between Person and Content.
    
    Args:
        session: Neo4j session
        author_uuid: UUID of the Person (author)
        content_uuid: UUID of the Content
        
    Example:
        ```python
        async with connection_manager.session() as session:
            await create_authored_by_relationship(
                session, author_uuid, content_uuid
            )
        ```
    """
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
    """
    Create Quote nodes and QUOTED_IN relationships, return list of UUIDs.
    
    Creates all quotes in a single transaction and links them to the content.
    Returns UUIDs ordered by creation date (newest first).
    
    Args:
        session: Neo4j session
        quotes: List of Quote objects to create
        content_uuid: UUID of the Content to link quotes to
        
    Returns:
        List of created quote UUIDs, ordered by created_at DESC
        
    Example:
        ```python
        quotes = [Quote(text="Quote 1"), Quote(text="Quote 2")]
        async with connection_manager.session() as session:
            uuids = await create_quotes_for_content(session, quotes, content_uuid)
        ```
    """
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
    """
    Find Content node by UUID.
    
    Args:
        session: Neo4j session
        content_uuid: UUID of the Content
        
    Returns:
        Content object if found, None otherwise
        
    Example:
        ```python
        async with connection_manager.session() as session:
            content = await find_content_by_uuid(session, content_uuid)
            if content:
                print(content.title)
        ```
    """
    query = "MATCH (c:Content {uuid: $uuid}) RETURN c"
    result = await session.run(query, uuid=content_uuid)
    record = await result.single()
    if record:
        properties = dict(record["c"])
        return deserialize_to_model(properties, Content)
    return None


async def find_quotes_by_content(session: AsyncSession, content_uuid: str) -> List[Quote]:
    """
    Find all quotes linked to a specific content.
    
    Returns quotes ordered by creation date (newest first).
    Embeddings are excluded for performance.
    
    Args:
        session: Neo4j session
        content_uuid: UUID of the Content
        
    Returns:
        List of Quote objects, ordered by created_at DESC
        
    Example:
        ```python
        async with connection_manager.session() as session:
            quotes = await find_quotes_by_content(session, content_uuid)
            for quote in quotes:
                print(quote.text)
        ```
    """
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
    """
    Find Quote node by UUID.
    
    Embedding is excluded for performance.
    
    Args:
        session: Neo4j session
        quote_uuid: UUID of the Quote
        
    Returns:
        Quote object if found, None otherwise
        
    Example:
        ```python
        async with connection_manager.session() as session:
            quote = await find_quote_by_uuid(session, quote_uuid)
        ```
    """
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
    """
    Find Concept node by UUID.
    
    Args:
        session: Neo4j session
        concept_uuid: UUID of the Concept
        
    Returns:
        Concept object if found, None otherwise
        
    Example:
        ```python
        async with connection_manager.session() as session:
            concept = await find_concept_by_uuid(session, concept_uuid)
        ```
    """
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


async def create_concept(session: AsyncSession, concept: Concept) -> str:
    """
    Create Concept node in Neo4j, return UUID.
    
    Args:
        session: Neo4j session
        concept: Concept object to create
        
    Returns:
        UUID of the created Concept node
        
    Raises:
        Exception: If creation fails (no record returned)
        
    Example:
        ```python
        concept = Concept(
            title="Concept Title",
            concept="Concept description",
            analysis="Personal analysis"
        )
        async with connection_manager.session() as session:
            uuid = await create_concept(session, concept)
        ```
    """
    query = "CREATE (c:Concept $properties) RETURN c.uuid as uuid"
    properties = serialize_model(concept)
    result = await session.run(query, properties=properties)
    record = await result.single()
    if not record:
        raise Exception("Failed to create Concept")
    return record["uuid"]


async def create_concept_relation(
    session: AsyncSession,
    source_uuid: str,
    target_uuid: str,
    relation_type: str
) -> None:
    """
    Create bidirectional concept relation using RELATION_MAP.
    
    Args:
        session: Neo4j session
        source_uuid: UUID of source concept
        target_uuid: UUID of target concept
        relation_type: Forward relation type (e.g., "GENERALIZES")
    """
    # Import RELATION_MAP to get reverse relation type
    from minerva_backend.obsidian.obsidian_service import RELATION_MAP
    
    if relation_type not in RELATION_MAP:
        raise ValueError(f"Invalid relation type: {relation_type}")
    
    forward_type, reverse_type = RELATION_MAP[relation_type]
    
    # Create forward relation
    forward_query = f"""
    MATCH (source:Concept {{uuid: $source_uuid}})
    MATCH (target:Concept {{uuid: $target_uuid}})
    MERGE (source)-[r:{forward_type}]->(target)
    RETURN r
    """
    await session.run(forward_query, source_uuid=source_uuid, target_uuid=target_uuid)
    
    # Create reverse relation (if different from forward)
    if forward_type != reverse_type:
        reverse_query = f"""
        MATCH (source:Concept {{uuid: $source_uuid}})
        MATCH (target:Concept {{uuid: $target_uuid}})
        MERGE (target)-[r:{reverse_type}]->(source)
        RETURN r
        """
        await session.run(reverse_query, source_uuid=source_uuid, target_uuid=target_uuid)
    elif forward_type == reverse_type:
        # For symmetric relations, only create one direction (already done above)
        pass


async def create_supports_relation(
    session: AsyncSession,
    quote_uuid: str,
    concept_uuid: str,
    reasoning: str | None = None,
    confidence: float | None = None
) -> None:
    """
    Create (Quote)-[:SUPPORTS]->(Concept) relationship.
    
    Args:
        session: Neo4j session
        quote_uuid: UUID of the quote
        concept_uuid: UUID of the concept
        reasoning: Optional reasoning for the support
        confidence: Optional confidence score (0.0-1.0)
    """
    # Build properties dict for the relationship
    rel_props = {}
    if reasoning:
        rel_props["reasoning"] = reasoning
    if confidence is not None:
        rel_props["confidence"] = confidence
    
    if rel_props:
        props_str = " {" + ", ".join(f"{k}: ${k}" for k in rel_props.keys()) + "}"
        query = f"""
        MATCH (q:Quote {{uuid: $quote_uuid}})
        MATCH (c:Concept {{uuid: $concept_uuid}})
        MERGE (q)-[r:SUPPORTS{props_str}]->(c)
        RETURN r
        """
        params = {"quote_uuid": quote_uuid, "concept_uuid": concept_uuid, **rel_props}
    else:
        query = """
        MATCH (q:Quote {uuid: $quote_uuid})
        MATCH (c:Concept {uuid: $concept_uuid})
        MERGE (q)-[r:SUPPORTS]->(c)
        RETURN r
        """
        params = {"quote_uuid": quote_uuid, "concept_uuid": concept_uuid}
    
    await session.run(query, **params)


async def update_content_processed_date(
    session: AsyncSession,
    content_uuid: str,
    processed_date: datetime | None = None
) -> None:
    """
    Set processed_date on Content node.
    
    Args:
        session: Neo4j session
        content_uuid: UUID of the content
        processed_date: Timestamp to set (defaults to current time)
    """
    if processed_date is None:
        processed_date = datetime.now()
    
    query = """
    MATCH (c:Content {uuid: $content_uuid})
    SET c.processed_date = $processed_date
    RETURN c
    """
    await session.run(
        query,
        content_uuid=content_uuid,
        processed_date=processed_date.isoformat()
    )


async def get_unprocessed_quotes_by_supports(
    session: AsyncSession,
    content_uuid: str
) -> List[Quote]:
    """
    Get quotes for content that don't have any SUPPORTS relations to concepts.
    
    Args:
        session: Neo4j session
        content_uuid: UUID of the content
    
    Returns:
        List of unprocessed Quote objects (quotes without SUPPORTS relations)
    """
    query = """
    MATCH (q:Quote)-[:QUOTED_IN]->(c:Content {uuid: $content_uuid})
    WHERE NOT EXISTS {
        (q)-[:SUPPORTS]->(:Concept)
    }
    RETURN q
    ORDER BY q.created_at DESC
    """
    result = await session.run(query, content_uuid=content_uuid)
    quotes = []
    async for record in result:
        properties = dict(record["q"])
        properties.pop("embedding", None)
        quotes.append(deserialize_to_model(properties, Quote))
    return quotes


def get_neo4j_connection_manager() -> Neo4jConnectionManager:
    """
    Factory function to create configured connection manager.
    
    Returns:
        Neo4jConnectionManager: Configured connection manager instance
        
    Note:
        Connection parameters are currently hardcoded. Modify this function
        to change connection settings or read from environment variables.
        
    Example:
        ```python
        connection_manager = get_neo4j_connection_manager()
        async with connection_manager.session() as session:
            # Use session
            pass
        ```
    """
    return Neo4jConnectionManager(
        uri="bolt://localhost:7687",
        user="neo4j",
        password="Alxe342!"
    )
