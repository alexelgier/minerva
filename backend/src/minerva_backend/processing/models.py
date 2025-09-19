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
