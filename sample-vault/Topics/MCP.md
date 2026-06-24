---
title: Model Context Protocol
tags: [mcp, protocols]
---

# Model Context Protocol

The **Model Context Protocol** (MCP) is an open standard introduced by Anthropic
that lets AI applications talk to external tools and data in a uniform way.

## Three primitives

- **Tools** — functions the model can invoke (this vault's `get_note` is one).
- **Resources** — read-only data the host can attach to context.
- **Prompts** — user-triggered templates / workflows.

## Transports

- `stdio` — local subprocess, used by Cursor and Claude Desktop.
- Streamable HTTP — remote servers with OAuth 2.1.

See also: [[Topics/Obsidian]], [[Welcome]].
