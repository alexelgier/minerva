from .base import BaseRepository
from ..models.entities import Content, Consumable, Place
from ..models.enums import EntityType


class PlaceRepository(BaseRepository[Content]):
    """Repository for Place entities with specialized place operations."""

    @property
    def entity_label(self) -> str:
        return EntityType.PLACE.value

    @property
    def entity_class(self) -> type[Place]:
        return Place
