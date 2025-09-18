from enum import Enum

from minerva_backend.graph.models.entities import Person, Feeling, Emotion, Event, Project, Concept, Content, \
    Consumable, Place
from minerva_backend.graph.models.relations import Relation


# ----------------------------
# Core entity + relationship + partition types
# ----------------------------

class EntityType(str, Enum):
    PERSON = "Person"
    FEELING = "Feeling"
    EMOTION = "Emotion"
    EVENT = "Event"
    PROJECT = "Project"
    CONCEPT = "Concept"
    CONTENT = "Content"
    CONSUMABLE = "Consumable"
    PLACE = "Place"


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


class RelationshipType(str, Enum):
    RELATED_TO = "RELATED_TO"


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


class ProjectStatus(str, Enum):
    NOT_STARTED = "NOT_STARTED"
    ACTIVE = "ACTIVE"
    ON_HOLD = "ON_HOLD"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"


class ResourceType(str, Enum):
    BOOK = "BOOK"
    ARTICLE = "ARTICLE"
    YOUTUBE = "YOUTUBE"
    MOVIE = "MOVIE"
    MISC = "MISC"


class ResourceStatus(str, Enum):
    WANT_TO_CONSUME = "WANT_TO_CONSUME"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    REFERENCE = "REFERENCE"
    ABANDONED = "ABANDONED"
