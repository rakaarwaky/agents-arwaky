"""Skill-pack loadability audit primitives (shared taxonomy layer).

Pure, stateless pack-inspection functions moved from
:mod:`modules.skill.src.utility_skill_pack` so that capability modules in
other features can import them without a capabilities->capabilities edge
(AES201). Provenance/pruning (I/O-bound) stay in the skill feature.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from modules.shared.src.taxonomy_core_constant import (
    DESCRIPTION_BUDGET_BYTES,
)

SKILL_FILE = "SKILL.md"
_SKIP_PARTS = {"node_modules", ".venv", "venv", "target", ".git", "__pycache__"}


@dataclass(frozen=True)
class PackFinding:
    """One violated loadability invariant, ready for CLI reporting."""

    code: str
    message: str
    path: str = ""


def _read(skill_md: Path) -> str:
    try:
        return skill_md.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""


def _frontmatter_value(text: str, field: str) -> str:
    block = re.match(r"^---\s*\n(.*?)\n---", text, re.DOTALL)
    if not block:
        return ""
    found = re.search(
        rf"^{field}:\s*[\"']?(.*?)[\"']?\s*$", block.group(1), re.MULTILINE
    )
    return found.group(1).strip() if found else ""


def skill_name(skill_md: Path) -> str:
    return _frontmatter_value(_read(skill_md), "name")


def skill_description(skill_md: Path) -> str:
    return _frontmatter_value(_read(skill_md), "description")


def iter_skill_files(base: Path) -> list[Path]:
    """Every ``SKILL.md`` under *base*, ignoring vendored/build directories."""
    if not base.is_dir():
        return []
    return [
        path
        for path in sorted(base.rglob(SKILL_FILE))
        if not _SKIP_PARTS.intersection(path.relative_to(base).parts)
    ]


def pack_names(base: Path) -> set[str]:
    """Folder names of every skill in the pack."""
    return {path.parent.name for path in iter_skill_files(base)}


def audit_pack(base: Path) -> list[PackFinding]:
    """Check the pack against the loadability invariants; empty list means clean."""
    files = iter_skill_files(base)
    if not files:
        return [PackFinding("pack-missing", f"No {SKILL_FILE} found under {base}", str(base))]

    findings: list[PackFinding] = []
    seen: dict[str, str] = {}
    description_bytes = 0
    categories: set[str] = set()

    for path in files:
        parts = path.relative_to(base).parts
        rel_text = str(Path(base.name, *parts))
        category = parts[0] if len(parts) >= 2 else ""
        skill_dir = parts[1] if len(parts) >= 3 else ""
        if category:
            categories.add(category)

        # 1. one level below a category: <category>/<skill>/SKILL.md
        if len(parts) != 3:
            findings.append(PackFinding(
                "nested-layout",
                f"{rel_text} is not <category>/<skill>/{SKILL_FILE}; the harness scans "
                "one level below a skills root, so this skill never loads",
                rel_text,
            ))

        text = _read(path)

        # 2. frontmatter name == folder name
        name = _frontmatter_value(text, "name")
        if not name:
            findings.append(PackFinding("name-missing", f"{rel_text} has no frontmatter name:", rel_text))
        elif skill_dir and name != skill_dir:
            findings.append(PackFinding(
                "name-mismatch",
                f"{rel_text} declares name '{name}' but lives in folder '{skill_dir}'",
                rel_text,
            ))

        # 3. non-empty description
        description = _frontmatter_value(text, "description")
        if not description:
            findings.append(PackFinding(
                "description-missing", f"{rel_text} has no description:", rel_text
            ))
        description_bytes += len(description.encode("utf-8"))

        # 4. names unique across the whole pack
        if name:
            if name in seen:
                findings.append(PackFinding(
                    "duplicate-name",
                    f"'{name}' is used by both {seen[name]} and {rel_text}",
                    rel_text,
                ))
            else:
                seen[name] = rel_text

    # 5. aggregate description budget (injected into every session prompt)
    if description_bytes > DESCRIPTION_BUDGET_BYTES:
        findings.append(PackFinding(
            "description-budget",
            f"descriptions total {description_bytes} bytes, over the "
            f"{DESCRIPTION_BUDGET_BYTES}-byte budget; shorten triggers or move detail "
            "into references/*.md",
            base.name,
        ))

    # A category with no skill is never registered as a root, so it hides its files.
    present = {
        entry.name
        for entry in sorted(base.iterdir())
        if entry.is_dir() and not entry.name.startswith(".")
        and entry.name not in _SKIP_PARTS
    }
    for empty in sorted(present - categories):
        findings.append(PackFinding(
            "empty-category",
            f"skills/{empty} holds no <skill>/{SKILL_FILE}; a category with no skill "
            "is never registered as a skills root, so anything inside it is invisible",
            f"{base.name}/{empty}",
        ))

    # A folder at skill depth must carry SKILL.md directly, or the loader skips it.
    for category in sorted(present):
        for entry in sorted((base / category).iterdir()):
            if not entry.is_dir() or entry.name.startswith(".") or entry.name in _SKIP_PARTS:
                continue
            if not (entry / SKILL_FILE).is_file():
                findings.append(PackFinding(
                    "skill-without-skill-md",
                    f"skills/{category}/{entry.name} has no {SKILL_FILE}; the loader "
                    "only reads that exact filename, so the folder is dead weight",
                    f"{base.name}/{category}/{entry.name}",
                ))

    return findings


# --- provenance ---------------------------------------------------------------
