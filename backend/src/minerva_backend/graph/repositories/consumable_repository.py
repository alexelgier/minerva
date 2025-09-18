from .base import BaseRepository
from ..models.entities import Content, Consumable
from ..models.enums import EntityType


class ConsumableRepository(BaseRepository[Content]):
    """Repository for Consumable entities with specialized consumable operations."""

    @property
    def entity_label(self) -> str:
        return EntityType.CONSUMABLE.value

    @property
    def entity_class(self) -> type[Consumable]:
        return Consumable
