from __future__ import annotations

from enum import Enum
from typing import Annotated, Literal

from pydantic import Field

from .base import Node, PartitionType


class RelationshipType(str, Enum):
    RELATED_TO = "RELATED_TO"


class ConceptRelationType(str, Enum):
    GENERALIZES = "GENERALIZES"
    SPECIFIC_OF = "SPECIFIC_OF"
    PART_OF = "PART_OF"
    HAS_PART = "HAS_PART"
    SUPPORTS = "SUPPORTS"
    SUPPORTED_BY = "SUPPORTED_BY"
    OPPOSES = "OPPOSES"
    SIMILAR_TO = "SIMILAR_TO"
    RELATES_TO = "RELATES_TO"


class Relation(Node):
    """Generic relationship between two entities."""

    source: str = Field(..., min_length=1, description="UUID of the source entity")
    target: str = Field(..., min_length=1, description="UUID of the target entity")
    type: RelationshipType | ConceptRelationType = RelationshipType.RELATED_TO
    proposed_types: (
        Annotated[
            list[str],
            Field(min_length=1, description="Propuestas de tipo para la relación"),
        ]
        | None
    ) = Field(default=None)
    summary_short: str = Field(
        ..., description="Resumen de la relación. Máximo 30 palabras"
    )
    summary: str = Field(..., description="Resumen de la relación. Máximo 100 palabras")
    partition: Literal[PartitionType.DOMAIN] = PartitionType.DOMAIN
    embedding: list[float] | None = Field(
        default=None, description="Embedding of the summary field"
    )


class ConceptRelation(Relation):
    """Specialized relationship between two concepts with typed relations."""

    type: ConceptRelationType = Field(..., description="Type of concept relation")
    proposed_types: (
        Annotated[
            list[str],
            Field(
                min_length=1,
                description="Proposed types for concept relation (optional, uses type field instead)",
            ),
        ]
        | None
    ) = Field(default=None)
    # Inherits source, target, summary_short, summary, partition, embedding from Relation

