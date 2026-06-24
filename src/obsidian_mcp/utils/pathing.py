"""Sandboxed path resolution.

This module is the single chokepoint through which every caller-supplied path
must pass before the server touches the filesystem. Centralising the logic here
keeps the surface area for path-traversal and symlink-escape bugs minimal.

The contract is:

    safe_resolve(vault_root, user_input) -> Path

returns an absolute, fully-resolved path that is guaranteed to live inside
``vault_root``, or raises :class:`VaultPathError`.
"""

from __future__ import annotations

import unicodedata
from pathlib import Path, PurePosixPath

from obsidian_mcp.utils.errors import VaultPathError

_FORBIDDEN_SEGMENTS = {"..", ""}


def _normalise(raw: str) -> str:
    """NFC-normalise unicode and trim whitespace. Absolute paths are rejected."""
    normalised = unicodedata.normalize("NFC", raw).strip()
    if not normalised:
        raise VaultPathError("Path must not be empty")
    return normalised


def safe_resolve(vault_root: Path, user_path: str) -> Path:
    """Resolve ``user_path`` relative to ``vault_root`` with sandbox checks.

    The function is intentionally strict:

    * absolute paths are rejected (callers must supply vault-relative paths);
    * ``..`` segments are rejected before any filesystem touch;
    * the resolved path must remain inside ``vault_root`` after following
      any symlinks.

    Args:
        vault_root: Already-resolved vault root (see :class:`Settings`).
        user_path: Caller-supplied, vault-relative path.

    Returns:
        An absolute, symlink-resolved path inside ``vault_root``.

    Raises:
        VaultPathError: If the input is empty, absolute, contains ``..``,
            or escapes the sandbox.
    """
    normalised = _normalise(user_path)

    pure = PurePosixPath(normalised)
    if pure.is_absolute():
        raise VaultPathError(f"Absolute paths are not allowed: {user_path!r}")

    for part in pure.parts:
        if part in _FORBIDDEN_SEGMENTS:
            raise VaultPathError(f"Path segment {part!r} is not allowed: {user_path!r}")

    candidate = (vault_root / pure).resolve()
    try:
        candidate.relative_to(vault_root)
    except ValueError as exc:
        raise VaultPathError(f"Path escapes the vault sandbox: {user_path!r}") from exc

    return candidate


def is_hidden(path: Path, vault_root: Path) -> bool:
    """Return True if any path component (relative to vault root) is a dotfile."""
    try:
        rel = path.relative_to(vault_root)
    except ValueError:
        return True
    return any(part.startswith(".") for part in rel.parts)
