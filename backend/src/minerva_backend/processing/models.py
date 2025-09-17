from typing import Set, Any

from pydantic import BaseModel

from minerva_backend.graph.models.documents import Span
from minerva_backend.graph.models.entities import Entity
from minerva_backend.graph.models.relations import Relation
from minerva_backend.prompt.extract_relationships import RelationshipContext


class EntitySpanMapping(BaseModel):
    entity: Entity
    spans: Set[Span]

    def __init__(self, entity: Entity, spans: Set[Span]) -> None:
        self.entity = entity
        self.spans = spans


class RelationSpanContextMapping(BaseModel):
    relation: Relation
    spans: Set[Span]
    context: Set[RelationshipContext]

    def __init__(self, relation: Relation, spans: Set[Span], context: Set[RelationshipContext]) -> None:
        self.relation = relation
        self.spans = spans
        self.context = context
