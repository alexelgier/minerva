from __future__ import annotations

from abc import ABC
from datetime import datetime
from enum import Enum
from typing import Literal
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field, field_validator

# ----------------------------
# Base Enums
# ----------------------------


class PartitionType(str, Enum):
    DOMAIN = "DOMAIN"
    LEXICAL = "LEXICAL"
    TEMPORAL = "TEMPORAL"


class LexicalType(str, Enum):
    JOURNAL_ENTRY = "JournalEntry"
    SPAN = "Span"
    CHUNK = "Chunk"
    QUOTE = "Quote"


# ----------------------------
# Base Entity
# ----------------------------


class Node(BaseModel, ABC):
    """Entidad abstracta. Todos los nodos tienen al menos estos campos."""

    partition: PartitionType = Field(..., description="partición del grafo")
    uuid: str = Field(default_factory=lambda: str(uuid4()))
    created_at: datetime = Field(default_factory=lambda: datetime.now())

    @field_validator("created_at", mode="before")
    @classmethod
    def validate_created_at(cls, v):
        """Convert Neo4j DateTime objects to Python datetime objects."""
        if hasattr(v, 'to_native'):  # Neo4j DateTime/Date objects
            return v.to_native()
        return v

    def __hash__(self):
        return hash(self.uuid)

    def __eq__(self, other):
        if isinstance(other, Node):
            return self.uuid == other.uuid
        return False

    model_config = ConfigDict(
        # extra = "allow"  # allow schema evolution (new fields in future)
        use_enum_values=True
    )


class Document(Node, ABC):
    type: LexicalType = Field(..., description="Tipo de documento")
    text: str = Field(..., description="El texto original del documento")
    partition: Literal[PartitionType.LEXICAL] = PartitionType.LEXICAL

