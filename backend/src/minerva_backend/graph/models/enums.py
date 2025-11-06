"""Re-export enums and entity type mapping from minerva-models."""
from minerva_models import (
    Concept,
    Consumable,
    Content,
    Emotion,
    EntityType,
    Event,
    FeelingConcept,
    FeelingEmotion,
    Person,
    Place,
    Project,
    Relation,
    RelationshipType,
    ENTITY_TYPE_MAP as MINERVA_ENTITY_TYPE_MAP,
)

# Use the ENTITY_TYPE_MAP from minerva_models
ENTITY_TYPE_MAP = MINERVA_ENTITY_TYPE_MAP

RELATIONSHIP_TYPE_MAP = {RelationshipType.RELATED_TO: Relation}
