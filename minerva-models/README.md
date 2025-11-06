# Minerva Models

Shared Pydantic models for the Minerva knowledge graph system.

This package contains all graph node models (entities, documents, relations) and their base classes, extracted from `minerva-backend` to be usable across multiple packages without importing the entire backend.

## Models Included

- **Base**: `Node`, `Document`, `PartitionType`, `LexicalType`
- **Entities**: `Person`, `Concept`, `Content`, `Emotion`, `Event`, `Project`, `Consumable`, `Place`, `FeelingEmotion`, `FeelingConcept`
- **Documents**: `Quote`, `JournalEntry`, `Span`, `Chunk`
- **Relations**: `Relation`, `ConceptRelation`
- **Enums**: `EntityType`, `ResourceType`, `ResourceStatus`, `ProjectStatus`, `EmotionType`, `RelationshipType`, `ConceptRelationType`

## Usage

```python
from minerva_models.entities import Content, Person, Concept
from minerva_models.documents import Quote
from minerva_models.base import Node, Document
```

