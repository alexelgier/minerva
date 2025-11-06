import os
import re
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Set, Tuple, Union

import yaml

from minerva_backend.obsidian.frontmatter_constants import (
    ALIASES_KEY,
    CONCEPT_RELATIONS_KEY,
    ENTITY_ID_KEY,
    ENTITY_TYPE_KEY,
    SHORT_SUMMARY_KEY,
    SUMMARY_KEY,
)
from minerva_backend.prompt.generate_zettel_summary import GenerateZettelSummaryPrompt
from minerva_backend.utils.logging import get_logger

# Concept relation mapping
# Maps natural language relation types to (forward_edge_type, reverse_edge_type) tuples
RELATION_MAP: Dict[str, Tuple[str, str]] = {
    "GENERALIZES": ("GENERALIZES", "SPECIFIC_OF"),
    "SPECIFIC_OF": ("SPECIFIC_OF", "GENERALIZES"),
    "PART_OF": ("PART_OF", "HAS_PART"),
    "HAS_PART": ("HAS_PART", "PART_OF"),
    "SUPPORTS": ("SUPPORTS", "SUPPORTED_BY"),
    "SUPPORTED_BY": ("SUPPORTED_BY", "SUPPORTS"),
    "OPPOSES": ("OPPOSES", "OPPOSES"),  # Symmetric
    "SIMILAR_TO": ("SIMILAR_TO", "SIMILAR_TO"),  # Symmetric
    "RELATES_TO": ("RELATES_TO", "RELATES_TO"),  # Symmetric
}


@dataclass
class ResolvedLink:
    """Representa el resultado de resolver un enlace de Obsidian."""

    file_path: Optional[str] = None
    entity_name: Optional[str] = None
    entity_long_name: Optional[str] = None
    entity_id: Optional[str] = None
    entity_type: Optional[str] = None
    aliases: Optional[List[str]] = None
    display_text: str = ""
    short_summary: Optional[str] = None


@dataclass
class SyncResult:
    """
    Result of syncing Zettels to database.

    This class provides comprehensive information about the sync process,
    including statistics, errors, and data quality issues.

    Attributes:
        total_files: Total number of Zettel files found
        parsed: Number of files successfully parsed
        created: Number of new concepts created
        updated: Number of existing concepts updated
        unchanged: Number of concepts that existed but had no changes
        errors: Number of errors encountered
        errors_list: List of error messages
        missing_concepts: List of concept names that don't exist yet
        broken_notes: List of file paths with corrupted frontmatter
        relations_created: Number of concept relations created
        relations_updated: Number of concept relations updated
        relations_deleted: Number of orphaned relations deleted from database
        self_connections_removed: Number of self-connections cleaned up
        inconsistent_relations: List of inconsistency descriptions
    """

    total_files: int
    parsed: int
    created: int
    updated: int
    unchanged: int  # Concepts that existed but had no changes
    errors: int
    errors_list: List[str]
    missing_concepts: List[str]
    broken_notes: List[str]
    relations_created: int
    relations_updated: int
    self_connections_removed: int
    inconsistent_relations: List[str]
    relations_deleted: int = 0  # Relations removed from database


