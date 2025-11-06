"""
Constants for YAML frontmatter keys used throughout the Minerva system.

This module centralizes all frontmatter key definitions to ensure consistency
across the codebase and make maintenance easier.
"""

# Entity identification keys
ENTITY_ID_KEY = "entity_id"
ENTITY_TYPE_KEY = "entity_type"

# Summary keys
SHORT_SUMMARY_KEY = "short_summary"
SUMMARY_KEY = "summary"

# Entity metadata keys
ALIASES_KEY = "aliases"

# Concept relations key
CONCEPT_RELATIONS_KEY = "concept_relations"

# All frontmatter keys for easy iteration
ALL_FRONTMATTER_KEYS = [
    ENTITY_ID_KEY,
    ENTITY_TYPE_KEY,
    SHORT_SUMMARY_KEY,
    SUMMARY_KEY,
    ALIASES_KEY,
    CONCEPT_RELATIONS_KEY,
]
