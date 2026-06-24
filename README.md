# obsidian-mcp

> A [Model Context Protocol](https://modelcontextprotocol.io) server that lets any MCP-compatible AI host (Cursor, Claude Desktop, Zed, etc.) read, search, link, and write notes inside a local Markdown / [Obsidian](https://obsidian.md) vault.

[![CI](https://github.com/darrenlopez/obsidian-mcp/actions/workflows/ci.yml/badge.svg)](https://github.com/darrenlopez/obsidian-mcp/actions/workflows/ci.yml)
[![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-blue)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](./LICENSE)

---

## What is this?

`obsidian-mcp` is an [MCP](https://modelcontextprotocol.io) server. MCP is an open
standard from Anthropic for connecting AI assistants to external tools and data
sources — think "USB-C for AI applications". Once this server is registered with
an MCP host you can ask the model questions like:

> *"What did I learn about MCP this week, and which of my notes link to it?"*

…and the model will call this server's tools (`search_notes`, `find_backlinks`,
`get_recent_notes`, …) to answer using **your** actual notes.

## Status

| Phase | Scope | State |
|------:|------|------|
| 0 | Repo skeleton, CI, sample vault, server stub with `get_note` | **shipped** |
| 1 | Sandboxed pathing, parser, reader, tests | **shipped** |
| 2 | Search, listings, backlinks, tag index | planned |
| 3 | Resources (notes as `obsidian://` URIs) | planned |
| 4 | Write tools (`create_note`, `append_to_note`) + atomic writes | planned |
| 5 | Prompts (`/weekly-review`, `/daily-note-template`) | planned |

## Architecture

```text
┌────────────────┐    stdio JSON-RPC    ┌────────────────────────┐
│  MCP host      │ ───────────────────► │  obsidian-mcp server   │
│ (Cursor /      │                      │  (this repo)           │
│  Claude /      │                      │                        │
│  Zed)          │                      │  tools / resources /   │
└────────────────┘                      │  prompts               │
                                        └───────────┬────────────┘
                                                    │
                                        sandboxed   ▼
                                        ┌────────────────────────┐
                                        │  Local Markdown vault  │
                                        └────────────────────────┘
```

Every caller-supplied path is funnelled through a single sandboxing function
(`utils/pathing.py::safe_resolve`) before any filesystem access, so the server
cannot be coerced into reading files outside the configured vault root.

## Quickstart

### 1. Install

```bash
git clone https://github.com/darrenlopez/obsidian-mcp.git
cd obsidian-mcp
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
```

### 2. Try it against the bundled sample vault

```bash
OBSIDIAN_MCP_VAULT_PATH="$(pwd)/sample-vault" \
  npx @modelcontextprotocol/inspector \
  python -m obsidian_mcp
```

This launches Anthropic's official [MCP Inspector](https://github.com/modelcontextprotocol/inspector)
pointed at this server, so you can interactively call `get_note` and inspect
schemas without leaving your browser.

### 3. Register with Cursor

Add the following to your Cursor MCP config
(`~/.cursor/mcp.json` or the Cursor settings UI):

```json
{
  "mcpServers": {
    "obsidian": {
      "command": "python",
      "args": ["-m", "obsidian_mcp"],
      "env": {
        "OBSIDIAN_MCP_VAULT_PATH": "/absolute/path/to/your/vault",
        "OBSIDIAN_MCP_READ_ONLY": "false"
      }
    }
  }
}
```

### 4. Register with Claude Desktop

Add the same block to `~/Library/Application Support/Claude/claude_desktop_config.json`
on macOS (or the platform equivalent).

## Configuration

All configuration is via environment variables (prefix `OBSIDIAN_MCP_`).

| Variable | Default | Purpose |
|---|---|---|
| `OBSIDIAN_MCP_VAULT_PATH` | *(required)* | Absolute path to the vault root. |
| `OBSIDIAN_MCP_READ_ONLY` | `false` | When `true`, write tools are not registered. |
| `OBSIDIAN_MCP_MAX_FILE_KB` | `1024` | Max note size (KiB) returned by read operations. |
| `OBSIDIAN_MCP_INCLUDE_HIDDEN` | `false` | Include dotfiles and `.obsidian/` in listings/search. |

## Tools (Phase 0 / 1)

| Tool | Description |
|------|-------------|
| `get_note(path)` | Read a single note, returning parsed frontmatter, tags, and outgoing wikilinks. |

The Phase 2+ tool surface (`search_notes`, `list_notes`, `find_backlinks`,
`list_tags`, `get_recent_notes`, …) is documented in the
[architecture plan](#architecture) and tracked in [`STATUS`](#status).

## Security

This server reads (and, in non-read-only mode, writes) files on your machine.
Some choices that limit blast radius:

- **Sandboxed paths.** Every path is resolved through `safe_resolve(vault_root, user_input)`,
  which rejects absolute paths, `..` segments, and symlink escapes before any
  filesystem touch.
- **Read-only mode.** Set `OBSIDIAN_MCP_READ_ONLY=true` and write tools are
  not registered at all.
- **Size limits.** `OBSIDIAN_MCP_MAX_FILE_KB` caps the bytes returned by read
  operations to prevent DoS via huge files.
- **Hidden-file exclusion.** `.obsidian/` and dotfiles are skipped by default,
  so plugin secrets do not leak into model context.
- **No network.** The server makes no outbound network requests of its own.
- **No `shell=True`, no `eval`.** Anywhere.

## Development

```bash
pip install -e ".[dev]"
ruff check .
ruff format --check .
mypy
pytest
```

The test suite includes adversarial path-traversal tests
(`tests/test_pathing.py`) — keep them green.

## License

[MIT](./LICENSE)
