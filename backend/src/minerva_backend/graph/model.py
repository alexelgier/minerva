from __future__ import annotations

from abc import ABC
from datetime import date, datetime, timedelta, timezone
from enum import Enum
from typing import List, Optional, Literal
from uuid import uuid4

from pydantic import BaseModel, Field


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
    ENTERTAINS = "ENTERTAINS"
    PARTICIPATES_IN = "PARTICIPATES_IN"
    WORKS_ON = "WORKS_ON"
    KNOWS = "KNOWS"
    TRIGGERS = "TRIGGERS"
    TRIGGERED_BY = "TRIGGERED_BY"
    RELATES_TO = "RELATES_TO"
    INVOLVES = "INVOLVES"
    TEACHES = "TEACHES"
    MENTIONS = "MENTIONS"
    CONTAINS = "CONTAINS"


class PartitionType(str, Enum):
    DOMAIN = "DOMAIN"
    LEXICAL = "LEXICAL"


# ----------------------------
# Base Entity
# ----------------------------

class Node(BaseModel, ABC):
    """Abstract entity. All nodes get at least these fields."""
    partition: PartitionType = Field(..., description='partition of the graph')
    uuid: str = Field(default_factory=lambda: str(uuid4()))
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Config:
        extra = "allow"  # allow schema evolution (new fields in future)
        use_enum_values = True


class Entity(Node, ABC):
    name: str = Field(..., description='name of the entity')
    type: EntityType = Field(..., description="Entity type (Person, Event, etc)")
    summary_short: str = Field(..., description="Summary of the entity. Max 30 words")
    summary: str = Field(..., description="Summary of the entity. Max 300 words")
    partition: Literal[PartitionType.DOMAIN] = Field(PartitionType.DOMAIN.value,
                                                     description="Partition type (always DOMAIN)")
    name_embedding: list[float] | None = Field(default=None, description='embedding of the name')


class Document(Node, ABC):
    type: DocumentType = Field(..., description="Document type")
    text: str = Field(..., description="The original text of the document")
    partition: Literal[PartitionType.LEXICAL] = Field(PartitionType.LEXICAL.value,
                                                      description="Partition type (always LEXICAL)")


class Chunk(Node, ABC):
    text: str = Field(..., description="The text of the chunk")
    partition: Literal[PartitionType.LEXICAL] = Field(PartitionType.LEXICAL.value,
                                                      description="Partition type (always LEXICAL)")
    embedding: list[float] | None = Field(default=None, description='embedding of the chunk')


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


# ----------------------------
# Specific entities (all extend Entity)
# ----------------------------

class Person(Entity):
    """Represents an individual person."""
    type: Literal[EntityType.PERSON] = Field(EntityType.PERSON.value, description="Entity type (always PERSON)")
    occupation: str | None = Field(default=None, description="Job title or profession")
    birth_date: date | None = Field(default=None, description="Date of birth")


class Emotion(Entity):
    """Represents a distinct type of emotion that can be felt"""
    type: Literal[EntityType.EMOTION] = Field(EntityType.EMOTION.value, description="Entity type (always EMOTION)")


class Feeling(Entity):
    """Reified relationship: Person experiences Emotion or Thought about something"""
    timestamp: datetime = Field(..., description="When this feeling occurred")
    type: Literal[EntityType.FEELING] = Field(EntityType.FEELING.value, description="Entity type (always FEELING)")
    intensity: int | None = Field(default=None, description="Intensity level (1-10)")
    duration: timedelta | None = Field(default=None, description="How long the feeling lasted")


class Event(Entity):
    """Represents a notable occurrence or activity that happened at a specific time."""
    category: str = Field(..., description="Category of event (meeting, workout, etc)")
    date: datetime = Field(..., description="When the event occurred")
    type: Literal[EntityType.EVENT] = Field(EntityType.EVENT.value, description="Entity type (always EVENT)")
    duration: timedelta | None = Field(default=None, description="Duration of the event (e.g., 2 hours, 30 minutes)")
    location: str | None = Field(default=None, description="Where the event took place")


class Project(Entity):
    """Represents an ongoing initiative, goal, or multistep endeavor with trackable progress."""
    type: Literal[EntityType.PROJECT] = Field(EntityType.PROJECT.value, description="Entity type (always PROJECT)")
    status: ProjectStatus | None = Field(default=None, description="Current status of the project")
    start_date: datetime | None = Field(default=None, description="Date when the project was started")
    target_completion: datetime | None = Field(default=None, description="Target or expected completion date")
    progress: float | None = Field(default=None, description="Completion percentage (0.0 to 100.0)")


class Concept(Entity):
    """Represents an atomic idea or concept in your zettelkasten knowledge system."""
    title: str = Field(..., description="Concise title of the concept or idea")
    analysis: str = Field(..., description="Your personal analysis, insights, and understanding of the concept")
    type: Literal[EntityType.CONCEPT] = Field(EntityType.CONCEPT.value, description="Entity type (always CONCEPT)")


class Resource(Entity):
    """Represents external content (books, articles, videos) that serve as a source of information or entertainment."""
    title: str = Field(..., description="Title or name of the resource")
    category: ResourceType = Field(..., description="Category of resource")
    type: Literal[EntityType.RESOURCE] = Field(EntityType.RESOURCE.value, description="Entity type (always RESOURCE)")
    url: str | None = Field(default=None, description="Web URL or location where the resource can be accessed")
    quotes: List[str] | None = Field(default=None, description="Notable quotes or excerpts from the resource")
    status: ResourceStatus | None = Field(default=None, description="Current consumption status")
    author: str | None = Field(default=None, description="Creator or author of the resource")


class JournalEntry(Document):
    date: date = Field(..., description="Date of the journal entry")
    type: Literal[DocumentType.JOURNAL_ENTRY] = Field(DocumentType.JOURNAL_ENTRY.value,
                                                      description="Document type (always JOURNAL_ENTRY)")
    entry_text: str | None = Field(default=None, description="The body text of the journal entry")
    panas_pos: List | None = Field(default=None, description="PANAS positive scores")
    panas_neg: List | None = Field(default=None, description="PANAS negative scores")
    bpns: List | None = Field(default=None, description="BPNS scores")
    flourishing: List | None = Field(default=None, description="Flourishing scores")
    wake: datetime | None = Field(default=None, description="Datetime of waking up")
    sleep: datetime | None = Field(default=None, description="Datetime of going to sleep")
