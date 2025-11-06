"""
Minerva Models - Shared Pydantic models for knowledge graph.

Exports all models, enums, and base classes for use across Minerva packages.
"""

from .base import Document, LexicalType, Node, PartitionType
from .documents import Chunk, JournalEntry, Quote, Span
from .entities import (
    Concept,
    Consumable,
    Content,
    Emotion,
    EmotionType,
    Entity,
    EntityType,
    Event,
    FeelingConcept,
    FeelingEmotion,
    Person,
    Place,
    Project,
    ProjectStatus,
    ResourceStatus,
    ResourceType,
)
from .relations import ConceptRelation, ConceptRelationType, Relation, RelationshipType

# Entity type mapping for dynamic instantiation
ENTITY_TYPE_MAP = {
    EntityType.PERSON: Person,
    EntityType.FEELING_EMOTION: FeelingEmotion,
    EntityType.FEELING_CONCEPT: FeelingConcept,
    EntityType.EMOTION: Emotion,
    EntityType.EVENT: Event,
    EntityType.PROJECT: Project,
    EntityType.CONCEPT: Concept,
    EntityType.CONTENT: Content,
    EntityType.CONSUMABLE: Consumable,
    EntityType.PLACE: Place,
}

RELATIONSHIP_TYPE_MAP = {RelationshipType.RELATED_TO: Relation}

__all__ = [
    # Base classes
    "Node",
    "Document",
    "Entity",
    "PartitionType",
    "LexicalType",
    # Entities
    "Person",
    "Concept",
    "Content",
    "Emotion",
    "Event",
    "Project",
    "Consumable",
    "Place",
    "FeelingEmotion",
    "FeelingConcept",
    # Documents
    "Quote",
    "JournalEntry",
    "Span",
    "Chunk",
    # Relations
    "Relation",
    "ConceptRelation",
    # Enums
    "EntityType",
    "ResourceType",
    "ResourceStatus",
    "ProjectStatus",
    "EmotionType",
    "RelationshipType",
    "ConceptRelationType",
    # Mappings
    "ENTITY_TYPE_MAP",
    "RELATIONSHIP_TYPE_MAP",
]

