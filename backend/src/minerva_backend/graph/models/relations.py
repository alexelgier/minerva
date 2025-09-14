from __future__ import annotations

from typing import Literal

from pydantic import Field

from .base import Edge
from .enums import PartitionType, RelationshipType


class Relation(Edge):
    """Generic relationship between two entities."""
    source: str = Field(..., description="UUID of the source entity")
    target: str = Field(..., description="UUID of the target entity")
    type: Literal[RelationshipType.RELATED_TO] = Field(RelationshipType.RELATED_TO.value,
                                                       description="Type of the relationship (always RELATED_TO for entity relations)")
    summary_short: str = Field(..., description="Resumen de la relación. Máximo 30 palabras")
    summary: str = Field(..., description="Resumen de la relación. Máximo 300 palabras")
    partition: Literal[PartitionType.DOMAIN] = Field(PartitionType.DOMAIN.value,
                                                     description="Partition type (always DOMAIN for entity relations)")


class Mentions(Edge):
    """A JournalEntry mentions an Entity."""
    source: str = Field(..., description="UUID of the source JournalEntry")
    target: str = Field(..., description="UUID of the target Entity")
    partition: Literal[PartitionType.LEXICAL] = Field(PartitionType.LEXICAL.value,
                                                      description="Partition type (always LEXICAL for mentions)")


class Contains(Edge):
    """A JournalEntry/Chunk contains a Chunk."""
    source: str = Field(..., description="UUID of the source JournalEntry or Chunk")
    target: str = Field(..., description="UUID of the target Chunk")
    partition: Literal[PartitionType.LEXICAL] = Field(PartitionType.LEXICAL.value,
                                                      description="Partition type (always LEXICAL for contains)")
