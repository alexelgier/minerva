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

class EmotionType(str, Enum):
    ANGER = "anger"
    ANNOYANCE = "annoyance"
    CONTEMPT = "contempt"
    DISGUST = "disgust"
    IRRITATION = "irritation"
    ANXIETY = "anxiety"
    EMBARRASSMENT = "embarrassment"
    FEAR = "fear"
    HELPLESSNESS = "helplessness"
    POWERLESSNESS = "powerlessness"
    WORRY = "worry"
    DOUBT = "doubt"
    ENVY = "envy"
    FRUSTRATION = "frustration"
    GUILT = "guilt"
    SHAME = "shame"
    CONFUSION = "confusion"
    BOREDOM = "boredom"
    DESPAIR = "despair"
    DISAPPOINTMENT = "disappointment"
    HURT = "hurt"
    SADNESS = "sadness"
    LONELINESS = "loneliness"
    STRESS = "stress"
    TENSION = "tension"
    AMUSEMENT = "amusement"
    DELIGHT = "delight"
    ELATION = "elation"
    EXCITEMENT = "excitement"
    HAPPINESS = "happiness"
    JOY = "joy"
    PLEASURE = "pleasure"
    SATISFACTION = "satisfaction"
    AFFECTION = "affection"
    EMPATHY = "empathy"
    LOVE = "love"
    PRIDE = "pride"
    GRATITUDE = "gratitude"
    HOPE = "hope"
    TRUST = "trust"
    ANTICIPATION = "anticipation"
    CALMNESS = "calmness"
    CONTENTMENT = "contentment"
    RELAXATION = "relaxation"
    RELIEF = "relief"
    SERENITY = "serenity"
    AWE = "awe"
    NOSTALGIA = "nostalgia"
    INTEREST = "interest"
    SURPRISE = "surprise"
