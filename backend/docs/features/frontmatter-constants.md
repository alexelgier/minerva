# Frontmatter Constants Documentation

## 🎯 Overview

The Minerva system uses standardized YAML frontmatter keys across all Obsidian notes to ensure consistency and maintainability. All frontmatter operations use centralized constants defined in `minerva_backend.obsidian.frontmatter_constants`.

## 📋 Standardized Frontmatter Keys

### Entity Identification
- **`entity_id`** - Unique identifier (UUID) for the entity in the database
- **`entity_type`** - Type of entity (Person, Concept, Event, etc.)

### Summary Fields
- **`short_summary`** - Brief description (max 30 words, LLM-generated)
- **`summary`** - Detailed description (max 100 words, LLM-generated)

### Entity Metadata
- **`aliases`** - Alternative names for the entity (array of strings)
- **`concept_relations`** - UUID-based concept relationships (object with relation types as keys)

## 🔧 Implementation

### Constants Module
```python
# backend/src/minerva_backend/obsidian/frontmatter_constants.py

# Entity identification keys
ENTITY_ID_KEY = "entity_id"
ENTITY_TYPE_KEY = "entity_type"

# Summary keys
SHORT_SUMMARY_KEY = "short_summary"
SUMMARY_KEY = "summary"

# Entity metadata keys
ALIASES_KEY = "aliases"
CONCEPT_RELATIONS_KEY = "concept_relations"
```

### Usage in Code
```python
from minerva_backend.obsidian.frontmatter_constants import (
    ENTITY_ID_KEY,
    ENTITY_TYPE_KEY,
    SHORT_SUMMARY_KEY,
    SUMMARY_KEY,
)

# Update frontmatter with constants
obsidian_service.update_link(
    entity.name,
    {
        ENTITY_ID_KEY: entity_uuid,
        ENTITY_TYPE_KEY: entity.type,
        SHORT_SUMMARY_KEY: entity.summary_short,
        SUMMARY_KEY: entity.summary,
    },
)
```

## 📝 Frontmatter Template

### Standard Zettel Template
```yaml
---
entity_id: "uuid-will-be-added-automatically"
entity_type: "Concept"
short_summary: "Brief concept description (LLM-generated)"
summary: "Detailed concept description (LLM-generated)"
aliases: ["Alternative Name 1", "Alternative Name 2"]
concept_relations:
  GENERALIZES: ["uuid1", "uuid2"]
  PART_OF: ["uuid3"]
---
```

### Entity Notes Template
```yaml
---
entity_id: "uuid-will-be-added-automatically"
entity_type: "Person"
short_summary: "Brief person description (LLM-generated)"
summary: "Detailed person description (LLM-generated)"
aliases: ["Nickname", "Alternative Name"]
---
```

## 🔄 Benefits

### Code Maintainability
- **Centralized Constants**: All frontmatter keys defined in one location
- **Type Safety**: Prevents typos in frontmatter key names
- **Easy Updates**: Changes to frontmatter structure only require updating constants

### Consistency
- **Standardized Keys**: All frontmatter operations use the same key names
- **Predictable Structure**: Frontmatter follows consistent patterns across all notes
- **Documentation**: Constants serve as living documentation of frontmatter structure

### Developer Experience
- **IDE Support**: Autocomplete and refactoring support for frontmatter keys
- **Error Prevention**: Compile-time checking prevents invalid key names
- **Self-Documenting**: Code is more readable with named constants

## 📚 Related Documentation

- [Concept Extraction](concept-extraction.md) - How frontmatter is used in Zettel processing
- [Concept Relations](concept-relations.md) - How `concept_relations` frontmatter is managed
- [Field Comparison](field-comparison.md) - How frontmatter fields are compared during sync
- [Processing Pipeline](architecture/processing-pipeline.md) - How frontmatter fits into the overall system
