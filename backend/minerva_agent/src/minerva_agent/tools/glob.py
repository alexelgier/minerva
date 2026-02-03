"""Glob pattern search in the Obsidian vault (read-only)."""

from pathlib import Path

from langchain_core.tools import tool

from minerva_agent.tools._vault import resolve_vault_path


def create_glob_tool(vault_path: str):
    """Create a glob tool scoped to the given vault path."""

    @tool
    def glob(pattern: str, directory: str = ".") -> str:
        """Find files matching a glob pattern in the Obsidian vault. Pattern is relative to the vault (e.g. "**/*.md" or "02 - Daily Notes/*.md"). Optional directory restricts search to a subdirectory."""
        try:
            base = resolve_vault_path(vault_path, directory)
            if not base.is_dir():
                return f"Error: not a directory or not found: {directory}"
            # Restrict to base so we don't escape vault
            matches = sorted(base.glob(pattern), key=lambda p: str(p))
            # Filter to files only and relativize to vault
            vault_root = Path(vault_path).resolve()
            results = []
            for p in matches:
                if p.is_file():
                    try:
                        rel = p.relative_to(vault_root)
                        results.append(str(rel).replace("\\", "/"))
                    except ValueError:
                        pass
            return "\n".join(results) if results else "(no matches)"
        except ValueError as e:
            return f"Error: {e}"
        except OSError as e:
            return f"Error: {e}"

    glob.name = "glob"
    return glob

