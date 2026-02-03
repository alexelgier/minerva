"""List directory contents in the Obsidian vault (read-only)."""

from pathlib import Path

from langchain_core.tools import tool

from minerva_agent.tools._vault import resolve_vault_path


def create_list_dir_tool(vault_path: str):
    """Create a list_dir tool scoped to the given vault path."""

    @tool
    def list_dir(directory_path: str = ".") -> str:
        """List files and folders in a directory in the Obsidian vault. Use a path relative to the vault root (e.g. "01 - Inbox" or "." for the vault root)."""
        try:
            full_path = resolve_vault_path(vault_path, directory_path)
            if not full_path.is_dir():
                return f"Error: not a directory or not found: {directory_path}"
            entries = sorted(full_path.iterdir(), key=lambda p: (not p.is_dir(), p.name.lower()))
            lines = []
            for p in entries:
                name = p.name
                if p.is_dir():
                    lines.append(f"  [dir]  {name}/")
                else:
                    lines.append(f"  [file] {name}")
            return "\n".join(lines) if lines else "(empty)"
        except ValueError as e:
            return f"Error: {e}"
        except OSError as e:
            return f"Error listing directory: {e}"

    list_dir.name = "list_dir"
    return list_dir

