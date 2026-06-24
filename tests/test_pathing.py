"""Security tests for the sandboxed path resolver.

These tests are intentionally adversarial: every path-traversal trick we can
think of must be rejected. If a future refactor weakens the resolver, these
tests should be the first thing that fails.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from obsidian_mcp.utils.errors import VaultPathError
from obsidian_mcp.utils.pathing import is_hidden, safe_resolve


def test_resolves_simple_relative_path(vault: Path) -> None:
    resolved = safe_resolve(vault, "Welcome.md")
    assert resolved == vault / "Welcome.md"


def test_resolves_nested_path(vault: Path) -> None:
    resolved = safe_resolve(vault, "Topics/MCP.md")
    assert resolved == vault / "Topics" / "MCP.md"


@pytest.mark.parametrize(
    "bad_path",
    [
        "../etc/passwd",
        "Topics/../../etc/passwd",
        "../../../../../../etc/passwd",
        "/etc/passwd",
        "/Welcome.md",
        "",
        "   ",
        "./../escape",
        "Topics/..",
    ],
)
def test_rejects_traversal_and_absolute(vault: Path, bad_path: str) -> None:
    with pytest.raises(VaultPathError):
        safe_resolve(vault, bad_path)


def test_rejects_symlink_escape(vault: Path, tmp_path: Path) -> None:
    outside = tmp_path / "outside.txt"
    outside.write_text("secret", encoding="utf-8")
    link = vault / "escape.md"
    link.symlink_to(outside)

    with pytest.raises(VaultPathError):
        safe_resolve(vault, "escape.md")


def test_is_hidden_detects_dotfiles(vault: Path) -> None:
    hidden_file = vault / ".secrets" / "x.md"
    hidden_file.parent.mkdir()
    hidden_file.write_text("x", encoding="utf-8")

    assert is_hidden(hidden_file, vault) is True
    assert is_hidden(vault / "Welcome.md", vault) is False
