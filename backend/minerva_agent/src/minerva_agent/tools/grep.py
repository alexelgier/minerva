"""Content search (grep) in the Obsidian vault (read-only)."""

import re
from pathlib import Path

from langchain_core.tools import tool

from minerva_agent.tools._vault import resolve_vault_path


def create_grep_tool(vault_path: str):
    """Create a grep tool scoped to the given vault path."""

    @tool
    def grep(
        pattern: str,
        directory: str = ".",
        file_pattern: str = "*.md",
        max_results: int = 50,
    ) -> str:
        """Search for a text pattern in markdown files in the Obsidian vault. Pattern is a regex. Optional directory restricts search (default: vault root). file_pattern is a glob (default: *.md). Returns up to max_results matches (default 50)."""
        try:
            base = resolve_vault_path(vault_path, directory)
            if not base.is_dir():
                return f"Error: not a directory or not found: {directory}"
            vault_root = Path(vault_path).resolve()
            regex = re.compile(pattern, re.IGNORECASE)
            count = 0
            lines_out = []
            for path in sorted(base.rglob(file_pattern)):
                if not path.is_file():
                    continue
                try:
                    rel = path.relative_to(vault_root)
                    rel_str = str(rel).replace("\\", "/")
                except ValueError:
                    continue
                try:
                    text = path.read_text(encoding="utf-8", errors="replace")
                except OSError:
                    continue
                for i, line in enumerate(text.splitlines(), 1):
                    if regex.search(line):
                        lines_out.append(f"{rel_str}:{i}: {line.strip()[:200]}")
                        count += 1
                        if count >= max_results:
                            break
                if count >= max_results:
                    break
            if not lines_out:
                return "(no matches)"
            return "\n".join(lines_out)
        except ValueError as e:
            return f"Error: {e}"
        except re.error as e:
            return f"Error: invalid regex: {e}"
        except OSError as e:
            return f"Error: {e}"

    grep.name = "grep"
    return grep

