"""Markdown / Obsidian parsing helpers.

We intentionally use lightweight regex-based extraction for wikilinks and tags
rather than a full Markdown AST. The Obsidian conventions are simple enough
that this is reliable, fast, and dependency-free.
"""

from __future__ import annotations

import re
from typing import Any

import frontmatter

from obsidian_mcp.vault.models import Frontmatter, Note

_WIKILINK_RE = re.compile(r"\[\[([^\[\]\n|#]+)(?:#[^\[\]\n|]+)?(?:\|[^\[\]\n]+)?\]\]")
_TAG_RE = re.compile(r"(?<!\S)#([A-Za-z][\w/-]*)")
_H1_RE = re.compile(r"^\s*#\s+(.+?)\s*$", re.MULTILINE)


def _coerce_str_tuple(value: Any) -> tuple[str, ...]:
    """Coerce a frontmatter value (str, list, None) to a tuple of strings."""
    if value is None:
        return ()
    if isinstance(value, str):
        return (value,)
    if isinstance(value, list | tuple):
        return tuple(str(item) for item in value if item is not None)
    return ()


def _parse_frontmatter(raw_metadata: dict[str, Any]) -> Frontmatter:
    known = {"title", "tags", "aliases"}
    extra = {k: v for k, v in raw_metadata.items() if k not in known}
    return Frontmatter(
        title=raw_metadata.get("title"),
        tags=_coerce_str_tuple(raw_metadata.get("tags")),
        aliases=_coerce_str_tuple(raw_metadata.get("aliases")),
        extra=extra,
    )


def _extract_title(fm: Frontmatter, body: str, fallback: str) -> str:
    if fm.title:
        return fm.title
    match = _H1_RE.search(body)
    if match:
        return match.group(1).strip()
    return fallback


def parse_note(
    *,
    relative_path: str,
    raw_text: str,
    size_bytes: int,
    modified_at: Any = None,
    truncated: bool = False,
) -> Note:
    """Parse a raw note string into a :class:`Note`.

    The parser is tolerant: malformed frontmatter is treated as no frontmatter,
    and unparseable structures degrade gracefully rather than raising.
    """
    try:
        post = frontmatter.loads(raw_text)
        body: str = post.content
        fm = _parse_frontmatter(dict(post.metadata))
    except Exception:
        body = raw_text
        fm = Frontmatter()

    inline_tags = tuple(sorted({m.group(1) for m in _TAG_RE.finditer(body)}))
    all_tags = tuple(sorted(set(fm.tags) | set(inline_tags)))
    outgoing = tuple(sorted({m.group(1).strip() for m in _WIKILINK_RE.finditer(body)}))

    fallback_title = relative_path.rsplit("/", 1)[-1].removesuffix(".md")
    title = _extract_title(fm, body, fallback_title)

    return Note(
        path=relative_path,
        title=title,
        content=body,
        frontmatter=fm,
        tags=all_tags,
        outgoing_links=outgoing,
        size_bytes=size_bytes,
        modified_at=modified_at,
        truncated=truncated,
    )
