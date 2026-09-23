"""Shared skill-name helpers (AES taxonomy layer, _vo: pure functions allowed)."""
from __future__ import annotations

import posixpath
import re
from dataclasses import dataclass
from pathlib import Path
from typing import NewType

#: Process or command exit code (0 = success, non-zero = failure).
ExitCode = NewType("ExitCode", int)

#: Tool filter query string for skill listing.
ToolFilter = NewType("ToolFilter", str)

#: Skill name query string for skill show/install.
SkillQuery = NewType("SkillQuery", str)

#: Skill command argument list.
SkillArgs = NewType("SkillArgs", list)

#: Operation token dispatched through ``ISkillProtocol.execute``.
SkillOp = NewType("SkillOp", str)

#: Tool identifier accepted by skill provisioning actions.
SkillToolId = NewType("SkillToolId", str)

#: Optional destination directory override for skill provisioning.
SkillDest = NewType("SkillDest", str)

#: Optional skill/tool name argument for a skill op.
SkillName = NewType("SkillName", str)

#: Module-level singletons for default arguments (B008).
FILTER_EMPTY: ToolFilter = ToolFilter("")
QUERY_EMPTY: SkillQuery = SkillQuery("")
ARGS_EMPTY: SkillArgs = SkillArgs([])
SKILL_EMPTY: SkillName = SkillName("")

def extract_skill_name(skill_md: Path) -> str:
    """Extract `name:` from SKILL.md frontmatter; fallback to parent dir name."""
    try:
        text = skill_md.read_text(encoding="utf-8", errors="replace")
        m = re.search(r"^---\s*\n(.*?)\n---", text, re.DOTALL)
        if m:
            nm = re.search(r"^name:\s*[\"']?(.+?)[\"']?\s*$", m.group(1), re.MULTILINE)
            if nm:
                return nm.group(1).strip()
    except OSError:
        pass
    return skill_md.parent.name


def sanitize_skill_name(raw: str, fallback: str) -> str:
    """Convert frontmatter name into a safe directory name (prevents path traversal)."""
    raw = (raw or "").strip().replace("\\", "/")
    raw = posixpath.basename(raw)
    name = re.sub(r"[^A-Za-z0-9._-]+", "-", raw).strip(".-")
    if not name:
        name = re.sub(r"[^A-Za-z0-9._-]+", "-", fallback).strip(".-") or "skill"
    return name[:64]


def safe_skill_name(skill_md: Path) -> str:
    return sanitize_skill_name(extract_skill_name(skill_md), skill_md.parent.name)


def safe_child(base: Path, name: str) -> Path:
    """Lexical ``base / name`` for a provisioned skill dir.

    Unlike ensure_under this never resolves symlinks: a destination that is
    already a symlink into the skill pack resolves OUTSIDE the harness skills
    dir, which would make every re-provision fail the containment check.
    Traversal is blocked by rejecting anything but a single safe component.
    """
    if not name or name in (".", "..") or "/" in name or "\\" in name:
        raise ValueError(f"Refusing unsafe skill name: {name!r}")
    return base / name


def ensure_under(base: Path, child: Path) -> Path:
    """Ensure child path stays inside base. Raises ValueError on traversal."""
    base_resolved = base.resolve()
    child_resolved = child.resolve()
    if child_resolved == base_resolved:
        return child_resolved
    if base_resolved not in child_resolved.parents:
        raise ValueError(f"Refusing path outside target directory: {child_resolved}")
    return child_resolved


@dataclass(frozen=True)
class SkillInfo:
    """Registration row for a tool: id, category, description."""

    tool_id: str
    category: str
    description: str


@dataclass(frozen=True)
class SkillProvisionResult:
    """Outcome of provisioning/unprovisioning skills for one tool."""

    success: bool
    tool_id: str
    provisioned: int
    message: str


__all__ = [
    "ARGS_EMPTY",
    "FILTER_EMPTY",
    "QUERY_EMPTY",
    "SKILL_EMPTY",
    "ExitCode",
    "SkillArgs",
    "SkillDest",
    "SkillInfo",
    "SkillName",
    "SkillOp",
    "SkillProvisionResult",
    "SkillQuery",
    "SkillToolId",
    "ToolFilter",
    "ensure_under",
    "extract_skill_name",
    "safe_child",
    "safe_skill_name",
    "sanitize_skill_name",
]
