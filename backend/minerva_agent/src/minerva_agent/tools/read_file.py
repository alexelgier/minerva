"""Read file from the Obsidian vault (read-only)."""

from pathlib import Path

from langchain_core.tools import tool

from minerva_agent.tools._vault import resolve_vault_path


def create_read_file_tool(vault_path: str):
    """Create a read_file tool scoped to the given vault path."""

    @tool
    def read_file(file_path: str, start_line: int | None = None, end_line: int | None = None) -> str:
        """Read a file from the Obsidian vault. Use a path relative to the vault root (e.g. "02 - Daily Notes/2025-01-15.md"). Optionally specify start_line and end_line (1-based) to read a range."""
        try:
            full_path = resolve_vault_path(vault_path, file_path)
            if not full_path.is_file():
                return f"Error: not a file or not found: {file_path}"
            text = full_path.read_text(encoding="utf-8", errors="replace")
            if start_line is not None or end_line is not None:
                lines = text.splitlines()
                start = (start_line or 1) - 1
                end = end_line if end_line is not None else len(lines)
                start = max(0, start)
                end = min(len(lines), end)
                if start >= end:
                    return ""
                return "\n".join(lines[start:end])
            return text
        except ValueError as e:
            return f"Error: {e}"
        except OSError as e:
            return f"Error reading file: {e}"

    read_file.name = "read_file"
    return read_file
