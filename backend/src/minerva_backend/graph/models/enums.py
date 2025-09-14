from enum import Enum


# ----------------------------
# Core entity + relationship + partition types
# ----------------------------

class EntityType(str, Enum):
    PERSON = "PERSON"
    FEELING = "FEELING"
    EMOTION = "EMOTION"
    EVENT = "EVENT"
    PROJECT = "PROJECT"
    CONCEPT = "CONCEPT"
    RESOURCE = "RESOURCE"


class DocumentType(str, Enum):
    JOURNAL_ENTRY = "JOURNAL_ENTRY"


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
