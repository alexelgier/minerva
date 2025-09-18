from __future__ import annotations

from abc import ABC
from datetime import datetime, timezone
from typing import Literal
from uuid import uuid4

from pydantic import BaseModel, Field

from .enums import LexicalType, PartitionType


# ----------------------------
# Base Entity
# ----------------------------

class Node(BaseModel, ABC):
    """Entidad abstracta. Todos los nodos tienen al menos estos campos."""
    partition: PartitionType = Field(..., description='partición del grafo')
    uuid: str = Field(default_factory=lambda: str(uuid4()))
    created_at: datetime = Field(default_factory=lambda: datetime.now())

    def __hash__(self):
        return hash(self.uuid)

    def __eq__(self, other):
        if isinstance(other, Node):
            return self.uuid == other.uuid
        return False

    class Config:
        # extra = "allow"  # allow schema evolution (new fields in future)
        use_enum_values = True


class Edge(BaseModel, ABC):
    """Relación abstracta. Todas las aristas tienen al menos estos campos."""
    partition: PartitionType = Field(..., description='partición del grafo')
    uuid: str = Field(default_factory=lambda: str(uuid4()))
    created_at: datetime = Field(default_factory=lambda: datetime.now())

    def __hash__(self):
        return hash(self.uuid)

    def __eq__(self, other):
        if isinstance(other, Node):
            return self.uuid == other.uuid
        return False

    class Config:
        # extra = "allow"  # allow schema evolution (new fields in future)
        use_enum_values = True


class Document(Node, ABC):
    type: LexicalType = Field(..., description="Tipo de documento")
    text: str = Field(..., description="El texto original del documento")
    partition: Literal[PartitionType.LEXICAL] = PartitionType.LEXICAL.value

