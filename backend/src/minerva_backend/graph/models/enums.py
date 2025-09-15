from enum import Enum


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
    RESOURCE = "Resource"
    CONSUMABLE = "Consumable"
    PLACE = "Place"


class LexicalType(str, Enum):
    JOURNAL_ENTRY = "JournalEntry"
    SPAN = "Span"


class RelationshipType(str, Enum):
    RELATED_TO = "RELATED_TO"


class PartitionType(str, Enum):
    DOMAIN = "DOMAIN"
    LEXICAL = "LEXICAL"
    TEMPORAL = "TEMPORAL"


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
