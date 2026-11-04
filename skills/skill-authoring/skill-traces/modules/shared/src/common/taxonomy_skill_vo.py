"""Common kernel utilities shared across skill features."""

from __future__ import annotations

from pathlib import Path


def extract_skill_name(skill_md: Path) -> str | None:
    """Return the ``name:`` from frontmatter, or None when absent."""
    try:
        text = skill_md.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return None
    if not text.startswith("---\n"):
        return None
    end = text.find("\n---", 4)
    if end == -1:
        return None
    for line in text[4:end].splitlines():
        if line.startswith("name:"):
            return line.split(":", 1)[1].strip().strip("\"'")
    return None


__all__ = ["extract_skill_name"]