class ObsidianService:
    """Service for resolving Obsidian links and managing vault cache."""

    def __init__(
        self, vault_path: str = "D:\\yo", llm_service=None, concept_repository=None
    ):
        self.vault_path = vault_path
        self._cache: Optional[Dict[str, str]] = None
        self.llm_service = llm_service
        self.concept_repository = concept_repository
        self.logger = get_logger("minerva_backend.obsidian.obsidian_service")
        self.logger.info(
            f"ObsidianService initialized with vault_path={vault_path}, llm_service={llm_service is not None}, concept_repository={concept_repository is not None}"
        )

    def _build_cache(self) -> Dict[str, str]:
        """Construye un caché de todas las notas en el vault, indexado por nombre de archivo."""
        if self._cache is not None:
            return self._cache

        self.logger.info("Construyendo caché del vault...")
        self._cache = {}

        for root, dirs, files in os.walk(self.vault_path):
            for file in files:
                if file.endswith(".md"):
                    full_path = os.path.join(root, file)
                    nombre_archivo = file[:-3]  # Remove .md
                    self._cache[nombre_archivo] = full_path

                    # También almacenar por ruta relativa completa para casos disambiguados
                    rel_path = os.path.relpath(full_path, self.vault_path)
                    rel_path_key = rel_path.replace("\\", "/")[
                        :-3
                    ]  # Normalizar y quitar .md
                    if rel_path_key != nombre_archivo:  # Solo si es diferente
                        self._cache[rel_path_key] = full_path

        self.logger.info(f"Caché construido con {len(self._cache)} entradas")
        return self._cache

    def rebuild_cache(self) -> None:
        """Force rebuild of the vault cache."""
        self._cache = None
        self._build_cache()

    def _parse_yaml_frontmatter(self, file_path: str) -> Optional[Dict]:
        """Extrae el YAML frontmatter de un archivo markdown."""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            # Check if file starts with frontmatter
            if not content.startswith("---"):
                return None

            # Find the end of frontmatter
            lines = content.split("\n")
            yaml_end = None
            for i, line in enumerate(lines[1:], 1):
                if line.strip() == "---":
                    yaml_end = i
                    break

            if yaml_end is None:
                return None

            # Extract YAML content
            yaml_content = "\n".join(lines[1:yaml_end])
            return yaml.safe_load(yaml_content)

        except (yaml.YAMLError, IOError, UnicodeDecodeError):
            # Invalid YAML or file read error - skip
            return None

    def _normalize_aliases(
        self, aliases_value: Union[str, List[str], None]
    ) -> Optional[List[str]]:
        """Normalizes the aliases field which can come in various formats."""
        if aliases_value is None:
            return None

        if isinstance(aliases_value, str):
            return [aliases_value]
        elif isinstance(aliases_value, list):
            return [str(alias) for alias in aliases_value]
        else:
            return None

    def resolve_link(self, link_text: str) -> ResolvedLink:
        """
        Resolves an Obsidian link to file path and entity metadata.

        Args:
            link_text: Raw link content, e.g.:
                - "Federico Demarchi"
                - "Federico Demarchi|Fede"
                - "05 - Personal/Proyectos/Música/Música|Música"

        Returns:
            ResolvedLink: Instancia con la información del enlace resuelto
        """
        # Ensure cache is built
        cache = self._build_cache()

        # Parse the link text
        if "|" in link_text:
            target, display_text = link_text.split("|", 1)
        else:
            target = link_text
            display_text = link_text

        # Initialize result
        result = ResolvedLink(
            entity_long_name=target, display_text=display_text.strip()
        )

        # Look up in cache
        target = target.strip()

        # Always set entity_name from the target (the note title being referenced)
        if "/" in target:
            # For disambiguated paths, extract the actual note name (last part)
            result.entity_name = os.path.basename(target)
        else:
            # For simple cases, the target is the note name
            result.entity_name = target

        if target not in cache:
            return result

        file_path = cache[target]
        result.file_path = file_path

        # Parse frontmatter for entity metadata
        frontmatter = self._parse_yaml_frontmatter(file_path)
        if frontmatter:
            result.entity_id = frontmatter.get(ENTITY_ID_KEY)
            result.entity_type = frontmatter.get(ENTITY_TYPE_KEY)
            result.aliases = self._normalize_aliases(frontmatter.get(ALIASES_KEY))
            result.short_summary = frontmatter.get(SHORT_SUMMARY_KEY)

        return result

    def update_link(self, link_text: str, metadata: Dict[str, Any]) -> bool:
        """
        Updates the YAML frontmatter of a note identified by a link.

        Args:
            link_text: Raw link content, e.g., "Federico Demarchi".
            metadata: A dictionary of metadata to update in the frontmatter.
                      Existing keys will be overwritten.
                      To remove a key, provide it with a value of None.

        Returns:
            True if the update was successful, False otherwise.
        """
        try:
            # Get or create the target file
            file_path = self._get_or_create_target_file(link_text)
            if not file_path:
                return False

            # Read and parse existing content
            content = self._read_file_content(file_path)
            existing_frontmatter, body = self._parse_frontmatter_and_body(content)

            # Update frontmatter with new metadata
            updated_frontmatter = self._merge_frontmatter(
                existing_frontmatter, metadata
            )

            # Write updated content back to file
            self._write_updated_file(file_path, updated_frontmatter, body)
            return True

        except (IOError, yaml.YAMLError, UnicodeDecodeError):
            return False

    def _get_or_create_target_file(self, link_text: str) -> str | None:
        """Get the target file path, creating it if it doesn't exist."""
        cache = self._build_cache()
        target = self._extract_target_from_link(link_text)
        file_path = cache.get(target)

        if not file_path:
            file_path = self._create_new_note_file(target)
            self._update_cache_with_new_file(target, file_path)

        return file_path

    def _extract_target_from_link(self, link_text: str) -> str:
        """Extract the target file name from link text."""
        if "|" in link_text:
            target, _ = link_text.split("|", 1)
        else:
            target = link_text
        return target.strip()

    def _create_new_note_file(self, target: str) -> str:
        """Create a new note file for the given target."""
        relative_path_with_ext = target.replace("/", os.sep) + ".md"
        file_path = os.path.join(self.vault_path, relative_path_with_ext)

        # Ensure parent directory exists
        parent_dir = os.path.dirname(file_path)
        os.makedirs(parent_dir, exist_ok=True)

        # Create a placeholder empty file
        with open(file_path, "w", encoding="utf-8"):
            pass

        return file_path

    def _update_cache_with_new_file(self, target: str, file_path: str) -> None:
        """Update the cache with the new file."""
        if self._cache is None:
            self._cache = {}
        self._cache[target] = file_path
        # Also key by note name only, if different
        nombre_archivo = os.path.basename(target)
        if nombre_archivo != target:
            self._cache[nombre_archivo] = file_path

    def _read_file_content(self, file_path: str) -> str:
        """Read file content from the given path."""
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()

    def _parse_frontmatter_and_body(self, content: str) -> tuple[Dict[str, Any], str]:
        """Parse frontmatter and body from file content."""
        existing_frontmatter: Dict[str, Any] = {}
        body = content

        if content.startswith("---"):
            lines = content.split("\n")
            yaml_end_index = self._find_yaml_end_index(lines)

            if yaml_end_index > 0:
                frontmatter_lines = lines[1:yaml_end_index]
                frontmatter_str = "\n".join(frontmatter_lines)
                existing_frontmatter = yaml.safe_load(frontmatter_str) or {}
                body = "\n".join(lines[yaml_end_index + 1 :])

        return existing_frontmatter, body

    def _find_yaml_end_index(self, lines: List[str]) -> int:
        """Find the index of the YAML end marker."""
        for i, line in enumerate(lines[1:], 1):
            if line.strip() == "---":
                return i
        return -1

    def _merge_frontmatter(
        self, existing_frontmatter: Dict[str, Any], metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Merge new metadata with existing frontmatter, removing None values."""
        existing_frontmatter.update(metadata)
        return {k: v for k, v in existing_frontmatter.items() if v is not None}

    def _write_updated_file(
        self, file_path: str, frontmatter: Dict[str, Any], body: str
    ) -> None:
        """Write the updated content back to the file."""
        with open(file_path, "w", encoding="utf-8") as f:
            if frontmatter:
                f.write("---\n")
                yaml.dump(frontmatter, f, allow_unicode=True, sort_keys=False)
                f.write("---\n")
            f.write(body)

    def _build_obsidian_entity_lookup(self, links: List[str]) -> Dict[str, Any]:
        """Build lookup tables for existing Obsidian entities and their aliases."""
        # Resolve all links to get entity metadata
        resolved_links = self._resolve_all_links(links)

        # Remove duplicates based on entity_long_name
        unique_links = self._remove_duplicate_links(resolved_links)

        # Build lookup tables
        name_to_entity = self._build_name_lookup(unique_links)
        entities_with_db_ids = self._filter_entities_with_db_ids(unique_links)
        glossary = self._build_glossary(unique_links)

        return {
            "name_lookup": name_to_entity,
            "db_entities": entities_with_db_ids,
            "glossary": glossary,
        }

    def _resolve_all_links(self, links: List[str]) -> List:
        """Resolve all links to get entity metadata."""
        resolved_links = []
        for link in links:
            resolved = self.resolve_link(link)
            resolved_links.append(resolved)
        return resolved_links

    def _remove_duplicate_links(self, resolved_links: List) -> List:
        """Remove duplicates based on entity_long_name."""
        return list({link.entity_long_name: link for link in resolved_links}.values())

    def _build_name_lookup(self, unique_links: List) -> Dict[str, Any]:
        """Build name-to-entity lookup including aliases."""
        name_to_entity = {}

        for link_data in unique_links:
            entity_name = link_data.entity_name

            # Map primary name to entity data
            if entity_name and entity_name not in name_to_entity:
                name_to_entity[entity_name] = link_data

            # Map aliases to the same entity data
            if link_data.aliases:
                for alias in link_data.aliases:
                    if alias not in name_to_entity:
                        name_to_entity[alias] = link_data

        return name_to_entity

    def _filter_entities_with_db_ids(self, unique_links: List) -> List:
        """Filter entities that exist in the database."""
        return [link for link in unique_links if link.entity_id]

    def _build_glossary(self, unique_links: List) -> Dict[str, str]:
        """Build glossary mapping entity names to short summaries."""
        return {
            link.entity_name: link.short_summary
            for link in unique_links
            if link.entity_name and link.short_summary
        }

    def build_entity_lookup(self, journal_entry) -> Dict[str, Dict]:
        """
        Build lookup tables for existing Obsidian entities and their aliases from a journal entry.

        This method extracts Obsidian links from journal entry text and builds lookup tables
        for entity resolution during extraction.

        Args:
            journal_entry: Journal entry object with entry_text attribute

        Returns:
            Dictionary containing:
            - name_lookup: Maps entity names/aliases to ResolvedLink objects
            - db_entities: List of entities that exist in the database
            - glossary: Maps entity names to short summaries
        """
        import re

        # Extract links from journal entry text
        link_matches = re.findall(
            r"\[\[(.+?)]]", journal_entry.entry_text, re.MULTILINE
        )

        # Add the narrator by default
        link_matches.append("Alex Elgier")

        return self._build_obsidian_entity_lookup(link_matches)

    def get_cache_stats(self) -> Dict:
        """Returns statistics about the vault cache."""
        cache = self._build_cache()
        return {
            "total_notes": len(cache),
            "vault_path": self.vault_path,
            "cache_built": self._cache is not None,
        }

    def find_note_by_name(self, name: str) -> Optional[str]:
        """Find a note file path by its name (without .md extension)."""
        cache = self._build_cache()
        return cache.get(name)

    def get_zettel_directory(self) -> str:
        """Get the path to the Zettel directory."""
        return os.path.join(self.vault_path, "08 - Ideas")

    def find_zettel_files(self) -> List[str]:
        """Find all Zettel files in the Ideas directory."""
        zettel_dir = self.get_zettel_directory()
        if not os.path.exists(zettel_dir):
            return []

        zettel_files = []
        for root, dirs, files in os.walk(zettel_dir):
            for file in files:
                if file.endswith(".md"):
                    zettel_files.append(os.path.join(root, file))

        return zettel_files

    def _compare_concept_content(
        self, db_concept, zettel_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Compare core content fields between database concept and zettel data.

        Args:
            db_concept: Concept entity from database
            zettel_data: Parsed zettel data from file

        Returns:
            Dictionary with comparison results:
            - 'has_changes': bool - whether any core content changed
            - 'changed_fields': list - list of field names that changed
            - 'updates': dict - field updates to apply if changes detected
        """
        changes: Dict[str, Any] = {
            "has_changes": False,
            "changed_fields": [],
            "updates": {},
        }

        # Compare core content fields (user-editable content)
        core_fields = ["concept", "analysis", "source", "title"]

        for field in core_fields:
            db_value = getattr(db_concept, field, None)
            zettel_value = zettel_data.get(field, None)

            # Normalize None/empty values for comparison
            db_value = db_value if db_value is not None else ""
            zettel_value = zettel_value if zettel_value is not None else ""

            if db_value != zettel_value:
                changes["has_changes"] = True
                changes["changed_fields"].append(field)
                changes["updates"][field] = zettel_value
                self.logger.debug(
                    f"Field '{field}' changed for {zettel_data['name']}: "
                    f"'{db_value}' -> '{zettel_value}'"
                )

        return changes

    def parse_zettel_content(self, file_path: str) -> Optional[Dict[str, Any]]:
        """
        Parse a Zettel file and extract its content according to the Zettel template.

        Args:
            file_path: Path to the Zettel file

        Returns:
            Dictionary with parsed Zettel content or None if parsing fails
        """
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            # Parse frontmatter
            frontmatter = self._parse_yaml_frontmatter(file_path) or {}

            # Extract title from filename
            filename = os.path.basename(file_path)
            title = filename[:-3] if filename.endswith(".md") else filename

            # Parse content sections
            sections = self._parse_zettel_sections(content)
            self.logger.debug(f"Parsed sections for {title}: {sections}")

            return {
                "title": title,
                "name": title,  # Use title as name
                "concept": sections.get("concepto", ""),
                "analysis": sections.get("análisis", ""),
                "connections": sections.get(
                    "conexiones", ""
                ),  # Keep raw for processing
                "source": sections.get("fuente", None),
                "file_path": file_path,
                "frontmatter": frontmatter,
            }

        except Exception as e:
            self.logger.error(f"Error parsing Zettel {file_path}: {e}")
            return None

    def _parse_zettel_sections(self, content: str) -> Dict[str, Any]:
        """
        Parse Zettel content into sections.

        Extracts the main sections from a Zettel file (Concepto, Análisis, Conexiones, Fuente)
        and returns them as a dictionary. The conexiones section is returned as a raw string
        for further processing by parse_conexiones_section.

        Args:
            content: The full content of the Zettel file as a string

        Returns:
            Dictionary with section names as keys and content as values:
            - "concepto": String content of the Concepto section
            - "análisis": String content of the Análisis section
            - "conexiones": Raw string content of the Conexiones section
            - "fuente": String content of the Fuente section (or None if missing)
        """
        sections = {"concepto": "", "análisis": "", "conexiones": "", "fuente": None}

        # Remove frontmatter and parse sections
        content_without_frontmatter = self._remove_frontmatter(content)
        self._parse_content_sections(content_without_frontmatter, sections)

        return sections

    def _remove_frontmatter(self, content: str) -> str:
        """Remove YAML frontmatter from content if present."""
        if content.startswith("---"):
            lines = content.split("\n")
            for i, line in enumerate(lines[1:], 1):
                if line.strip() == "---":
                    return "\n".join(lines[i + 1 :])
        return content

    def _parse_content_sections(self, content: str, sections: Dict[str, Any]) -> None:
        """Parse content into sections based on markdown headers."""
        current_section: str | None = None
        current_content: List[str] = []

        for line in content.split("\n"):
            line = line.strip()

            if line.startswith("## "):
                self._handle_section_header(
                    line, sections, current_section or "", current_content
                )
                current_section, current_content = self._process_section_header(
                    line, sections
                )
            else:
                current_section, current_content = self._process_content_line(
                    line, current_section or "", current_content, sections
                )

        # Save last section
        if current_section and current_content:
            sections[current_section] = "\n".join(current_content).strip()

    def _handle_section_header(
        self,
        line: str,
        sections: Dict[str, Any],
        current_section: str,
        current_content: List[str],
    ) -> None:
        """Save the previous section before starting a new one."""
        if current_section and current_content:
            sections[current_section] = "\n".join(current_content).strip()

    def _process_section_header(
        self, line: str, sections: Dict[str, Any]
    ) -> tuple[str, List[str]]:
        """Process a section header and return the new section name and empty content list."""
        section_name = line[3:].lower()
        self.logger.debug(f"Found section header: '{line[3:]}' -> '{section_name}'")

        if section_name in sections:
            self.logger.debug(f"Activating section: {section_name}")
            return section_name, []
        else:
            self.logger.debug(f"Unknown section, ignoring: {section_name}")
            return "", []

    def _process_content_line(
        self,
        line: str,
        current_section: str,
        current_content: List[str],
        sections: Dict[str, Any],
    ) -> tuple[str, List[str]]:
        """Process a content line and add it to the appropriate section."""
        if current_section:
            current_content.append(line)
        elif not current_section and line:
            # This is the main concept text
            sections["concepto"] += line + "\n"

        return current_section, current_content

    def parse_conexiones_section(self, content: str) -> Dict[str, List[str]]:
        """
        Parse Conexiones section and extract relations.

        Parses the raw Conexiones section content from a Zettel file to extract concept relations.
        This method is designed to work with the raw string output from _parse_zettel_sections.
        Expects format: "- RELATION_TYPE: [[Concept1]], [[Concept2]]"

        Args:
            content: The raw Conexiones section content as a string (from _parse_zettel_sections)

        Returns:
            Dictionary mapping relation types to lists of concept names.
            Example: {"GENERALIZES": ["Deep Learning", "Neural Networks"]}

        Note:
            Only processes relation types defined in RELATION_MAP.
            Invalid relation types are ignored.
            Empty relation lines (e.g., "- GENERALIZES: ") result in empty lists for that relation type.
        """
        relations: Dict[str, List[str]] = {}

        self.logger.debug(
            f"Parsing Conexiones section. Content type: {type(content)}, Content: '{content}'"
        )

        if not content:
            self.logger.debug("No content provided to parse_conexiones_section")
            return relations

        # Normalize content to string format
        normalized_content = self._normalize_conexiones_content(content)

        # Parse each line and extract relations
        self._parse_conexiones_lines(normalized_content, relations)

        # Log summary and return results
        self._log_conexiones_summary(relations)
        return relations

    def _normalize_conexiones_content(self, content: str) -> str:
        """Normalize content to string format, handling list inputs."""
        if isinstance(content, list):
            normalized = "\n".join(str(item) for item in content)
            self.logger.debug(f"Converted list to string: '{normalized}'")
            return normalized
        return content

    def _parse_conexiones_lines(
        self, content: str, relations: Dict[str, List[str]]
    ) -> None:
        """Parse each line in the conexiones content and extract relations."""
        for line in content.split("\n"):
            line = line.strip()
            self.logger.debug(f"Processing line: '{line}'")

            if not self._is_valid_relation_line(line):
                continue

            relation_type, links_part = self._extract_relation_parts(line)
            if not relation_type or relation_type not in RELATION_MAP:
                continue

            self._process_relation_line(relation_type, links_part, relations)

    def _is_valid_relation_line(self, line: str) -> bool:
        """Check if a line is a valid relation line."""
        if not line.startswith("- "):
            self.logger.debug(f"Line doesn't start with '- ', skipping: '{line}'")
            return False

        if ":" not in line:
            self.logger.debug(f"Line doesn't contain ':', skipping: '{line}'")
            return False

        return True

    def _extract_relation_parts(self, line: str) -> tuple[str, str]:
        """Extract relation type and links part from a line."""
        relation_part, links_part = line[2:].split(
            ":", 1
        )  # Remove "- " and split on first ":"
        relation_type = relation_part.strip()
        links_part = links_part.strip()

        self.logger.debug(
            f"Found relation type: '{relation_type}', links part: '{links_part}'"
        )

        return relation_type, links_part

    def _process_relation_line(
        self, relation_type: str, links_part: str, relations: Dict[str, List[str]]
    ) -> None:
        """Process a single relation line and add to relations dictionary."""
        if relation_type not in RELATION_MAP:
            self.logger.debug(
                f"Relation type '{relation_type}' not in RELATION_MAP, skipping"
            )
            return

        # Initialize empty list for this relation type if not exists
        if relation_type not in relations:
            relations[relation_type] = []

        # Extract [[link]] patterns only if there's content after the colon
        if links_part:
            links = re.findall(r"\[\[([^\]]+)\]\]", links_part)
            self.logger.debug(f"Extracted links: {links}")
            if links:
                relations[relation_type].extend(links)
                self.logger.debug(
                    f"Added links to relation: {relation_type} -> {relations[relation_type]}"
                )
        else:
            self.logger.debug(
                f"Empty relation line for {relation_type}, keeping empty list"
            )

    def _log_conexiones_summary(self, relations: Dict[str, List[str]]) -> None:
        """Log summary of parsed relations."""
        self.logger.debug(f"Final relations parsed: {relations}")

        total_relations = sum(len(links) for links in relations.values())
        self.logger.info(
            f"Parsed {len(relations)} relation types with {total_relations} total links"
        )

        for rel_type, links in relations.items():
            if links:
                self.logger.info(f"  {rel_type}: {links}")
            else:
                self.logger.debug(f"  {rel_type}: (empty)")

    def update_conexiones_section(
        self, file_path: str, relations: Dict[str, List[str]]
    ) -> bool:
        """
        Update Conexiones section with new relations, preserving user formatting.

        This method reads the existing Conexiones section, merges new relations
        with existing ones, and writes the updated section back to the file.
        It preserves the user's existing formatting and adds new relations
        at the end of each relation type.

        Args:
            file_path: Path to the Obsidian file to update
            relations: Dictionary mapping relation types to lists of concept names
                      Example: {"GENERALIZES": ["Deep Learning", "Neural Networks"]}

        Returns:
            True if the update was successful, False otherwise

        Note:
            If the Conexiones section doesn't exist, the method will return False.
            The method preserves existing relations and only adds new ones.
        """
        try:
            # Read file and find Conexiones section
            content = self._read_file_content(file_path)
            conexiones_bounds = self._find_conexiones_section_bounds(content)
            if not conexiones_bounds:
                return False

            # Extract and parse existing relations
            existing_section = content[conexiones_bounds[0] : conexiones_bounds[1]]
            existing_relations = self.parse_conexiones_section(existing_section)

            # Merge new relations with existing ones
            merged_relations = self._merge_relations(existing_relations, relations)

            # Rebuild and write the updated section
            new_conexiones = self._build_conexiones_section(merged_relations)
            self._write_updated_content(
                file_path, content, conexiones_bounds, new_conexiones
            )

            return True

        except Exception as e:
            self.logger.error(f"Error updating Conexiones section in {file_path}: {e}")
            return False

    def _find_conexiones_section_bounds(self, content: str) -> tuple[int, int] | None:
        """Find the start and end bounds of the Conexiones section."""
        conexiones_start = content.find("## Conexiones")
        if conexiones_start == -1:
            return None

        # Find end of Conexiones section (next ## or end of file)
        next_section = content.find("\n## ", conexiones_start + 1)
        if next_section == -1:
            next_section = len(content)
        else:
            next_section += 1  # Include the newline

        return conexiones_start, next_section

    def _merge_relations(
        self,
        existing_relations: Dict[str, List[str]],
        new_relations: Dict[str, List[str]],
    ) -> Dict[str, List[str]]:
        """Merge new relations with existing ones, avoiding duplicates."""
        merged = existing_relations.copy()

        for relation_type, new_links in new_relations.items():
            if relation_type in merged:
                # Add new links that don't already exist
                existing_links = merged[relation_type]
                for link in new_links:
                    if link not in existing_links:
                        existing_links.append(link)
            else:
                merged[relation_type] = new_links

        return merged

    def _build_conexiones_section(self, relations: Dict[str, List[str]]) -> str:
        """Build the Conexiones section content from relations dictionary."""
        new_conexiones = "## Conexiones\n"

        # Get all standard relation types from RELATION_MAP
        standard_relation_types = list(RELATION_MAP.keys())

        # Get any non-standard relation types that exist in the current section
        non_standard_types = set(relations.keys()) - set(standard_relation_types)

        # Process standard relation types first (in RELATION_MAP order)
        new_conexiones += self._build_relation_type_section(
            standard_relation_types, relations
        )

        # Process any non-standard relation types that were in the original section
        new_conexiones += self._build_relation_type_section(
            sorted(non_standard_types), relations
        )

        return new_conexiones

    def _build_relation_type_section(
        self, relation_types: List[str], relations: Dict[str, List[str]]
    ) -> str:
        """Build section content for a list of relation types."""
        section_content = ""

        for relation_type in relation_types:
            links = relations.get(relation_type, [])
            if links:
                link_strings = [f"[[{link}]]" for link in links]
                section_content += f"- {relation_type}: {', '.join(link_strings)}\n"
            else:
                section_content += f"- {relation_type}: \n"

        return section_content

    def _write_updated_content(
        self,
        file_path: str,
        content: str,
        conexiones_bounds: tuple[int, int],
        new_conexiones: str,
    ) -> None:
        """Write the updated content back to the file."""
        new_content = (
            content[: conexiones_bounds[0]]
            + new_conexiones
            + content[conexiones_bounds[1] :]
        )

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(new_content)

    def validate_relation_consistency(
        self, concept_name: str, relations: Dict[str, List[str]]
    ) -> List[str]:
        """
        Validate relation consistency and return list of inconsistencies.

        This method checks for common relation inconsistencies such as
        self-connections and bidirectional conflicts. It returns a list
        of descriptive inconsistency messages.

        Args:
            concept_name: Name of the concept being validated
            relations: Dictionary mapping relation types to lists of concept names
                      Example: {"GENERALIZES": ["Deep Learning"], "PART_OF": ["AI"]}

        Returns:
            List of inconsistency description strings.
            Empty list if no inconsistencies are found.

        Note:
            Currently validates:
            - Self-connections (concept relating to itself)
            - Future: bidirectional relation conflicts
        """
        inconsistencies = []

        # Check for self-connections
        for relation_type, links in relations.items():
            if concept_name in links:
                inconsistencies.append(
                    f"Self-connection found: {concept_name} {relation_type} {concept_name}"
                )

        # Check for bidirectional inconsistencies
        for relation_type, links in relations.items():
            if relation_type not in RELATION_MAP:
                continue

            forward_type, reverse_type = RELATION_MAP[relation_type]

            # Check if any of the linked concepts have the reverse relation back to this concept
            # This would be checked when processing the target concepts
            # For now, we'll just note that this needs to be checked during full sync

        return inconsistencies

    async def sync_zettels_to_db(self) -> SyncResult:
        """
        Sync all Zettels from Obsidian to the database using a two-phase approach.

        This method implements a comprehensive sync process that:
        1. Creates/updates all concept entities in Neo4j
        2. Parses and creates concept relations from Conexiones sections
        3. Updates Obsidian files with enriched frontmatter and relations
        4. Validates and cleans up relation inconsistencies

        The two-phase approach ensures that all concepts exist before
        creating relations, preventing orphaned relationship references.

        Returns:
            SyncResult containing comprehensive sync statistics and error information

        Note:
            This method will:
            - Create bidirectional relations (A->B and B->A)
            - Update frontmatter with UUID-based relations
            - Enrich Conexiones sections with missing reverse relations
            - Track missing concepts and broken notes
            - Remove self-connections and report inconsistencies
        """
        # Validate LLM service is available - required for summary generation
        if not self.llm_service:
            raise RuntimeError(
                "LLM service is required for Zettel sync. Summaries must be LLM-generated."
            )

        zettel_files = self.find_zettel_files()
        result = self._initialize_sync_result(zettel_files)

        self.logger.info(f"Found {len(zettel_files)} Zettel files to sync")

        # Phase 1: Create/Update all concepts and collect relation data
        concept_data, all_concept_names = await self._process_zettel_files(
            zettel_files, result
        )

        self.logger.info(
            f"Phase 1 completed: {result.created} created, {result.updated} updated, {result.unchanged} unchanged, {result.errors} errors"
        )

        # Phase 2: Create relations
        await self._create_concept_relations(concept_data, all_concept_names, result)

        # Phase 3: Clean up orphaned relations
        await self._cleanup_orphaned_relations(concept_data, result)

        self._log_sync_completion(result)
        return result

    def _initialize_sync_result(self, zettel_files: List[str]) -> SyncResult:
        """Initialize the SyncResult object with file count and empty statistics."""
        return SyncResult(
            total_files=len(zettel_files),
            parsed=0,
            created=0,
            updated=0,
            unchanged=0,
            errors=0,
            errors_list=[],
            missing_concepts=[],
            broken_notes=[],
            relations_created=0,
            relations_updated=0,
            self_connections_removed=0,
            inconsistent_relations=[],
        )

    async def _process_zettel_files(
        self, zettel_files: List[str], result: SyncResult
    ) -> tuple[Dict[str, Dict[str, Any]], set[str]]:
        """Process all Zettel files and return concept data and names."""
        concept_data: Dict[str, Dict[str, Any]] = (
            {}
        )  # concept_name -> {uuid, file_path, relations}
        all_concept_names: set[str] = set()

        for file_path in zettel_files:
            try:
                concept_uuid, relations, concept_name = (
                    await self._process_single_zettel_file(file_path, result)
                )
                if concept_uuid and concept_name:
                    concept_data[concept_name] = {
                        "uuid": concept_uuid,
                        "file_path": file_path,
                        "relations": relations,
                    }
                    all_concept_names.add(concept_name)
            except Exception as e:
                result.errors += 1
                result.errors_list.append(f"Error processing {file_path}: {str(e)}")
                self.logger.error(f"Error processing {file_path}: {e}")

        return concept_data, all_concept_names

    async def _process_single_zettel_file(
        self, file_path: str, result: SyncResult
    ) -> tuple[str | None, Dict, str | None]:
        """Process a single Zettel file and return concept UUID, relations, and concept name."""
        # Parse Zettel content
        zettel_data = self.parse_zettel_content(file_path)
        if not zettel_data:
            result.errors += 1
            result.errors_list.append(f"Failed to parse {file_path}")
            return None, {}, None

        result.parsed += 1
        concept_name = zettel_data["name"]

        # Check for corrupted frontmatter
        try:
            frontmatter = zettel_data["frontmatter"]
        except (KeyError, TypeError):
            result.broken_notes.append(file_path)
            result.errors += 1
            result.errors_list.append(f"Corrupted frontmatter in {file_path}")
            return None, {}, None

        # Check if concept already exists
        existing_concept = await self._find_existing_concept(frontmatter, concept_name)

        # Parse relations from Conexiones section
        conexiones_content = zettel_data.get("connections", "")
        relations = self.parse_conexiones_section(conexiones_content)
        self.logger.debug(f"Parsed relations for {concept_name}: {relations}")

        # Update zettel_data with parsed connections for prompt usage
        zettel_data["connections"] = relations

        if existing_concept:
            concept_uuid = await self._handle_existing_concept(
                existing_concept, zettel_data, result
            )
        else:
            concept_uuid = await self._create_new_concept(zettel_data, result)

        return concept_uuid, relations, concept_name

    async def _find_existing_concept(self, frontmatter: Dict, concept_name: str):
        """Find existing concept by UUID or name."""
        if frontmatter.get(ENTITY_ID_KEY):
            return self.concept_repository.find_by_uuid(frontmatter.get(ENTITY_ID_KEY))
        else:
            return await self.concept_repository.find_concept_by_name_or_title(
                concept_name
            )

    async def _handle_existing_concept(
        self, existing_concept, zettel_data: Dict, result: SyncResult
    ) -> str:
        """Handle updating an existing concept."""
        # Check if core content has changed
        changes = self._compare_concept_content(existing_concept, zettel_data)

        if changes["has_changes"]:
            self.logger.info(
                f"Concept {zettel_data['name']} has changes in fields: {changes['changed_fields']}"
            )
            await self._update_existing_concept(
                existing_concept, zettel_data, changes, result
            )
        else:
            self.logger.debug(
                f"Concept {zettel_data['name']} unchanged, skipping update"
            )
            result.unchanged += 1
            self._update_frontmatter_with_existing_concept(
                existing_concept, zettel_data["name"]
            )

        return existing_concept.uuid

    async def _update_existing_concept(
        self, existing_concept, zettel_data: Dict, changes: Dict, result: SyncResult
    ) -> None:
        """Update an existing concept with new content and summaries."""
        self.logger.debug(f"Regenerating LLM summaries for {zettel_data['name']}")

        try:
            prompt = GenerateZettelSummaryPrompt()
            response = await self.llm_service.generate(
                prompt=prompt.user_prompt(zettel_data),
                system_prompt=prompt.system_prompt(),
                response_model=prompt.response_model(),
            )

            # Update the concept with new content and summaries
            updates = changes["updates"].copy()
            updates["summary_short"] = response.summary_short
            updates["summary"] = response.summary

            # Update in database
            await self.concept_repository.update(existing_concept.uuid, updates)
            result.updated += 1
            self.logger.info(f"Updated concept: {zettel_data['name']}")

            # Update Obsidian frontmatter with entity info
            self._update_frontmatter_with_new_summaries(
                existing_concept.uuid, zettel_data["name"], response
            )

        except Exception as e:
            self.logger.error(f"Failed to update concept {zettel_data['name']}: {e}")
            raise RuntimeError(f"Failed to update concept {zettel_data['name']}: {e}")

    def _update_frontmatter_with_existing_concept(
        self, existing_concept, concept_name: str
    ) -> None:
        """Update frontmatter with existing concept data."""
        self.update_link(
            concept_name,
            {
                ENTITY_ID_KEY: existing_concept.uuid,
                ENTITY_TYPE_KEY: "Concept",
                SHORT_SUMMARY_KEY: existing_concept.summary_short,
                SUMMARY_KEY: existing_concept.summary,
            },
        )

    def _update_frontmatter_with_new_summaries(
        self, concept_uuid: str, concept_name: str, response
    ) -> None:
        """Update frontmatter with new LLM-generated summaries."""
        self.update_link(
            concept_name,
            {
                ENTITY_ID_KEY: concept_uuid,
                ENTITY_TYPE_KEY: "Concept",
                SHORT_SUMMARY_KEY: response.summary_short,
                SUMMARY_KEY: response.summary,
            },
        )

    async def _create_new_concept(self, zettel_data: Dict, result: SyncResult) -> str:
        """Create a new concept with LLM-generated summaries."""
        from minerva_models import Concept

        # Generate summaries using LLM (required - no fallbacks)
        self.logger.debug(f"Generating LLM summaries for {zettel_data['name']}")

        try:
            prompt = GenerateZettelSummaryPrompt()
            response = await self.llm_service.generate(
                prompt=prompt.user_prompt(zettel_data),
                system_prompt=prompt.system_prompt(),
                response_model=prompt.response_model(),
            )
            zettel_data["summary_short"] = response.summary_short
            zettel_data["summary"] = response.summary
            self.logger.debug(f"Generated summaries for {zettel_data['name']}")
        except Exception as e:
            self.logger.error(
                f"Failed to generate summaries for {zettel_data['name']}: {e}"
            )
            raise RuntimeError(
                f"LLM summary generation failed for {zettel_data['name']}: {e}"
            )

        concept = Concept(
            name=zettel_data["name"],
            title=zettel_data["title"],
            concept=zettel_data["concept"],
            analysis=zettel_data["analysis"],
            source=zettel_data["source"],
            summary_short=zettel_data["summary_short"],
            summary=zettel_data["summary"],
        )

        concept_uuid = await self.concept_repository.create(concept)
        result.created += 1
        self.logger.info(
            f"Created concept: {zettel_data['name']} (UUID: {concept_uuid})"
        )

        # Update Obsidian frontmatter with entity info
        self.update_link(
            zettel_data["name"],
            {
                ENTITY_ID_KEY: concept_uuid,
                ENTITY_TYPE_KEY: "Concept",
                SHORT_SUMMARY_KEY: zettel_data["summary_short"],
                SUMMARY_KEY: zettel_data["summary"],
            },
        )

        return concept_uuid

    def _log_sync_completion(self, result: SyncResult) -> None:
        """Log the final sync completion statistics."""
        self.logger.info(
            f"Zettel sync completed: {result.created} created, {result.updated} updated, {result.unchanged} unchanged, {result.errors} errors"
        )
        self.logger.info(
            f"Relations: {result.relations_created} created, {result.relations_updated} updated, {result.relations_deleted} deleted"
        )
        self.logger.info(f"Missing concepts: {len(result.missing_concepts)}")
        self.logger.info(f"Broken notes: {len(result.broken_notes)}")

    async def _create_concept_relations(
        self,
        concept_data: Dict[str, Dict[str, Any]],
        all_concept_names: set,
        result: SyncResult,
    ) -> None:
        """
        Phase 2: Create concept relations in Neo4j and update Obsidian files.

        This method processes all concept relations discovered in Phase 1,
        creates bidirectional edges in Neo4j, and updates Obsidian files
        with enriched frontmatter and Conexiones sections.

        Args:
            concept_repository: ConceptRepository instance for database operations
            concept_data: Dictionary mapping concept names to their data
                         Format: {concept_name: {uuid, file_path, relations}}
            all_concept_names: Set of all concept names that exist in the system
            result: SyncResult object to update with relation statistics

        Note:
            This method creates bidirectional relations and tracks:
            - Missing concepts (referenced but don't exist)
            - Self-connections (removed and counted)
            - Relation creation success/failure
        """
        self.logger.info("Starting Phase 2: Creating concept relations")
        self.logger.info(f"Processing {len(concept_data)} concepts with relations")
        self.logger.debug(f"Available concept names: {sorted(all_concept_names)}")

        # Clear existing concept_relations from frontmatter to prevent accumulation
        await self._clear_existing_relations(concept_data)

        # Track bidirectional relations to avoid duplicates
        processed_relations: Set[str] = set()
        total_relations_found = 0
        relations_processed = 0

        # Process each concept
        for concept_name, data in concept_data.items():
            concept_result = await self._process_concept_relations(
                concept_name,
                data,
                all_concept_names,
                concept_data,
                processed_relations,
                result,
            )
            total_relations_found += concept_result["total_relations"]
            relations_processed += concept_result["processed_relations"]

        self.logger.info(
            f"Phase 2 completed: {relations_processed} relations processed out of {total_relations_found} found"
        )
        self.logger.info(
            f"Relations created: {result.relations_created}, Errors: {result.errors}"
        )
        self.logger.info(
            f"Missing concepts: {len(result.missing_concepts)}, Self-connections removed: {result.self_connections_removed}"
        )

    async def _clear_existing_relations(self, concept_data: Dict[str, Dict[str, Any]]):
        """Clear existing concept_relations from frontmatter to prevent accumulation."""
        self.logger.info("Clearing existing concept_relations from frontmatter")
        for concept_name in concept_data.keys():
            self.update_link(concept_name, {CONCEPT_RELATIONS_KEY: None})

    async def _process_concept_relations(
        self,
        concept_name: str,
        data: Dict[str, Any],
        all_concept_names: set,
        concept_data: Dict[str, Dict[str, Any]],
        processed_relations: set,
        result: SyncResult,
    ) -> Dict[str, int]:
        """Process relations for a single concept."""
        concept_uuid = data["uuid"]
        file_path = data["file_path"]
        relations = data["relations"]

        self.logger.debug(f"Processing concept: {concept_name} (UUID: {concept_uuid})")
        self.logger.debug(f"Relations for {concept_name}: {relations}")

        if not relations:
            self.logger.debug(f"No relations found for {concept_name}, skipping")
            return {"total_relations": 0, "processed_relations": 0}

        # Count total relations for this concept
        concept_relation_count = sum(len(links) for links in relations.values())
        self.logger.debug(
            f"Found {concept_relation_count} relations for {concept_name}"
        )

        # Validate relations for this concept
        inconsistencies = self.validate_relation_consistency(concept_name, relations)
        if inconsistencies:
            self.logger.warning(
                f"Found {len(inconsistencies)} inconsistencies for {concept_name}: {inconsistencies}"
            )
            result.inconsistent_relations.extend(
                [f"{concept_name}: {inc}" for inc in inconsistencies]
            )
            return {"total_relations": concept_relation_count, "processed_relations": 0}

        # Process each relation type
        processed_relations_count = 0
        for relation_type, target_links in relations.items():
            processed_relations_count += await self._process_relation_type(
                concept_name,
                concept_uuid,
                file_path,
                relation_type,
                target_links,
                all_concept_names,
                concept_data,
                processed_relations,
                result,
            )

        return {
            "total_relations": concept_relation_count,
            "processed_relations": processed_relations_count,
        }

    async def _process_relation_type(
        self,
        concept_name: str,
        concept_uuid: str,
        file_path: str,
        relation_type: str,
        target_links: List[str],
        all_concept_names: set,
        concept_data: Dict[str, Dict[str, Any]],
        processed_relations: set,
        result: SyncResult,
    ) -> int:
        """Process a single relation type for a concept."""
        self.logger.debug(
            f"Processing relation type '{relation_type}' for {concept_name} with {len(target_links)} targets"
        )

        if relation_type not in RELATION_MAP:
            self.logger.warning(
                f"Unknown relation type '{relation_type}' for {concept_name}, skipping"
            )
            return 0

        forward_type, reverse_type = RELATION_MAP[relation_type]
        self.logger.debug(
            f"Mapping {relation_type} -> forward: {forward_type}, reverse: {reverse_type}"
        )

        processed_count = 0
        for target_name in target_links:
            if await self._process_single_relation(
                concept_name,
                concept_uuid,
                file_path,
                relation_type,
                target_name,
                forward_type,
                reverse_type,
                all_concept_names,
                concept_data,
                processed_relations,
                result,
            ):
                processed_count += 1

        return processed_count

    async def _process_single_relation(
        self,
        concept_name: str,
        concept_uuid: str,
        file_path: str,
        relation_type: str,
        target_name: str,
        forward_type: str,
        reverse_type: str,
        all_concept_names: set,
        concept_data: Dict[str, Dict[str, Any]],
        processed_relations: set,
        result: SyncResult,
    ) -> bool:
        """Process a single relation between two concepts."""
        self.logger.debug(
            f"Processing relation: {concept_name} {relation_type} {target_name}"
        )

        # Skip self-connections
        if target_name == concept_name:
            self.logger.debug(
                f"Skipping self-connection: {concept_name} {relation_type} {concept_name}"
            )
            result.self_connections_removed += 1
            return False

        # Check if target concept exists
        if target_name not in all_concept_names:
            self.logger.warning(
                f"Target concept '{target_name}' not found in available concepts"
            )
            if target_name not in result.missing_concepts:
                result.missing_concepts.append(target_name)
                self.logger.info(f"Added '{target_name}' to missing concepts list")
            return False

        # Get target concept UUID
        target_data = concept_data.get(target_name)
        if not target_data:
            self.logger.warning(
                f"Target data not found for '{target_name}' in concept_data"
            )
            return False

        target_uuid = target_data["uuid"]
        self.logger.debug(f"Target concept found: {target_name} (UUID: {target_uuid})")

        # Create relation key to avoid duplicates
        relation_key = tuple(sorted([concept_uuid, target_uuid]) + [forward_type])
        if relation_key in processed_relations:
            self.logger.debug(
                f"Relation already processed, skipping: {concept_name} {relation_type} {target_name}"
            )
            return False
        processed_relations.add(relation_key)
        self.logger.debug(f"Added relation key to processed set: {relation_key}")

        try:
            await self._create_bidirectional_relation(
                concept_name,
                concept_uuid,
                target_name,
                target_uuid,
                relation_type,
                forward_type,
                reverse_type,
                file_path,
                target_data,
                result,
            )
            return True

        except Exception as e:
            result.errors += 1
            result.errors_list.append(
                f"Error creating relation {concept_name} {relation_type} {target_name}: {e}"
            )
            self.logger.error(
                f"Error creating relation {concept_name} {relation_type} {target_name}: {e}"
            )
            import traceback

            self.logger.error(f"Traceback: {traceback.format_exc()}")
            return False

    async def _create_bidirectional_relation(
        self,
        concept_name: str,
        concept_uuid: str,
        target_name: str,
        target_uuid: str,
        relation_type: str,
        forward_type: str,
        reverse_type: str,
        file_path: str,
        target_data: Dict[str, Any],
        result: SyncResult,
    ):
        """Create bidirectional relation and update metadata."""
        self.logger.info(
            f"Creating relation: {concept_name} {forward_type} {target_name}"
        )

        # Create forward relation
        forward_success = await self._create_concept_edge(
            concept_uuid, target_uuid, forward_type
        )
        if forward_success:
            result.relations_created += 1
            self.logger.debug(
                f"Successfully created forward relation: {concept_name} {forward_type} {target_name}"
            )
        else:
            self.logger.error(
                f"Failed to create forward relation: {concept_name} {forward_type} {target_name}"
            )

        # Create reverse relation
        reverse_success = await self._create_concept_edge(
            target_uuid, concept_uuid, reverse_type
        )
        if reverse_success:
            result.relations_created += 1
            self.logger.debug(
                f"Successfully created reverse relation: {target_name} {reverse_type} {concept_name}"
            )
        else:
            self.logger.error(
                f"Failed to create reverse relation: {target_name} {reverse_type} {concept_name}"
            )

        # Update metadata for both concepts
        await self._update_relation_metadata(
            concept_name,
            concept_uuid,
            target_name,
            target_uuid,
            relation_type,
            reverse_type,
            file_path,
            target_data,
        )

        self.logger.info(
            f"Successfully processed relation: {concept_name} {relation_type} {target_name}"
        )

    async def _update_relation_metadata(
        self,
        concept_name: str,
        concept_uuid: str,
        target_name: str,
        target_uuid: str,
        relation_type: str,
        reverse_type: str,
        file_path: str,
        target_data: Dict[str, Any],
    ):
        """Update frontmatter and Conexiones sections for both concepts."""
        # Update frontmatter for both concepts
        self.logger.debug(f"Updating frontmatter for {concept_name}")
        self._update_concept_relations_frontmatter(
            concept_name,
            target_name,
            relation_type,
            concept_uuid,
            target_uuid,
        )

        self.logger.debug(f"Updating frontmatter for {target_name}")
        self._update_concept_relations_frontmatter(
            target_name,
            concept_name,
            reverse_type,
            target_uuid,
            concept_uuid,
        )

        # Update Conexiones sections
        self.logger.debug(f"Updating Conexiones section for {concept_name}")
        self._update_conexiones_with_relation(
            concept_name, target_name, relation_type, file_path
        )

        self.logger.debug(f"Updating Conexiones section for {target_name}")
        self._update_conexiones_with_relation(
            target_name,
            concept_name,
            reverse_type,
            target_data["file_path"],
        )

    async def _create_concept_edge(
        self, source_uuid: str, target_uuid: str, relation_type: str
    ) -> bool:
        """
        Create a concept relation edge in Neo4j.

        This is a wrapper method that delegates to the concept repository's
        create_concept_relation method.

        Args:
            source_uuid: UUID of the source concept
            target_uuid: UUID of the target concept
            relation_type: Type of relation to create (e.g., "GENERALIZES", "PART_OF")

        Returns:
            True if the relation was created successfully, False otherwise
        """
        self.logger.debug(
            f"Creating edge: {source_uuid} -[{relation_type}]-> {target_uuid}"
        )
        try:
            result = await self.concept_repository.create_concept_relation(
                source_uuid, target_uuid, relation_type
            )
            self.logger.debug(f"Edge creation result: {result}")
            return result
        except Exception as e:
            self.logger.error(f"Exception in _create_concept_edge: {e}")
            import traceback

            self.logger.error(f"Traceback: {traceback.format_exc()}")
            return False

    def _update_concept_relations_frontmatter(
        self,
        concept_name: str,
        target_name: str,
        relation_type: str,
        concept_uuid: str,
        target_uuid: str,
    ) -> None:
        """
        Update frontmatter with concept relations.

        This method updates the YAML frontmatter of a concept file to include
        the UUID-based relation information. It reads the current frontmatter,
        adds the relation to the concept_relations section, and updates the file.

        Args:
            concept_name: Name of the concept whose frontmatter to update
            target_name: Name of the target concept (for logging)
            relation_type: Type of relation (e.g., "GENERALIZES", "PART_OF")
            concept_uuid: UUID of the source concept
            target_uuid: UUID of the target concept to add to relations

        Note:
            If the concept file is not found, the method will log an error
            but will not raise an exception.
        """
        try:
            # Find the file for this concept
            cache = self._build_cache()
            file_path = cache.get(concept_name)
            if not file_path:
                self.logger.warning(f"Could not find file for concept: {concept_name}")
                return

            # Read current frontmatter
            frontmatter = self._parse_yaml_frontmatter(file_path)
            if not frontmatter:
                frontmatter = {}

            # Initialize concept_relations if not exists
            if CONCEPT_RELATIONS_KEY not in frontmatter:
                frontmatter[CONCEPT_RELATIONS_KEY] = {}

            # Add the relation
            if relation_type not in frontmatter[CONCEPT_RELATIONS_KEY]:
                frontmatter[CONCEPT_RELATIONS_KEY][relation_type] = []

            # Add target UUID if not already present
            if target_uuid not in frontmatter[CONCEPT_RELATIONS_KEY][relation_type]:
                frontmatter[CONCEPT_RELATIONS_KEY][relation_type].append(target_uuid)

            # Update the file
            self.update_link(concept_name, frontmatter)

        except Exception as e:
            self.logger.error(f"Error updating frontmatter for {concept_name}: {e}")

    def _update_conexiones_with_relation(
        self, concept_name: str, target_name: str, relation_type: str, file_path: str
    ) -> None:
        """
        Update Conexiones section with a new relation.

        This method adds a new relation to the Conexiones section of a concept file.
        It uses the update_conexiones_section method to merge the new relation
        with existing relations while preserving user formatting.

        Args:
            concept_name: Name of the concept (for logging)
            target_name: Name of the target concept to add
            relation_type: Type of relation (e.g., "GENERALIZES", "PART_OF")
            file_path: Path to the Obsidian file to update

        Note:
            If the update fails, the method will log an error but will not
            raise an exception.
        """
        try:
            # Create the relation dictionary
            relations: Dict[str, List[str]] = {relation_type: [target_name]}

            # Use the existing update_conexiones_section method
            success = self.update_conexiones_section(file_path, relations)
            if not success:
                self.logger.warning(
                    f"Failed to update Conexiones section for {concept_name}"
                )

        except Exception as e:
            self.logger.error(f"Error updating Conexiones for {concept_name}: {e}")

    def _get_frontmatter_relations(self, concept_name: str) -> Dict[str, List[str]]:
        """
        Get relations from frontmatter (already has UUIDs).

        Args:
            concept_name: Name of the concept

        Returns:
            Dictionary mapping relation types to lists of target UUIDs
        """
        try:
            # Use the existing cache system for efficiency
            cache = self._build_cache()
            file_path = cache.get(concept_name)
            if not file_path:
                return {}

            frontmatter = self._parse_yaml_frontmatter(file_path)
            if not frontmatter:
                return {}

            return frontmatter.get("concept_relations", {})

        except Exception as e:
            self.logger.error(f"Error reading frontmatter for {concept_name}: {e}")
            return {}

    def _find_orphaned_relations(
        self,
        db_relations: List[Dict[str, Any]],
        frontmatter_relations: Dict[str, List[str]],
    ) -> List[Dict[str, Any]]:
        """
        Find relations that exist in DB but not in frontmatter.

        Args:
            db_relations: List of database relations from get_concept_relations
            frontmatter_relations: Dictionary of frontmatter relations with UUIDs

        Returns:
            List of orphaned relations to delete
        """
        orphaned = []

        # Convert frontmatter to a set for fast lookup
        frontmatter_set = set()
        for relation_type, target_uuids in frontmatter_relations.items():
            for target_uuid in target_uuids:
                frontmatter_set.add((target_uuid, relation_type))

        # Check each database relation
        for db_rel in db_relations:
            target_uuid = db_rel["target_uuid"]
            relation_type = db_rel["relation_type"]

            if (target_uuid, relation_type) not in frontmatter_set:
                orphaned.append(db_rel)
                self.logger.debug(
                    f"Found orphaned relation: {relation_type} -> {target_uuid}"
                )

        return orphaned

    def _get_reverse_relation_type(self, relation_type: str) -> str:
        """
        Get the reverse relation type for bidirectional cleanup.

        Args:
            relation_type: Forward relation type

        Returns:
            Reverse relation type
        """
        for obsidian_type, (forward, reverse) in RELATION_MAP.items():
            if forward == relation_type:
                return reverse
        return relation_type  # For symmetric relations

    async def _delete_orphaned_relations(
        self, concept_uuid: str, orphaned_relations: List[Dict[str, Any]]
    ) -> int:
        """
        Delete orphaned relations from database.

        Args:
            concept_uuid: UUID of the source concept
            orphaned_relations: List of relations to delete

        Returns:
            Number of relations successfully deleted
        """
        deleted_count = 0

        for orphan in orphaned_relations:
            target_uuid = orphan["target_uuid"]
            relation_type = orphan["relation_type"]

            try:
                # Get reverse relation type
                reverse_type = self._get_reverse_relation_type(relation_type)

                # Delete forward relation
                success1 = await self.concept_repository.delete_concept_relation(
                    concept_uuid, target_uuid, relation_type
                )

                # Delete reverse relation
                success2 = await self.concept_repository.delete_concept_relation(
                    target_uuid, concept_uuid, reverse_type
                )

                if success1 and success2:
                    deleted_count += 1
                    self.logger.info(
                        f"Deleted orphaned relation: {concept_uuid} -[:{relation_type}]-> {target_uuid}"
                    )
                else:
                    self.logger.warning(
                        f"Failed to delete orphaned relation: {concept_uuid} -[:{relation_type}]-> {target_uuid}"
                    )

            except Exception as e:
                self.logger.error(
                    f"Error deleting orphaned relation {concept_uuid} -[:{relation_type}]-> {target_uuid}: {e}"
                )

        return deleted_count

    async def _cleanup_orphaned_relations(
        self, concept_data: Dict[str, Dict[str, Any]], result: SyncResult
    ) -> None:
        """
        Clean up relations that exist in DB but not in frontmatter.

        This method runs after all relations have been created and frontmatter
        has been updated, ensuring the database reflects the current state.

        Args:
            concept_repository: ConceptRepository instance for database operations
            concept_data: Dictionary mapping concept names to their data
            result: SyncResult object to update with cleanup statistics
        """
        self.logger.info("Starting Phase 3: Cleaning up orphaned relations")

        total_orphaned = 0

        for concept_name, concept_data in concept_data.items():
            concept_uuid: str = str(concept_data["uuid"])

            try:
                # Get current frontmatter relations (with UUIDs)
                frontmatter_relations = self._get_frontmatter_relations(concept_name)

                # Get current database relations
                db_relations = await self.concept_repository.get_concept_relations(
                    concept_uuid
                )

                if not db_relations:
                    self.logger.debug(f"No database relations found for {concept_name}")
                    continue

                # Find orphaned relations
                orphaned = self._find_orphaned_relations(
                    db_relations, frontmatter_relations
                )

                if orphaned:
                    self.logger.info(
                        f"Found {len(orphaned)} orphaned relations for {concept_name}"
                    )

                    # Delete orphaned relations
                    deleted_count = await self._delete_orphaned_relations(
                        concept_uuid, orphaned
                    )

                    total_orphaned += deleted_count
                    result.relations_deleted += deleted_count

                    # Log details for debugging
                    for orphan in orphaned:
                        result.errors_list.append(
                            f"Deleted orphaned relation: {concept_name} -[:{orphan['relation_type']}]-> {orphan['target_uuid']}"
                        )
                else:
                    self.logger.debug(f"No orphaned relations found for {concept_name}")

            except Exception as e:
                self.logger.error(
                    f"Error cleaning up relations for {concept_name}: {e}"
                )
                result.errors += 1
                result.errors_list.append(
                    f"Error cleaning up relations for {concept_name}: {e}"
                )

        self.logger.info(
            f"Phase 3 complete: Deleted {total_orphaned} orphaned relations"
        )
