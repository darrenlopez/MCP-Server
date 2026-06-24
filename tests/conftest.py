"""Shared pytest fixtures.

Each test that needs filesystem access gets its own isolated vault built in a
``tmp_path`` directory, so tests can mutate freely without touching the
checked-in ``sample-vault/``.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from obsidian_mcp.config import Settings


@pytest.fixture
def vault(tmp_path: Path) -> Path:
    """Create a tiny vault inside ``tmp_path`` and return its root.

    The vault is a *subdirectory* of ``tmp_path`` (not ``tmp_path`` itself) so
    tests that need to place files *outside* the vault sandbox have a sibling
    location to write to.
    """
    root = tmp_path / "vault"
    (root / "Topics").mkdir(parents=True)
    (root / "Daily").mkdir()

    (root / "Welcome.md").write_text(
        "---\ntitle: Welcome\ntags: [meta]\n---\n\n# Welcome\n\nSee [[Topics/MCP]]. #intro\n",
        encoding="utf-8",
    )
    (root / "Topics" / "MCP.md").write_text(
        "---\ntitle: MCP\ntags: [mcp, protocols]\n---\n\n# MCP\n\nBacklink to [[Welcome]].\n",
        encoding="utf-8",
    )
    (root / "Daily" / "2026-06-24.md").write_text(
        "# 2026-06-24\n\nMet with self about [[Topics/MCP]]. #daily\n",
        encoding="utf-8",
    )
    return root.resolve()


@pytest.fixture
def settings(vault: Path) -> Settings:
    """Settings pointing at the isolated test vault."""
    return Settings(vault_path=vault)
