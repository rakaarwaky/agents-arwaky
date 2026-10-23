"""Skill-library validation.

The 13 issue checks, lifted verbatim from
``skill-librarian/scripts/librarian.py`` ``validate_library`` (lines
300-450). Issue-type strings and message templates are read from the
SSOT (``_rules/skill_rules.py``) so this module and the librarian can
never drift apart (risk R3 in the design doc).

``validate_library`` takes an explicit ``skills_root``; ``librarian.py``
passes its own ``SKILLS_ROOT`` and keeps byte-identical output.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

_SCRIPTS_DIR = Path(__file__).resolve().parent
_RULES_DIR = Path(__file__).resolve().parent.parent / "_rules"
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))
if str(_RULES_DIR) not in sys.path:
    sys.path.insert(0, str(_RULES_DIR))

import model
from model import category_dirs, skill_entries
from skill_rules import (
    IGNORED_CATEGORY_DIRS,
    MAX_DESCRIPTION_LEN,
    IssueType,
    is_valid_skill_name,
    issue_message,
)

__all__ = ["validate_library", "validate_summary"]


def _issue(
    issue_type: IssueType,
    message: str,
    path: str | None = None,
    category: str | None = None,
) -> dict[str, Any]:
    """Shape an issue exactly the way ``librarian.py`` does: type + message,
    optional ``path`` (locator for skill-level issues) and ``category``
    (locator for category-level issues).
    """
    issue: dict[str, Any] = {"type": issue_type.value, "message": message}
    if path:
        issue["path"] = path
    if category:
        issue["category"] = category
    return issue


def _iter_skill_md_files_relative(skills_root: Path, pattern: str):
    """Yield ``skills_root``-relative SKILL.md files under ``pattern``,
    skipping hidden/ignored category dirs. Verbatim from
    ``librarian.py`` ``iter_skill_md_files_relative``.
    """
    for path in skills_root.glob(pattern):
        try:
            rel = path.relative_to(skills_root)
        except ValueError:
            continue

        parts = rel.parts
        if not parts:
            continue

        if parts[0].startswith("."):
            continue

        if parts[0] in IGNORED_CATEGORY_DIRS:
            continue

        yield path


def validate_library(skills_root: Path) -> dict[str, Any]:
    """Run every check; return ``{skills_root, catalog, issue_count, issues}``.

    ``catalog`` is the CATALOG.md path ``librarian.py`` reports (its
    siblings — catalog rendering and the ``--json`` flag — are PR-4/PR-5
    work, so the report keeps only the two fields the ``validate``
    subcommand of ``cli.py`` consumes today).
    """
    issues: list[dict[str, Any]] = []
    entries = model.skill_entries(skills_root)
    categories = model.category_summaries(entries, skills_root)
    assets = model.assets_container(skills_root)

    for cat in categories:
        if cat.category in assets:
            # Declared DM2 asset container: its emptiness and the missing
            # DESCRIPTION.md are by design, so both checks are skipped.
            continue
        if not cat.description_file_exists:
            issues.append(
                _issue(
                    IssueType.MISSING_CATEGORY_DESCRIPTION,
                    issue_message(IssueType.MISSING_CATEGORY_DESCRIPTION),
                    category=cat.category,
                )
            )
        elif not cat.description:
            issues.append(
                _issue(
                    IssueType.EMPTY_CATEGORY_DESCRIPTION,
                    issue_message(IssueType.EMPTY_CATEGORY_DESCRIPTION),
                    category=cat.category,
                )
            )

        if cat.skill_count == 0:
            issues.append(
                _issue(
                    IssueType.EMPTY_CATEGORY,
                    issue_message(IssueType.EMPTY_CATEGORY),
                    category=cat.category,
                )
            )

    name_map: dict[str, list[str]] = {}
    desc_map: dict[str, list[str]] = {}

    for entry in entries:
        path = entry.path

        name_map.setdefault(entry.skill, []).append(path)

        if entry.description:
            desc_map.setdefault(entry.description, []).append(path)

        if entry.frontmatter_name != entry.skill:
            issues.append(
                _issue(
                    IssueType.NAME_MISMATCH,
                    issue_message(
                        IssueType.NAME_MISMATCH,
                        name=entry.frontmatter_name,
                        dir=entry.skill,
                    ),
                    path=path,
                )
            )

        if not is_valid_skill_name(entry.skill):
            issues.append(
                _issue(
                    IssueType.INVALID_SKILL_NAME,
                    issue_message(IssueType.INVALID_SKILL_NAME),
                    path=path,
                )
            )

        if not entry.description:
            issues.append(
                _issue(
                    IssueType.MISSING_DESCRIPTION,
                    issue_message(IssueType.MISSING_DESCRIPTION),
                    path=path,
                )
            )
        else:
            if any(ch in entry.description for ch in ('<', '>', '"')):
                issues.append(
                    _issue(
                        IssueType.INVALID_DESCRIPTION_CHARACTERS,
                        issue_message(IssueType.INVALID_DESCRIPTION_CHARACTERS),
                        path=path,
                    )
                )

            if len(entry.description) > MAX_DESCRIPTION_LEN:
                issues.append(
                    _issue(
                        IssueType.DESCRIPTION_TOO_LONG,
                        issue_message(
                            IssueType.DESCRIPTION_TOO_LONG,
                            length=len(entry.description),
                            max_len=MAX_DESCRIPTION_LEN,
                        ),
                        path=path,
                    )
                )

        skill_dir = skills_root / path
        nested = [
            str(p.relative_to(skills_root))
            for p in skill_dir.rglob("SKILL.md")
            if p != skill_dir / "SKILL.md"
        ]

        if nested:
            issues.append(
                _issue(
                    IssueType.NESTED_SKILL_MD,
                    issue_message(IssueType.NESTED_SKILL_MD, paths=", ".join(nested)),
                    path=path,
                )
            )

    for p in _iter_skill_md_files_relative(skills_root, "*/SKILL.md"):
        issues.append(
            _issue(
                IssueType.INVALID_PLACEMENT,
                issue_message(IssueType.INVALID_PLACEMENT),
                path=str(p.relative_to(skills_root)),
            )
        )

    for p in _iter_skill_md_files_relative(skills_root, "*/*/*/SKILL.md"):
        # DM1 nested-pack marker: the intermediate directory carrying
        # ``pack.toml`` opts the pack in — its too-deep files are
        # skipped. Without the marker the violation stands unchanged.
        if str(p.relative_to(skills_root)) in model.too_deep_exempt_paths(skills_root):
            continue
        issues.append(
            _issue(
                IssueType.TOO_DEEP,
                issue_message(IssueType.TOO_DEEP),
                path=str(p.relative_to(skills_root)),
            )
        )

    for name, paths in sorted(name_map.items()):
        if len(paths) > 1:
            issues.append(
                _issue(
                    IssueType.DUPLICATE_SKILL_NAME,
                    issue_message(
                        IssueType.DUPLICATE_SKILL_NAME,
                        name=name,
                        paths=", ".join(sorted(paths)),
                    ),
                )
            )

    for description, paths in sorted(desc_map.items()):
        if len(paths) > 1:
            issues.append(
                _issue(
                    IssueType.DUPLICATE_DESCRIPTION,
                    issue_message(
                        IssueType.DUPLICATE_DESCRIPTION,
                        paths=", ".join(sorted(paths)),
                    ),
                )
            )

    return {
        "skills_root": str(skills_root),
        "catalog": str(skills_root / "CATALOG.md"),
        "issue_count": len(issues),
        "issues": issues,
    }


def validate_summary(skills_root: Path) -> str:
    """One-line observability summary for CI (design §10.1):
    ``<issues> issues / <skills> skills / <categories> categories``.

    All three counts are derived from the live tree: issues is
    ``validate_library``'s total (unfiltered, matching the exit-code
    semantics), skills is the loader-visible count from
    ``model.skill_entries`` (``category/*/SKILL.md`` with frontmatter),
    categories is the count of directories ``model.category_dirs``
    yields. Nothing is hardcoded.
    """
    report = validate_library(skills_root)
    entries = skill_entries(skills_root)
    categories = list(category_dirs(skills_root))
    return f"{report['issue_count']} issues / {len(entries)} skills / {len(categories)} categories"
