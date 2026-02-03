from minerva_models import Consumable, Content, Place
from ..models.enums import EntityType
from .base import BaseRepository


class PlaceRepository(BaseRepository[Place]):
    """Repository for Place entities with specialized place operations."""

    @property
    def entity_label(self) -> str:
        return EntityType.PLACE.value

    @property
    def entity_class(self) -> type[Place]:
        return Place
