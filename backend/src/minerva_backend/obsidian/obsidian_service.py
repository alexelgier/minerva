import os
from typing import Dict, Optional, Union, List, Any

import yaml


class ObsidianService:
    """Service for resolving Obsidian links and managing vault cache."""

    def __init__(self, vault_path: str = "D:\\yo"):
        self.vault_path = vault_path
        self._cache = None

    def _build_cache(self) -> Dict[str, str]:
        """Construye un caché de todas las notas en el vault, indexado por nombre de archivo."""
        if self._cache is not None:
            return self._cache

        print("Construyendo caché del vault...")
        self._cache = {}

        for root, dirs, files in os.walk(self.vault_path):
            for file in files:
                if file.endswith('.md'):
                    full_path = os.path.join(root, file)
                    nombre_archivo = file[:-3]  # Remove .md
                    self._cache[nombre_archivo] = full_path

                    # También almacenar por ruta relativa completa para casos disambiguados
                    rel_path = os.path.relpath(full_path, self.vault_path)
                    rel_path_key = rel_path.replace('\\', '/')[:-3]  # Normalizar y quitar .md
                    if rel_path_key != nombre_archivo:  # Solo si es diferente
                        self._cache[rel_path_key] = full_path

        print(f"Caché construido con {len(self._cache)} entradas\n")
        return self._cache

    def rebuild_cache(self) -> None:
        """Force rebuild of the vault cache."""
        self._cache = None
        self._build_cache()

    def _parse_yaml_frontmatter(self, file_path: str) -> Optional[Dict]:
        """Extrae el YAML frontmatter de un archivo markdown."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Check if file starts with frontmatter
            if not content.startswith('---'):
                return None

            # Find the end of frontmatter
            lines = content.split('\n')
            yaml_end = None
            for i, line in enumerate(lines[1:], 1):
                if line.strip() == '---':
                    yaml_end = i
                    break

            if yaml_end is None:
                return None

            # Extract YAML content
            yaml_content = '\n'.join(lines[1:yaml_end])
            return yaml.safe_load(yaml_content)

        except (yaml.YAMLError, IOError, UnicodeDecodeError):
            # Invalid YAML or file read error - skip
            return None

    def _normalize_aliases(self, aliases_value: Union[str, List[str], None]) -> Optional[List[str]]:
        """Normalizes the aliases field which can come in various formats."""
        if aliases_value is None:
            return None

        if isinstance(aliases_value, str):
            return [aliases_value]
        elif isinstance(aliases_value, list):
            return [str(alias) for alias in aliases_value]
        else:
            return None

    def resolve_link(self, link_text: str) -> Dict:
        """
        Resolves an Obsidian link to file path and entity metadata.

        Args:
            link_text: Raw link content, e.g.:
                - "Federico Demarchi"
                - "Federico Demarchi|Fede"
                - "05 - Personal/Proyectos/Música/Música|Música"

        Returns:
            {
                'file_path': str | None,
                'entity_name': str | None,  # The filename (note title)
                'entity_id': str | None,
                'entity_type': str | None,
                'aliases': list | None,
                'display_text': str  # The part after | or the whole thing
            }
        """
        # Ensure cache is built
        cache = self._build_cache()

        # Parse the link text
        if '|' in link_text:
            target, display_text = link_text.split('|', 1)
        else:
            target = link_text
            display_text = link_text

        # Initialize result
        result = {
            'file_path': None,
            'entity_name': None,
            'entity_long_name': target,
            'entity_id': None,
            'entity_type': None,
            'aliases': None,
            'display_text': display_text.strip(),
            'short_summary': None
        }

        # Look up in cache
        target = target.strip()

        # Always set entity_name from the target (the note title being referenced)
        if '/' in target:
            # For disambiguated paths, extract the actual note name (last part)
            result['entity_name'] = os.path.basename(target)
        else:
            # For simple cases, the target is the note name
            result['entity_name'] = target

        if target not in cache:
            return result

        file_path = cache[target]
        result['file_path'] = file_path

        # Parse frontmatter for entity metadata
        frontmatter = self._parse_yaml_frontmatter(file_path)
        if frontmatter:
            result['entity_id'] = frontmatter.get('entity_id')
            result['entity_type'] = frontmatter.get('entity_type')
            result['aliases'] = self._normalize_aliases(frontmatter.get('aliases'))
            result['short_summary'] = frontmatter.get('short_summary')

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
        cache = self._build_cache()

        # Parse the link text to get the target file
        if '|' in link_text:
            target, _ = link_text.split('|', 1)
        else:
            target = link_text
        target = target.strip()

        if target not in cache:
            return False

        file_path = cache[target]

        try:
            # Read original content
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Separate frontmatter and body
            existing_frontmatter = {}
            body = content
            if content.startswith('---'):
                lines = content.split('\n')
                yaml_end_index = -1
                # Start search from the second line
                for i, line in enumerate(lines[1:], 1):
                    if line.strip() == '---':
                        yaml_end_index = i
                        break

                if yaml_end_index > 0:
                    frontmatter_lines = lines[1:yaml_end_index]
                    frontmatter_str = '\n'.join(frontmatter_lines)
                    existing_frontmatter = yaml.safe_load(frontmatter_str) or {}
                    body = '\n'.join(lines[yaml_end_index + 1:])

            # Update with new metadata
            existing_frontmatter.update(metadata)

            # Clean up keys with None values
            updated_frontmatter = {k: v for k, v in existing_frontmatter.items() if v is not None}

            # Write back to file
            with open(file_path, 'w', encoding='utf-8') as f:
                if updated_frontmatter:
                    f.write('---\n')
                    yaml.dump(updated_frontmatter, f, allow_unicode=True, sort_keys=False)
                    f.write('---\n')
                f.write(body)

            return True
        except (IOError, yaml.YAMLError, UnicodeDecodeError):
            return False

    def get_cache_stats(self) -> Dict:
        """Returns statistics about the vault cache."""
        cache = self._build_cache()
        return {
            'total_notes': len(cache),
            'vault_path': self.vault_path,
            'cache_built': self._cache is not None
        }

    def find_note_by_name(self, name: str) -> Optional[str]:
        """Find a note file path by its name (without .md extension)."""
        cache = self._build_cache()
        return cache.get(name)
