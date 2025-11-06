"""
Quote Repository for Minerva
Handles all Quote document database operations.
"""

import logging

from minerva_models import Quote
from minerva_backend.graph.db import Neo4jConnection
from minerva_backend.processing.llm_service import LLMService

logger = logging.getLogger(__name__)


class QuoteRepository:
    """Repository for Quote documents with specialized quote operations."""

    def __init__(self, connection: Neo4jConnection, llm_service: LLMService):
        """Initialize repository with database connection and LLM service."""
        self.connection = connection
        self.llm_service = llm_service

    def _node_to_properties(self, node: Quote) -> dict:
        """Convert Quote node to Neo4j properties."""
        properties = node.model_dump()
        return properties

    def _properties_to_node(self, properties: dict) -> Quote:
        """Convert Neo4j properties back to Quote node."""
        return Quote(**properties)

    async def create(self, quote: Quote) -> str:
        """
        Create a new Quote in the database with embedding generation.
        
        Args:
            quote: Quote object to create
            
        Returns:
            str: UUID of created quote
        """
        # Generate embedding if not already present
        if quote.embedding is None:
            quote.embedding = await self._generate_embedding(quote.text)
        
        properties = self._node_to_properties(quote)
        
        query = """
        CREATE (q:Quote $properties)
        RETURN q.uuid as uuid
        """
        
        async with self.connection.session_async() as session:
            try:
                result = await session.run(query, properties=properties)
                record = await result.single()
                
                if not record:
                    raise Exception("Failed to create Quote")
                
                quote_uuid = record["uuid"]
                logger.info(f"Created Quote: {quote.text[:50]}... (UUID: {quote_uuid})")
                return quote_uuid
                
            except Exception as e:
                logger.error(f"Error creating Quote: {e}")
                raise

    async def create_quotes_for_content(self, quotes: list[Quote], content_uuid: str) -> list[str]:
        """
        Create multiple quotes and link them to a content entity in a single query.
        
        Args:
            quotes: List of Quote objects to create
            content_uuid: UUID of the content entity to link quotes to
            
        Returns:
            List of UUIDs of created quotes
        """
        if not quotes:
            return []
        
        # Generate embeddings for quotes that don't have them
        for quote in quotes:
            if quote.embedding is None:
                quote.embedding = await self._generate_embedding(quote.text)
        
        # Prepare quote properties for batch creation
        quote_properties = [self._node_to_properties(quote) for quote in quotes]
        
        query = """
        MATCH (c:Content {uuid: $content_uuid})
        UNWIND $quotes AS quote_props
        CREATE (q:Quote)
        SET q = quote_props
        CREATE (q)-[:QUOTED_IN]->(c)
        RETURN q.uuid as uuid
        ORDER BY q.created_at DESC
        """
        
        async with self.connection.session_async() as session:
            try:
                result = await session.run(
                    query, 
                    content_uuid=content_uuid, 
                    quotes=quote_properties
                )
                
                created_quote_uuids = []
                async for record in result:
                    created_quote_uuids.append(record["uuid"])
                
                logger.info(f"Created {len(created_quote_uuids)} quotes for content {content_uuid}")
                return created_quote_uuids
                
            except Exception as e:
                logger.error(f"Error creating quotes for content {content_uuid}: {e}")
                raise


    async def find_quotes_by_content(self, content_uuid: str) -> list[Quote]:
        """
        Find all quotes linked to a specific content.
        
        Args:
            content_uuid: UUID of the content
            
        Returns:
            List of Quote objects
        """
        query = """
        MATCH (q:Quote)-[:QUOTED_IN]->(c:Content {uuid: $content_uuid})
        RETURN q
        ORDER BY q.created_at DESC
        """
        
        async with self.connection.session_async() as session:
            result = await session.run(query, content_uuid=content_uuid)
            quotes = []
            
            async for record in result:
                properties = dict(record["q"])
                quote = self._properties_to_node(properties)
                quotes.append(quote)
                
            return quotes

    async def _generate_embedding(self, text: str) -> list[float]:
        """
        Generate embedding for quote text using LLM service.
        
        Args:
            text: Text to generate embedding for
            
        Returns:
            list[float]: Embedding vector
        """
        try:
            embedding = await self.llm_service.create_embedding(text)
            logger.debug(f"Generated embedding for quote text: {text[:50]}...")
            return embedding
        except Exception as e:
            logger.error(f"Error generating embedding for quote: {e}")
            raise

    async def search_similar_quotes(
        self, 
        query_text: str, 
        limit: int = 10, 
        threshold: float = 0.7
    ) -> list[Quote]:
        """
        Search for quotes similar to the query text using vector similarity.
        
        Args:
            query_text: Text to search for similar quotes
            limit: Maximum number of results to return
            threshold: Minimum similarity threshold (0.0-1.0)
            
        Returns:
            List of similar Quote objects
        """
        try:
            # Generate embedding for query text
            query_embedding = await self._generate_embedding(query_text)
            
            # Use the connection's vector search method
            results = await self.connection.vector_search(
                label="Quote",
                query_embedding=query_embedding,
                limit=limit,
                threshold=threshold
            )
            
            # Convert results to Quote objects
            quotes = []
            for result in results:
                node = result["node"]
                properties = dict(node)
                quote = self._properties_to_node(properties)
                quotes.append(quote)
                
            logger.info(f"Found {len(quotes)} similar quotes for query: {query_text[:50]}...")
            return quotes
            
        except Exception as e:
            logger.error(f"Error searching similar quotes: {e}")
            raise

    async def update_quote_embedding(self, quote_uuid: str) -> bool:
        """
        Update the embedding for a specific quote.
        
        Args:
            quote_uuid: UUID of the quote to update
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # First, get the quote text
            query = """
            MATCH (q:Quote {uuid: $quote_uuid})
            RETURN q.text as text
            """
            
            async with self.connection.session_async() as session:
                result = await session.run(query, quote_uuid=quote_uuid)
                record = await result.single()
                
                if not record:
                    logger.warning(f"Quote with UUID {quote_uuid} not found")
                    return False
                
                text = record["text"]
                
                # Generate new embedding
                embedding = await self._generate_embedding(text)
                
                # Update the quote with new embedding
                update_query = """
                MATCH (q:Quote {uuid: $quote_uuid})
                SET q.embedding = $embedding
                RETURN q.uuid as uuid
                """
                
                update_result = await session.run(
                    update_query, 
                    quote_uuid=quote_uuid, 
                    embedding=embedding
                )
                
                if update_result.single():
                    logger.info(f"Updated embedding for quote {quote_uuid}")
                    return True
                else:
                    logger.error(f"Failed to update embedding for quote {quote_uuid}")
                    return False
                    
        except Exception as e:
            logger.error(f"Error updating quote embedding: {e}")
            return False

    async def create_supports_relationship(
        self, 
        quote_uuid: str, 
        concept_uuid: str, 
        reasoning: str, 
        confidence: float
    ) -> None:
        """Create (Quote)-[:SUPPORTS]->(Concept) relationship"""
        query = """
        MATCH (q:Quote {uuid: $quote_uuid})
        MATCH (c:Concept {uuid: $concept_uuid})
        CREATE (q)-[:SUPPORTS {reasoning: $reasoning, confidence: $confidence}]->(c)
        """
        
        async with self.connection.session_async() as session:
            try:
                await session.run(
                    query,
                    quote_uuid=quote_uuid,
                    concept_uuid=concept_uuid,
                    reasoning=reasoning,
                    confidence=confidence
                )
                logger.info(f"Created SUPPORTS relationship: {quote_uuid} -> {concept_uuid}")
            except Exception as e:
                logger.error(f"Error creating SUPPORTS relationship: {e}")
                raise