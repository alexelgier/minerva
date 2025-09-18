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
    ANGER = "Anger"
    ANNOYANCE = "Annoyance"
    CONTEMPT = "Contempt"
    DISGUST = "Disgust"
    IRRITATION = "Irritation"
    ANXIETY = "Anxiety"
    EMBARRASSMENT = "Embarrassment"
    FEAR = "Fear"
    HELPLESSNESS = "Helplessness"
    POWERLESSNESS = "Powerlessness"
    WORRY = "Worry"
    DOUBT = "Doubt"
    ENVY = "Envy"
    FRUSTRATION = "Frustration"
    GUILT = "Guilt"
    SHAME = "Shame"
    CONFUSION = "Confusion"
    BOREDOM = "Boredom"
    DESPAIR = "Despair"
    DISAPPOINTMENT = "Disappointment"
    HURT = "Hurt"
    SADNESS = "Sadness"
    LONELINESS = "Loneliness"
    STRESS = "Stress"
    TENSION = "Tension"
    AMUSEMENT = "Amusement"
    DELIGHT = "Delight"
    ELATION = "Elation"
    EXCITEMENT = "Excitement"
    HAPPINESS = "Happiness"
    JOY = "Joy"
    PLEASURE = "Pleasure"
    SATISFACTION = "Satisfaction"
    AFFECTION = "Affection"
    EMPATHY = "Empathy"
    LOVE = "Love"
    PRIDE = "Pride"
    GRATITUDE = "Gratitude"
    HOPE = "Hope"
    TRUST = "Trust"
    ANTICIPATION = "Anticipation"
    CALMNESS = "Calmness"
    CONTENTMENT = "Contentment"
    RELAXATION = "Relaxation"
    RELIEF = "Relief"
    SERENITY = "Serenity"
    AWE = "Awe"
    NOSTALGIA = "Nostalgia"
    INTEREST = "Interest"
    SURPRISE = "Surprise"
