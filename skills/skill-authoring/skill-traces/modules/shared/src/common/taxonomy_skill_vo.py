"""Common kernel utilities shared across skill features."""

from __future__ import annotations

from pathlib import Path


class SkillDescriptor:
    """Resolved identity for one skill directory.

    ``name`` is the frontmatter ``name:`` value (or directory name fallback);
    ``description`` is the frontmatter ``description:`` (empty when absent).
    """

    __slots__ = ("description", "name")

    def __init__(self, name: str, description: str = "") -> None:
        self.name = name
        self.description = description

    def __repr__(self) -> str:
        return f"SkillDescriptor(name={self.name!r}, description={self.description!r})"


def extract_skill_name(skill_md: Path) -> tuple[str | None, str]:
    """Return ``(name, description)`` from frontmatter; ``None`` name when absent."""
    try:
        text = skill_md.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return None, ""
    if not text.startswith("---\n"):
        return None, ""
    end = text.find("\n---", 4)
    if end == -1:
        return None, ""
    name: str | None = None
    description = ""
    for line in text[4:end].splitlines():
        if line.startswith("name:") and name is None:
            name = line.split(":", 1)[1].strip().strip("\"'")
        elif line.startswith("description:"):
            description = line.split(":", 1)[1].strip().strip("\"'")
    return name, description


__all__ = ["SkillDescriptor", "extract_skill_name"]
