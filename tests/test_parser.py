"""Parser unit tests."""

from __future__ import annotations

from obsidian_mcp.vault.parser import parse_note


def test_parses_frontmatter_tags_and_links() -> None:
    raw = (
        "---\n"
        "title: Hello\n"
        "tags: [alpha, beta]\n"
        "aliases: [Hi]\n"
        "---\n"
        "\n"
        "# Hello\n"
        "\n"
        "Body referring to [[Other Note]] and [[Other Note|alias]] with a #gamma tag.\n"
    )
    note = parse_note(relative_path="Hello.md", raw_text=raw, size_bytes=len(raw))

    assert note.title == "Hello"
    assert note.frontmatter.aliases == ("Hi",)
    assert set(note.tags) == {"alpha", "beta", "gamma"}
    assert note.outgoing_links == ("Other Note",)


def test_falls_back_to_h1_then_filename() -> None:
    raw = "# From Heading\n\nbody\n"
    note = parse_note(relative_path="Folder/raw.md", raw_text=raw, size_bytes=len(raw))
    assert note.title == "From Heading"

    note2 = parse_note(relative_path="Folder/no-title.md", raw_text="body\n", size_bytes=5)
    assert note2.title == "no-title"


def test_tolerates_malformed_frontmatter() -> None:
    raw = "---\nnot: [valid yaml\n---\n\n# Body\n"
    note = parse_note(relative_path="bad.md", raw_text=raw, size_bytes=len(raw))
    assert "Body" in note.title or note.title == "bad"


def test_ignores_tag_inside_word() -> None:
    raw = "# X\n\nemail like a#b should not be a tag, but #real is.\n"
    note = parse_note(relative_path="x.md", raw_text=raw, size_bytes=len(raw))
    assert note.tags == ("real",)
