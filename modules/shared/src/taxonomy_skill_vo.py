"""Shared skill-name helpers (AES taxonomy layer, _vo: pure functions allowed)."""
from __future__ import annotations

import posixpath
import re
from pathlib import Path

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
