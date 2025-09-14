from __future__ import annotations

from typing import Literal

from pydantic import Field

from .base import Edge
from .enums import PartitionType, RelationshipType


class Relation(Edge):
    """Generic relationship between two entities."""
    source: str = Field(..., description="UUID of the source entity")
    target: str = Field(..., description="UUID of the target entity")
    type: RelationshipType = Field(..., description="Type of the relationship")
    context: str = Field(..., description="Context or reason for the relationship")
    partition: Literal[PartitionType.DOMAIN] = Field(PartitionType.DOMAIN.value,
                                                     description="Partition type (always DOMAIN for entity relations)")


class Mentions(Edge):
    """A JournalEntry mentions an Entity."""
    source: str = Field(..., description="UUID of the source JournalEntry")
    target: str = Field(..., description="UUID of the target Entity")
    context: str | None = Field(default=None, description="The textual context of the mention")
    partition: Literal[PartitionType.LEXICAL] = Field(PartitionType.LEXICAL.value,
                                                       description="Partition type (always LEXICAL for mentions)")


class Contains(Edge):
    """A JournalEntry contains a Chunk."""
    source: str = Field(..., description="UUID of the source JournalEntry")
    target: str = Field(..., description="UUID of the target Chunk")
    partition: Literal[PartitionType.LEXICAL] = Field(PartitionType.LEXICAL.value,
                                                       description="Partition type (always LEXICAL for contains)")
