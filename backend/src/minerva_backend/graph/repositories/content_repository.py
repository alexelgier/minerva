"""
Resource Repository for Minerva
Handles all Resource entity database operations.
"""

from minerva_models import Content
from ..models.enums import EntityType
from .base import BaseRepository


class ContentRepository(BaseRepository[Content]):
    """Repository for Content entities with specialized content operations."""

    @property
    def entity_label(self) -> str:
        return EntityType.CONTENT.value

    @property
    def entity_class(self) -> type[Content]:
        return Content

    async def create_authored_by_relationship(self, author_uuid: str, content_uuid: str) -> None:
        """
        Create an AUTHORED_BY relationship between a Person and Content.
        
        Args:
            author_uuid: UUID of the author Person
            content_uuid: UUID of the Content
        """
        query = """
        MATCH (p:Person {uuid: $author_uuid})
        MATCH (c:Content {uuid: $content_uuid})
        CREATE (p)-[:AUTHORED_BY]->(c)
        """
        
        async with self.connection.session_async() as session:
            await session.run(query, author_uuid=author_uuid, content_uuid=content_uuid)
            print(f"[ContentRepository] Created AUTHORED_BY relationship: {author_uuid} -> {content_uuid}")