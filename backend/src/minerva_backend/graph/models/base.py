from __future__ import annotations

from abc import ABC
from datetime import datetime, timezone
from typing import Literal
from uuid import uuid4

from pydantic import BaseModel, Field

from .enums import DocumentType, EntityType, PartitionType


# ----------------------------
# Base Entity
# ----------------------------

class Node(BaseModel, ABC):
    """Entidad abstracta. Todos los nodos tienen al menos estos campos."""
    partition: PartitionType = Field(..., description='partición del grafo')
    uuid: str = Field(default_factory=lambda: str(uuid4()))
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Config:
        extra = "allow"  # allow schema evolution (new fields in future)
        use_enum_values = True


class Entity(Node, ABC):
    name: str = Field(..., description='nombre de la entidad')
    type: EntityType = Field(..., description="Tipo de entidad (Persona, Evento, etc)")
    summary_short: str = Field(..., description="Resumen de la entidad. Máximo 30 palabras")
    summary: str = Field(..., description="Resumen de la entidad. Máximo 300 palabras")
    partition: Literal[PartitionType.DOMAIN] = Field(PartitionType.DOMAIN.value,
                                                     description="Tipo de partición (siempre DOMAIN)")
    name_embedding: list[float] | None = Field(default=None, description='embedding del nombre')


class Document(Node, ABC):
    type: DocumentType = Field(..., description="Tipo de documento")
    text: str = Field(..., description="El texto original del documento")
    partition: Literal[PartitionType.LEXICAL] = Field(PartitionType.LEXICAL.value,
                                                      description="Tipo de partición (siempre LEXICAL)")


class Chunk(Node, ABC):
    text: str = Field(..., description="El texto del fragmento")
    partition: Literal[PartitionType.LEXICAL] = Field(PartitionType.LEXICAL.value,
                                                      description="Tipo de partición (siempre LEXICAL)")
    embedding: list[float] | None = Field(default=None, description='embedding del fragmento')
