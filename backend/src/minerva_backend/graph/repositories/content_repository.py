"""
Resource Repository for Minerva
Handles all Resource entity database operations.
"""

from .base import BaseRepository
from ..models.entities import Content
from ..models.enums import EntityType


class ContentRepository(BaseRepository[Content]):
    """Repository for Content entities with specialized content operations."""

    @property
    def entity_label(self) -> str:
        return EntityType.CONTENT.value

    @property
    def entity_class(self) -> type[Content]:
        return Content
