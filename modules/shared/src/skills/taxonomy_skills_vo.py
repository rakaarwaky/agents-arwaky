"""Skills taxonomy value objects (AES taxonomy layer).

Pure data + helpers for the skills feature. No I/O, no imports from
capabilities/agent/root/surface layers.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import NewType

SkillQuery = NewType("SkillQuery", str)
"""A skill name / identifier to look up in the pack."""

SkillContent = NewType("SkillContent", str)
"""Raw SKILL.md text returned by a read."""

SkillDescription = NewType("SkillDescription", str)
"""One-line description extracted from SKILL.md frontmatter."""


@dataclass(frozen=True)
class SkillRecord:
    """One discoverable skill in the pack."""

    name: str
    description: SkillDescription
    path: Path


@dataclass(frozen=True)
class SkillsRequest:
    """Input for a skills read operation.

    op: "list" | "show". For "show", ``query`` carries the skill name.
    """

    op: str = "list"
    query: SkillQuery = field(default_factory=lambda: SkillQuery(""))


@dataclass(frozen=True)
class SkillsResult:
    """Response to a skills read operation."""

    ok: bool
    records: tuple[SkillRecord, ...] = field(default_factory=lambda: ())
    content: SkillContent | None = None
    message: str = ""


__all__ = [
    "SkillContent",
    "SkillDescription",
    "SkillQuery",
    "SkillRecord",
    "SkillsRequest",
    "SkillsResult",
]