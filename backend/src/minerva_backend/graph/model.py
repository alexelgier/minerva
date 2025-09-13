from __future__ import annotations
from datetime import date, datetime, timedelta
from enum import Enum
from typing import List, Optional, Literal
from pydantic import BaseModel, Field


# ----------------------------
# Core entity + relationship types
# ----------------------------

class EntityType(str, Enum):
    PERSON = "Person"
    FEELING = "Feeling"
    EMOTION = "Emotion"
    EVENT = "Event"
    PROJECT = "Project"
    CONCEPT = "Concept"
    RESOURCE = "Resource"
    JOURNAL_ENTRY = "JournalEntry"


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


# ----------------------------
# Base Entity
# ----------------------------

class Entity(BaseModel):
    """Generic entity. All nodes get at least these fields."""
    id: Optional[str] = Field(
        None, description="Internal unique ID or external UUID"
    )
    type: EntityType = Field(..., description="Entity type (Person, Event, etc.)")
    summary_short: str = Field(..., description="Summary of the entity. Max 30 words.")
    summary: str = Field(..., description="Summary of the entity. Max 300 words.")
    created_at: datetime = Field(default_factory=datetime.now)

    class Config:
        extra = "allow"  # allow schema evolution (new fields in future)
        use_enum_values = True


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
    full_name: str = Field(..., description="Full name of the person")
    occupation: Optional[str] = Field(None, description="Job title or profession")
    birth_date: Optional[date] = Field(None, description="Date of birth")


class Emotion(Entity):
    """Represents a distinct type of emotion that can be felt"""
    type: Literal[EntityType.EMOTION] = Field(EntityType.EMOTION.value, description="Entity type (always EMOTION)")
    emotion_name: str = Field(..., description="Name of the emotion (e.g. joy, anger)")


class Feeling(Entity):
    """Reified relationship: Person experiences Emotion or Thought about something"""
    type: Literal[EntityType.FEELING] = Field(EntityType.FEELING.value, description="Entity type (always FEELING)")
    intensity: Optional[int] = Field(..., description="Intensity level (1-10)")
    timestamp: datetime = Field(..., description="When this feeling occurred")
    duration: Optional[timedelta] = Field(None, description="How long the feeling lasted")


class Event(Entity):
    """Represents a notable occurrence or activity that happened at a specific time."""
    type: Literal[EntityType.EVENT] = Field(EntityType.EVENT.value, description="Entity type (always EVENT)")
    category: str = Field(..., description="Category of event (meeting, workout, etc.)")
    date: datetime = Field(..., description="When the event occurred")
    duration: Optional[timedelta] = Field(None, description="Duration of the event (e.g., 2 hours, 30 minutes)")
    location: Optional[str] = Field(None, description="Where the event took place")


class Project(Entity):
    """Represents an ongoing initiative, goal, or multistep endeavor with trackable progress."""
    type: Literal[EntityType.PROJECT] = Field(EntityType.PROJECT.value, description="Entity type (always PROJECT)")
    project_name: str = Field(..., description="Name or title of the project")
    status: Optional[ProjectStatus] = Field(None, description="Current status of the project")
    start_date: Optional[datetime] = Field(None, description="Date when the project was started")
    target_completion: Optional[datetime] = Field(None, description="Target or expected completion date")
    progress: Optional[float] = Field(None, description="Completion percentage (0.0 to 100.0)")


class Concept(Entity):
    """Represents an atomic idea or concept in your zettelkasten knowledge system."""
    type: Literal[EntityType.CONCEPT] = Field(EntityType.CONCEPT.value, description="Entity type (always CONCEPT)")
    title: str = Field(..., description="Concise title of the concept or idea")
    analysis: str = Field(..., description="Your personal analysis, insights, and understanding of the concept")


class Resource(Entity):
    """Represents external content (books, articles, videos) that serve as a source of information or entertainment."""
    type: Literal[EntityType.RESOURCE] = Field(EntityType.RESOURCE.value, description="Entity type (always RESOURCE)")
    title: str = Field(..., description="Title or name of the resource")
    category: ResourceType = Field(..., description="Category of resource")
    url: Optional[str] = Field(None, description="Web URL or location where the resource can be accessed")
    quotes: Optional[List[str]] = Field(None, description="Notable quotes or excerpts from the resource")
    status: Optional[ResourceStatus] = Field(None, description="Current consumption status")
    author: Optional[str] = Field(None, description="Creator or author of the resource")


class JournalEntry(Entity):
    type: Literal[EntityType.JOURNAL_ENTRY] = Field(EntityType.JOURNAL_ENTRY.value,
                                                    description="Entity type (always JOURNAL_ENTRY)")
    date: date = Field(..., description="Date of the journal entry.")
    fulltext: str = Field(..., description="The complete, original text of the journal entry.")
    text: Optional[str] = Field(None, description="The body text of the journal entry, excluding frontmatter.")
    panas_pos: Optional[List] = Field(None, description="Positive and Negative Affect Schedule (PANAS) positive scores.")
    panas_neg: Optional[List] = Field(None, description="Positive and Negative Affect Schedule (PANAS) negative scores.")
    bpns: Optional[List] = Field(None, description="Basic Psychological Need Satisfaction (BPNS) scores.")
    flourishing: Optional[List] = Field(None, description="Flourishing scale scores.")
    wake: Optional[datetime] = Field(None, description="Time of waking up on the entry's date.")
    sleep: Optional[datetime] = Field(None, description="Time of going to sleep on the entry's date.")
