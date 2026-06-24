"""Safe filesystem reader for the vault.

All paths go through :func:`obsidian_mcp.utils.pathing.safe_resolve` so the
reader cannot be used to exfiltrate files outside the configured vault root.
"""

from __future__ import annotations

from collections.abc import Iterator
from datetime import UTC, datetime
from pathlib import Path

from obsidian_mcp.config import Settings
from obsidian_mcp.utils.errors import NoteNotFoundError, NoteTooLargeError
from obsidian_mcp.utils.pathing import is_hidden, safe_resolve
from obsidian_mcp.vault.models import Note
from obsidian_mcp.vault.parser import parse_note

_MD_SUFFIXES = {".md", ".markdown"}


class VaultReader:
    """Read-only view onto the vault filesystem."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    @property
    def root(self) -> Path:
        return self._settings.vault_path

    def _relpath(self, path: Path) -> str:
        return path.relative_to(self.root).as_posix()

    def iter_notes(self, folder: str | None = None) -> Iterator[Path]:
        """Yield absolute paths of every Markdown note under ``folder``.

        Hidden files and the ``.obsidian`` directory are skipped unless the
        ``include_hidden`` setting is enabled.
        """
        base = safe_resolve(self.root, folder) if folder else self.root
        if not base.exists() or not base.is_dir():
            return
        for path in sorted(base.rglob("*")):
            if not path.is_file():
                continue
            if path.suffix.lower() not in _MD_SUFFIXES:
                continue
            if not self._settings.include_hidden and is_hidden(path, self.root):
                continue
            yield path

    def read_note(self, relative_path: str) -> Note:
        """Read and parse a single note. Truncates oversized files."""
        path = safe_resolve(self.root, relative_path)
        if not path.exists() or not path.is_file():
            raise NoteNotFoundError(f"Note not found: {relative_path}")

        max_bytes = self._settings.max_file_kb * 1024
        size = path.stat().st_size
        truncated = False

        try:
            with path.open("rb") as fh:
                raw_bytes = fh.read(max_bytes + 1)
        except OSError as exc:
            raise NoteNotFoundError(f"Note not readable: {relative_path}") from exc

        if len(raw_bytes) > max_bytes:
            raw_bytes = raw_bytes[:max_bytes]
            truncated = True

        if b"\x00" in raw_bytes:
            raise NoteTooLargeError(
                f"Note appears to be binary, refusing to parse: {relative_path}"
            )

        text = raw_bytes.decode("utf-8", errors="replace")
        modified_at = datetime.fromtimestamp(path.stat().st_mtime, tz=UTC)

        return parse_note(
            relative_path=self._relpath(path),
            raw_text=text,
            size_bytes=size,
            modified_at=modified_at,
            truncated=truncated,
        )
