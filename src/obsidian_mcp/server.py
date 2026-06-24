"""MCP server entry point.

This module builds a :class:`mcp.server.fastmcp.FastMCP` instance and registers
the Phase 1 tool set. Subsequent phases extend the tool, resource, and prompt
registries here.

Why a build function instead of a module-level singleton?
The server is constructed lazily so tests can spin up isolated instances
against a fixture vault without touching real environment variables.
"""

from __future__ import annotations

from mcp.server.fastmcp import FastMCP

from obsidian_mcp.config import Settings
from obsidian_mcp.utils.errors import VaultError
from obsidian_mcp.vault.models import Note
from obsidian_mcp.vault.reader import VaultReader

SERVER_NAME = "obsidian-mcp"


def build_server(settings: Settings | None = None) -> FastMCP:
    """Construct a fully-configured MCP server.

    Args:
        settings: Optional preloaded settings. When ``None`` settings are read
            from the environment (and, optionally, a ``.env`` file).

    Returns:
        A ready-to-run :class:`FastMCP` instance.
    """
    resolved_settings = settings or Settings()  # type: ignore[call-arg]
    reader = VaultReader(resolved_settings)

    mcp = FastMCP(
        SERVER_NAME,
        instructions=(
            "Tools for reading, searching and (when not in read-only mode) "
            "writing notes in a local Markdown / Obsidian vault. Paths are "
            "always vault-relative POSIX paths (e.g. 'Topics/MCP.md')."
        ),
    )

    @mcp.tool()
    def get_note(path: str) -> Note:
        """Read a single note from the vault.

        Args:
            path: Vault-relative POSIX path to a Markdown file
                (e.g. ``Topics/MCP.md``).

        Returns:
            The parsed note including frontmatter, tags, and outgoing wikilinks.
        """
        try:
            return reader.read_note(path)
        except VaultError as exc:
            raise ValueError(f"{exc.code}: {exc}") from exc

    return mcp


def run() -> None:
    """Run the server over stdio (the transport used by Cursor / Claude Desktop)."""
    server = build_server()
    server.run()
