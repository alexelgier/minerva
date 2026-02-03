"""Vault path sandboxing for read-only tools."""

import os
from pathlib import Path


def resolve_vault_path(vault_path: str, relative_path: str) -> Path:
    """
    Resolve a path relative to the vault and ensure it stays inside the vault.
    Raises ValueError if the path escapes the vault (path traversal).
    """
    vault = Path(vault_path).resolve()
    combined = (vault / relative_path.lstrip("/")).resolve()
    if not str(combined).startswith(str(vault)):
        raise ValueError(
            f"Path escapes vault: {relative_path} resolves outside {vault_path}"
        )
    return combined


def ensure_in_vault(vault_path: str, absolute_path: Path) -> Path:
    """Ensure an absolute path is inside the vault. Raises ValueError if not."""
    vault = Path(vault_path).resolve()
    if not str(absolute_path).startswith(str(vault)):
        raise ValueError(
            f"Path is outside vault: {absolute_path} not under {vault_path}"
        )
    return absolute_path
