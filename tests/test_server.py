"""Server-level smoke tests.

We construct the FastMCP app against a real fixture vault and assert that the
expected tools are registered. End-to-end protocol tests will be added in a
later phase once the full tool surface is in place.
"""

from __future__ import annotations

from typing import Any, cast

import pytest
from mcp.server.fastmcp.exceptions import ToolError

from obsidian_mcp.config import Settings
from obsidian_mcp.server import SERVER_NAME, build_server

# The FastMCP `call_tool` method is typed as ``Sequence[ContentBlock] | dict``
# but at runtime returns ``(content_blocks, structured_output)`` when
# ``convert_result=True`` (which is always the case for FastMCP tools).
# We cast at the call sites below so the rest of each test stays type-safe.
_ToolReturn = tuple[list[Any], dict[str, Any] | None]


async def test_build_server_registers_tools(settings: Settings) -> None:
    server = build_server(settings)
    tools = await server.list_tools()
    tool_names = {tool.name for tool in tools}

    assert server.name == SERVER_NAME
    assert "get_note" in tool_names


async def test_get_note_tool_returns_parsed_payload(settings: Settings) -> None:
    server = build_server(settings)
    content, structured = cast(
        _ToolReturn, await server.call_tool("get_note", {"path": "Topics/MCP.md"})
    )

    rendered = "".join(getattr(item, "text", "") for item in content)
    assert "MCP" in rendered
    assert structured is not None
    assert structured["path"] == "Topics/MCP.md"
    assert structured["title"] == "MCP"
    assert "mcp" in structured["tags"]


async def test_get_note_tool_surfaces_missing_note(settings: Settings) -> None:
    server = build_server(settings)
    with pytest.raises(ToolError, match="note_not_found"):
        await server.call_tool("get_note", {"path": "does-not-exist.md"})


async def test_get_note_tool_rejects_path_traversal(settings: Settings) -> None:
    server = build_server(settings)
    with pytest.raises(ToolError, match="invalid_path"):
        await server.call_tool("get_note", {"path": "../escape.md"})
