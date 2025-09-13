from dataclasses import dataclass
from datetime import date, datetime
from enum import Enum
from typing import List, Dict


class EntityType(Enum):
    PERSON = "Person"
    FEELING = "Feeling"
    EMOTION = "Emotion"
    EVENT = "Event"
    PROJECT = "Project"
    CONCEPT = "Concept"
    RESOURCE = "Resource"
    JOURNAL_ENTRY = "JournalEntry"


class RelationshipType(Enum):
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


@dataclass
class Person:
    id: str
    full_name: str
    aliases: List[str] = None
    occupation: str = None
    relationship_type: str = None
    birth_date: date = None
    first_mentioned: datetime = None
    last_updated: datetime = None
    mention_count: int = 0
    emotional_valence: float = 0.0


@dataclass
class Feeling:
    id: str
    emotion_type: str
    intensity: int
    timestamp: datetime
    duration_minutes: int = None
    context: str = None
    triggers: List[str] = None
    journal_entry_id: str = None


@dataclass
class Event:
    id: str
    title: str
    event_type: str
    start_date: datetime
    end_date: datetime = None
    location: str = None
    participants: List[str] = None
    significance_level: int = 5
    emotional_impact: float = 0.0
    tags: List[str] = None


@dataclass
class Project:
    id: str
    name: str
    description: str
    status: str
    priority: str = "medium"
    start_date: date = None
    target_completion: date = None
    progress_percentage: float = 0.0
    associated_people: List[str] = None
    related_concepts: List[str] = None
    milestones: List[Dict] = None


@dataclass
class Concept:
    id: str
    title: str
    definition: str
    category: str
    complexity_level: int = 3
    understanding_level: int = 3
    first_encountered: date = None
    source_type: str = None
    related_quotes: List[str] = None
    practical_applications: List[str] = None


@dataclass
class Resource:
    id: str
    title: str
    type: str
    author: str = None
    status: str = "to_consume"
    rating: int = None
    consumption_date: date = None
    key_insights: List[str] = None
    quotes: List[Dict] = None
    tags: List[str] = None


@dataclass
class JournalEntry:
    id: str
    date: date
    word_count: int
    processing_status: str = "pending"
    psychological_metrics: Dict = None
    sleep_data: Dict = None
    extraction_confidence: float = None
    curation_completed: datetime = None
