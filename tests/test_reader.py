"""VaultReader integration tests."""

from __future__ import annotations

from pathlib import Path

import pytest

from obsidian_mcp.config import Settings
from obsidian_mcp.utils.errors import NoteNotFoundError, NoteTooLargeError, VaultPathError
from obsidian_mcp.vault.reader import VaultReader


def test_iter_notes_lists_markdown_only(settings: Settings, vault: Path) -> None:
    (vault / "not-a-note.txt").write_text("ignore me", encoding="utf-8")
    paths = [p.relative_to(vault).as_posix() for p in VaultReader(settings).iter_notes()]
    assert set(paths) == {"Daily/2026-06-24.md", "Topics/MCP.md", "Welcome.md"}


def test_iter_notes_skips_hidden_by_default(settings: Settings, vault: Path) -> None:
    hidden_dir = vault / ".obsidian"
    hidden_dir.mkdir()
    (hidden_dir / "workspace.md").write_text("hidden", encoding="utf-8")
    paths = [p.relative_to(vault).as_posix() for p in VaultReader(settings).iter_notes()]
    assert ".obsidian/workspace.md" not in paths


def test_read_note_returns_parsed_model(settings: Settings) -> None:
    note = VaultReader(settings).read_note("Topics/MCP.md")
    assert note.title == "MCP"
    assert "mcp" in note.tags
    assert note.outgoing_links == ("Welcome",)
    assert note.truncated is False


def test_read_note_truncates_oversized_files(vault: Path) -> None:
    big = vault / "Big.md"
    big.write_text("a" * (2 * 1024 + 100), encoding="utf-8")
    settings = Settings(vault_path=vault, max_file_kb=2)
    note = VaultReader(settings).read_note("Big.md")
    assert note.truncated is True
    assert len(note.content) <= 2 * 1024


def test_read_note_missing_raises(settings: Settings) -> None:
    with pytest.raises(NoteNotFoundError):
        VaultReader(settings).read_note("does-not-exist.md")


def test_read_note_rejects_traversal(settings: Settings) -> None:
    with pytest.raises(VaultPathError):
        VaultReader(settings).read_note("../escape.md")


def test_read_note_rejects_binary(vault: Path, settings: Settings) -> None:
    (vault / "Binary.md").write_bytes(b"hello\x00world")
    with pytest.raises(NoteTooLargeError):
        VaultReader(settings).read_note("Binary.md")
