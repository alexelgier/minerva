from datetime import date as date_type
from datetime import datetime
from typing import Set, Any, Literal, Dict, List

from pydantic import BaseModel, Field

from minerva_backend.graph.models.documents import Span
from minerva_backend.graph.models.entities import Entity
from minerva_backend.graph.models.relations import Relation
from minerva_backend.prompt.extract_relationships import RelationshipContext


class EntitySpanMapping(BaseModel):
    entity: Entity
    spans: Set[Span]

    def __init__(self, entity: Entity, spans: Set[Span], **kwargs) -> None:
        super().__init__(entity=entity, spans=spans, **kwargs)


class RelationSpanContextMapping(BaseModel):
    relation: Relation
    spans: Set[Span]
    context: Set[RelationshipContext] | None = None

    def __init__(self, relation: Relation, spans: Set[Span], context: Set[RelationshipContext] = None,
                 **kwargs) -> None:
        super().__init__(relation=relation, spans=spans, context=context, **kwargs)

    def __hash__(self):
        return hash(self.relation.uuid)


class CurationTask(BaseModel):
    """Model for individual curation tasks."""
    id: str = Field(..., description="Task identifier")
    journal_id: str = Field(..., description="Associated journal entry ID")
    type: Literal["entity", "relationship"] = Field(..., description="Type of curation task")
    status: Literal["pending", "in_progress", "completed"] = Field(..., description="Task status")
    created_at: datetime = Field(..., description="Task creation timestamp")
    data: Dict[str, Any] = Field(..., description="Task data to be curated")


class JournalEntryCuration(BaseModel):
    journal_id: str = Field(..., description="Associated journal entry ID")
    date: date_type = Field(..., description="Fecha de la entrada del diario")
    entry_text: str | None = Field(default=None, description="El texto principal de la entrada del diario")
    tasks: List[CurationTask] = Field(default_factory=list, description="List of pending curation tasks")


class CurationEntityStats(BaseModel):
    """Entity curation statistics."""
    total_extracted: int = Field(default=0, description="Total entities extracted")
    accepted: int = Field(default=0, description="Total entities accepted")
    rejected: int = Field(default=0, description="Total entities rejected")
    pending: int = Field(default=0, description="Total entities pending")
    acceptance_rate: float = Field(default=0.0, description="Acceptance rate (accepted / (accepted + rejected))")


class CurationRelationshipStats(BaseModel):
    """Relationship curation statistics."""
    total_extracted: int = Field(default=0, description="Total relationships extracted")
    accepted: int = Field(default=0, description="Total relationships accepted")
    rejected: int = Field(default=0, description="Total relationships rejected")
    pending: int = Field(default=0, description="Total relationships pending")
    acceptance_rate: float = Field(default=0.0, description="Acceptance rate (accepted / (accepted + rejected))")


class CurationStats(BaseModel):
    """Curation statistics model."""
    total_journals: int = Field(default=0, description="Total journals in curation")
    pending_entities: int = Field(default=0, description="Journals pending entity curation")
    pending_relationships: int = Field(default=0, description="Journals pending relationship curation")
    completed: int = Field(default=0, description="Completed journals")
    entity_stats: CurationEntityStats = Field(default_factory=CurationEntityStats)
    relationship_stats: CurationRelationshipStats = Field(default_factory=CurationRelationshipStats)
