"""Custom exceptions surfaced to MCP clients as structured tool errors.

Keeping these as a small hierarchy lets us:
* match on a single base type at the server boundary;
* avoid leaking Python internals (``FileNotFoundError`` paths, tracebacks);
* attach a stable error code that clients can branch on.
"""

from __future__ import annotations


class VaultError(Exception):
    """Base class for all expected, user-facing vault errors."""

    code: str = "vault_error"


class VaultPathError(VaultError):
    """Raised when a requested path escapes the vault sandbox or is invalid."""

    code = "invalid_path"


class NoteNotFoundError(VaultError):
    """Raised when a requested note does not exist."""

    code = "note_not_found"


class NoteTooLargeError(VaultError):
    """Raised when a note exceeds the configured maximum size."""

    code = "note_too_large"


class ReadOnlyError(VaultError):
    """Raised when a write tool is invoked while the server is read-only."""

    code = "read_only"


class NoteAlreadyExistsError(VaultError):
    """Raised when ``create_note`` would overwrite an existing file."""

    code = "note_already_exists"
