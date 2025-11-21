"""Utilities for creating Obsidian zettel files from concepts.

This module provides functions for generating Obsidian markdown files from concept
data, including YAML frontmatter formatting and markdown content generation with
concept relations and links.
"""

from __future__ import annotations

import os
from typing import Dict, List, Any
import yaml

from zettel_agent.db import get_neo4j_connection_manager, find_concept_by_uuid


def get_zettel_directory(vault_path: str = "D:\\yo") -> str:
    """
    Get the path to the Zettels directory.
    
    Args:
        vault_path: Path to Obsidian vault (default: "D:\\yo")
        
    Returns:
        Path to "08 - Ideas" directory within the vault
        
    Example:
        ```python
        zettel_dir = get_zettel_directory("D:\\my_vault")
        # Returns: "D:\\my_vault\\08 - Ideas"
        ```
    """
    return os.path.join(vault_path, "08 - Ideas")


def format_zettel_frontmatter(
    concept_uuid: str,
    summary_short: str,
    summary: str,
    concept_relations: Dict[str, List[str]]
) -> str:
    """
    Generate YAML frontmatter for Obsidian zettel file.
    
    Args:
        concept_uuid: UUID of the concept
        summary_short: Short summary (30 words max)
        summary: Detailed summary (100 words max)
        concept_relations: Dict mapping relation types to lists of target concept UUIDs
    
    Returns:
        YAML frontmatter string
    """
    frontmatter = {
        "entity_id": concept_uuid,
        "entity_type": "Concept",
        "short_summary": summary_short,
        "summary": summary,
        "concept_relations": concept_relations
    }
    
    # Convert to YAML string
    yaml_str = yaml.dump(frontmatter, allow_unicode=True, sort_keys=False)
    return f"---\n{yaml_str}---\n"


def format_zettel_content(
    title: str,
    concept: str,
    analysis: str,
    concept_relations: Dict[str, List[str]],
    concept_names: Dict[str, str],
    source: str | None = None
) -> str:
    """
    Generate markdown content for Obsidian zettel file.
    
    Args:
        title: Concept title
        concept: Core concept description
        analysis: Personal analysis
        concept_relations: Dict mapping relation types to lists of target concept UUIDs
        concept_names: Dict mapping concept UUIDs to concept names
        source: Optional source reference
    
    Returns:
        Markdown content string
    """
    lines = [f"# {title}", "", "## Concepto", concept, "", "## Análisis", analysis, "", "## Conexiones"]
    
    # All 9 relation types in order
    relation_types = [
        "GENERALIZES", "SPECIFIC_OF", "PART_OF", "HAS_PART",
        "SUPPORTS", "SUPPORTED_BY", "OPPOSES", "SIMILAR_TO", "RELATES_TO"
    ]
    
    for rel_type in relation_types:
        target_uuids = concept_relations.get(rel_type, [])
        if target_uuids:
            # Convert UUIDs to concept names for links
            concept_links = [f"[[{concept_names.get(uuid, uuid)}]]" for uuid in target_uuids]
            lines.append(f"- {rel_type}: {', '.join(concept_links)}")
        else:
            lines.append(f"- {rel_type}: ")
    
    lines.append("")
    lines.append("## Fuente")
    if source:
        lines.append(source)
    else:
        lines.append("")
    
    return "\n".join(lines)


async def resolve_concept_names(concept_uuids: List[str]) -> Dict[str, str]:
    """
    Resolve concept UUIDs to concept names by querying Neo4j.
    
    For each UUID, queries the database to find the concept and extracts its name.
    Uses the concept's `name` field if available, otherwise falls back to `title`,
    or the UUID itself if neither is available.
    
    Args:
        concept_uuids: List of concept UUIDs to resolve
        
    Returns:
        Dictionary mapping UUIDs to concept names
        
    Example:
        ```python
        concept_names = await resolve_concept_names(["uuid-1", "uuid-2"])
        # Returns: {"uuid-1": "Concept Name 1", "uuid-2": "Concept Name 2"}
        ```
    """
    connection_manager = get_neo4j_connection_manager()
    concept_names = {}
    
    async with connection_manager.session() as session:
        for uuid in concept_uuids:
            from zettel_agent.db import find_concept_by_uuid
            concept = await find_concept_by_uuid(session, uuid)
            if concept:
                # Use name if available, otherwise title
                concept_names[uuid] = concept.name if hasattr(concept, 'name') and concept.name else (
                    concept.title if hasattr(concept, 'title') and concept.title else uuid
                )
    
    return concept_names


async def create_zettel_file(
    concept_uuid: str,
    title: str,
    concept: str,
    analysis: str,
    summary_short: str,
    summary: str,
    concept_relations: Dict[str, List[str]],
    source: str | None = None,
    vault_path: str = "D:\\yo"
) -> str:
    """
    Create an Obsidian zettel file for a concept.
    
    Args:
        concept_uuid: UUID of the concept
        title: Concept title
        concept: Core concept description
        analysis: Personal analysis
        summary_short: Short summary
        summary: Detailed summary
        concept_relations: Dict mapping relation types to lists of target concept UUIDs
        source: Optional source reference
        vault_path: Path to Obsidian vault
    
    Returns:
        Path to the created file
    """
    # Get all unique concept UUIDs from relations
    all_uuids = set()
    for uuids in concept_relations.values():
        all_uuids.update(uuids)
    
    # Resolve UUIDs to names
    concept_names = await resolve_concept_names(list(all_uuids))
    
    # Generate frontmatter and content
    frontmatter = format_zettel_frontmatter(
        concept_uuid, summary_short, summary, concept_relations
    )
    content = format_zettel_content(
        title, concept, analysis, concept_relations, concept_names, source
    )
    
    # Determine file path (use title as filename, sanitized)
    zettel_dir = get_zettel_directory(vault_path)
    os.makedirs(zettel_dir, exist_ok=True)
    
    # Sanitize filename (remove invalid characters)
    safe_title = "".join(c for c in title if c.isalnum() or c in (' ', '-', '_')).strip()
    safe_title = safe_title.replace(' ', '_')
    filename = f"{safe_title}.md"
    file_path = os.path.join(zettel_dir, filename)
    
    # Write file
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(frontmatter)
        f.write("\n")
        f.write(content)
    
    return file_path

