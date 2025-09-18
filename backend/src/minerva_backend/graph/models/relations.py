from __future__ import annotations

from typing import Literal, Optional, List

from pydantic import Field, conlist, BaseModel

from .base import Edge, PartitionType
from .enums import RelationshipType


class Relation(Edge):
    """Generic relationship between two entities."""
    source: str = Field(..., description="UUID of the source entity")
    target: str = Field(..., description="UUID of the target entity")
    type: Literal[RelationshipType.RELATED_TO] = RelationshipType.RELATED_TO.value
    proposed_types: conlist(str, min_length=1) = Field(..., description="Propuestas de tipo para la relación")
    summary_short: str = Field(..., description="Resumen de la relación. Máximo 30 palabras")
    summary: str = Field(..., description="Resumen de la relación. Máximo 100 palabras")
    partition: Literal[PartitionType.DOMAIN] = PartitionType.DOMAIN.value
