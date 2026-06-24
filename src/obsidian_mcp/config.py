"""Runtime configuration for the Obsidian MCP server.

Configuration is sourced from environment variables (prefix ``OBSIDIAN_MCP_``)
so the server can be configured by the MCP host (Cursor, Claude Desktop, etc.)
through its ``env`` block without any code changes.
"""

from __future__ import annotations

from pathlib import Path

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Server settings loaded from environment variables.

    Attributes:
        vault_path: Absolute path to the vault root. All file operations are
            sandboxed under this directory.
        read_only: When ``True`` write tools are not registered with the server.
        max_file_kb: Maximum size (in KiB) of a single note that may be read.
            Larger files are truncated with a warning to prevent DoS.
        include_hidden: When ``False`` (default) dotfiles and the ``.obsidian``
            directory are excluded from listings and search results.
    """

    model_config = SettingsConfigDict(
        env_prefix="OBSIDIAN_MCP_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    vault_path: Path = Field(
        ...,
        description="Absolute path to the Markdown / Obsidian vault root.",
    )
    read_only: bool = Field(
        default=False,
        description="If True, disables tools that mutate the vault.",
    )
    max_file_kb: int = Field(
        default=1024,
        ge=1,
        le=1024 * 100,
        description="Maximum note size (KiB) returned by read operations.",
    )
    include_hidden: bool = Field(
        default=False,
        description="Include dotfiles and .obsidian/ in listings and search.",
    )

    @field_validator("vault_path")
    @classmethod
    def _validate_vault_path(cls, value: Path) -> Path:
        resolved = value.expanduser().resolve()
        if not resolved.exists():
            raise ValueError(f"vault_path does not exist: {resolved}")
        if not resolved.is_dir():
            raise ValueError(f"vault_path is not a directory: {resolved}")
        return resolved
