"""Domain models for vault entities.

These are deliberately small, immutable dataclasses (via Pydantic) so they can
be safely serialised back to the MCP client without leaking internal state.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class Frontmatter(BaseModel):
    """Parsed YAML frontmatter for a note.

    Unknown fields are preserved in :attr:`extra` so we never silently drop
    user metadata when round-tripping notes.
    """

    model_config = ConfigDict(frozen=True)

    title: str | None = None
    tags: tuple[str, ...] = ()
    aliases: tuple[str, ...] = ()
    extra: dict[str, Any] = Field(default_factory=dict)


class Note(BaseModel):
    """A single Markdown note inside the vault."""

    model_config = ConfigDict(frozen=True)

    path: str = Field(description="Vault-relative POSIX path, e.g. 'Topics/MCP.md'.")
    title: str = Field(description="Display title (frontmatter > first H1 > filename stem).")
    content: str = Field(description="Raw Markdown body, without frontmatter.")
    frontmatter: Frontmatter = Field(default_factory=Frontmatter)
    tags: tuple[str, ...] = Field(
        default_factory=tuple, description="Inline #tags plus frontmatter tags."
    )
    outgoing_links: tuple[str, ...] = Field(
        default_factory=tuple, description="Targets of [[wikilinks]]."
    )
    size_bytes: int = 0
    modified_at: datetime | None = None
    truncated: bool = Field(
        default=False,
        description="True if the file was larger than max_file_kb and content is truncated.",
    )
