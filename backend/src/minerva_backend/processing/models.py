from dataclasses import dataclass
from datetime import date as date_type
from datetime import datetime
from typing import Any, Dict, List, Literal, Union

from pydantic import BaseModel, Field

from minerva_models import ConceptRelation, FeelingConcept, FeelingEmotion, Relation, Span
from minerva_backend.prompt.extract_relationships import RelationshipContext


@dataclass
class EntityMapping:
    """Simple container for entity and spans. No complex typing needed."""

    entity: Any  # Any entity type (Concept, Person, Feeling, etc.)
    spans: List[Any]  # Any span type


@dataclass
class CuratableMapping:
    """Unified container for curatable items (relations and feelings) with spans and optional context."""

    kind: Literal["relation", "concept_relation", "feeling_emotion", "feeling_concept"]
    data: Union[Relation, ConceptRelation, FeelingEmotion, FeelingConcept]
    spans: List[Any]  # Any span type
    context: List[Any] | None = None  # Any context type (only for relation kinds)

    def __hash__(self):
        return hash(self.data.uuid)


class CurationTask(BaseModel):
    """Model for individual curation tasks."""

    id: str = Field(..., description="Task identifier")
    journal_id: str = Field(..., description="Associated journal entry ID")
    type: Literal["entity", "relationship"] = Field(
        ..., description="Type of curation task"
    )
    status: Literal["pending", "in_progress", "completed"] = Field(
        ..., description="Task status"
    )
    created_at: datetime = Field(..., description="Task creation timestamp")
    data: Dict[str, Any] = Field(..., description="Task data to be curated")


class JournalEntryCuration(BaseModel):
    journal_id: str = Field(..., description="Associated journal entry ID")
    date: date_type = Field(..., description="Fecha de la entrada del diario")
    entry_text: str | None = Field(
        default=None, description="El texto principal de la entrada del diario"
    )
    phase: Literal["entities", "relationships"] = Field(..., description="Phase")
    tasks: Dict[str, CurationTask] = Field(
        default_factory=dict, description="List of pending curation tasks"
    )


class CurationEntityStats(BaseModel):
    """Entity curation statistics."""

    total_extracted: int = Field(default=0, description="Total entities extracted")
    accepted: int = Field(default=0, description="Total entities accepted")
    rejected: int = Field(default=0, description="Total entities rejected")
    pending: int = Field(default=0, description="Total entities pending")
    acceptance_rate: float = Field(
        default=0.0, description="Acceptance rate (accepted / (accepted + rejected))"
    )


class CurationRelationshipStats(BaseModel):
    """Relationship curation statistics."""

    total_extracted: int = Field(default=0, description="Total relationships extracted")
    accepted: int = Field(default=0, description="Total relationships accepted")
    rejected: int = Field(default=0, description="Total relationships rejected")
    pending: int = Field(default=0, description="Total relationships pending")
    acceptance_rate: float = Field(
        default=0.0, description="Acceptance rate (accepted / (accepted + rejected))"
    )


class CurationStats(BaseModel):
    """Curation statistics model."""

    total_journals: int = Field(default=0, description="Total journals in curation")
    pending_entities: int = Field(
        default=0, description="Journals pending entity curation"
    )
    pending_relationships: int = Field(
        default=0, description="Journals pending relationship curation"
    )
    completed: int = Field(default=0, description="Completed journals")
    entity_stats: CurationEntityStats = Field(default_factory=CurationEntityStats)
    relationship_stats: CurationRelationshipStats = Field(
        default_factory=CurationRelationshipStats
    )
