from enum import Enum

from minerva_backend.graph.models.entities import (
    Person, Feeling, Emotion, Event, Project, Concept, Content, Consumable, Place, EntityType
)
from minerva_backend.graph.models.relations import Relation, RelationshipType


# ----------------------------
# Core entity + relationship + partition types
# ----------------------------

ENTITY_TYPE_MAP = {
    EntityType.PERSON: Person,
    EntityType.FEELING: Feeling,
    EntityType.EMOTION: Emotion,
    EntityType.EVENT: Event,
    EntityType.PROJECT: Project,
    EntityType.CONCEPT: Concept,
    EntityType.CONTENT: Content,
    EntityType.CONSUMABLE: Consumable,
    EntityType.PLACE: Place
}


RELATIONSHIP_TYPE_MAP = {
    RelationshipType.RELATED_TO: Relation
}


# ----------------------------
# Enums
# ----------------------------

