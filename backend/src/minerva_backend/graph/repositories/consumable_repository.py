from minerva_models import Consumable, Content
from ..models.enums import EntityType
from .base import BaseRepository


class ConsumableRepository(BaseRepository[Consumable]):
    """Repository for Consumable entities with specialized consumable operations."""

    @property
    def entity_label(self) -> str:
        return EntityType.CONSUMABLE.value

    @property
    def entity_class(self) -> type[Consumable]:
        return Consumable
