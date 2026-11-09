"""Skills linter capability (AES capabilities layer).

Implements ``ISkillsLinterProtocol``: a combined scan that runs the
13-rule validator plus the weed report in one pass, returning a single
``LintReport``. The lint is read-only — it reports, it never writes.

The lint supports an optional *category* filter: when provided, only
issues whose ``category`` or ``path`` belongs to that category are
included in the report. The weed lines are not filtered (they are
library-wide duplicate/empty-category signals).

The 13-rule checks run inline here, ported from the retired
``capabilities_skills_validator.py`` which was folded into this
capability during the deep-clean. Rule IDs and message templates come
from the shared rule SSOT, so the checker and the generated rules doc
cannot drift apart. The weed-plan is consumed through the shared
``utility_skills_mutation.plan_weed`` helper, never through a sibling
capability import.
"""

from __future__ import annotations

import os
from collections.abc import Iterator
from pathlib import Path

from shared.src.common.taxonomy_common_constant import (
    CATALOG_FILENAME,
    IGNORED_CATEGORY_DIRS,
)
from shared.src.common.taxonomy_common_entity import (
    CategorySummary,
    SkillEntry,
)
from shared.src.design.contract_skills_protocol import ISkillsLinterProtocol
from shared.src.design.taxonomy_skills_constant import (
    ASSETS_MARKER_FILENAME,
    MAX_DESCRIPTION_LEN,
    PACK_MARKER_FILENAME,
)
from shared.src.design.taxonomy_skills_entity import (
    Issue,
)
from shared.src.design.taxonomy_skills_request import SkillsRoot
from shared.src.design.taxonomy_skills_vo import (
    IssueType,
    LintReport,
    ValidationReport,
    is_valid_skill_name,
    issue_message,
)
from shared.src.discovery.utility_discovery_core import (
    category_dirs,
    category_summaries,
    parse_frontmatter,
    relpath,
    skill_entries,
)
from shared.src.maintenance.utility_skills_mutation import plan_weed

__all__ = ["SkillsLinter"]


# ─── Block 1: Module Declaration ───
class SkillsLinter(ISkillsLinterProtocol):
    """Combined lint: 13-rule checks + weed report, optionally category-filtered."""

    # ─── Block 2: Module Contract ───
    def lint(
        self, root: SkillsRoot, category: str | None = None
    ) -> LintReport:
        """Run the full lint over *root*; optionally filter by *category*.

        Runs the 13-rule validator (per-skill, category, placement, and
        duplicate checks) inline plus the shared ``plan_weed`` helper for
        the weed lines. When *category* is set, issues are narrowed to
        that category; weed lines are kept as-is (library-wide signals).
        """
        skills_root = Path(root)

        # 13-rule validator checks
        entries = skill_entries(skills_root)
        categories = category_summaries(entries, skills_root)
        assets = assets_container(skills_root)

        issues: list[Issue] = []

        self._check_categories(categories, assets, issues)
        self._check_entries(skills_root, entries, issues)
        self._check_placement(skills_root, issues)
        self._check_duplicates(entries, issues)
        self._check_references(skills_root, entries, issues)

        report = ValidationReport(
            skills_root=skills_root,
            catalog=skills_root / CATALOG_FILENAME,
            issues=tuple(issues),
            skills=len(entries),
            categories=len(list(category_dirs(skills_root))),
        )

        # Weed report
        weed_plan = plan_weed(skills_root)
        weed_lines = weed_plan.lines

        # Category filter
        unfiltered_issues = report.issues
        unfiltered_weed_lines = weed_lines
        if category is not None:
            issues = tuple(
                issue
                for issue in report.issues
                if issue.category == category
                or (issue.path or "").startswith(f"{category}/")
            )
        else:
            issues = report.issues

        return LintReport(
            skills_root=skills_root,
            issues=issues,
            weed_lines=weed_lines,
            skills=report.skills,
            categories=report.categories,
            unfiltered_issues=unfiltered_issues,
            unfiltered_weed_lines=unfiltered_weed_lines,
        )

    # ─── Block 3: Module Helpers ───

    @staticmethod
    def _check_categories(
        categories: list[CategorySummary],
        assets: set[str],
        issues: list[Issue],
    ) -> None:
        """Category-shape checks, skipping declared DM2 asset containers."""
        for cat in categories:
            if cat.category in assets:
                continue

            if not cat.description_file_exists:
                issues.append(
                    Issue(
                        type=IssueType.MISSING_CATEGORY_DESCRIPTION.value,
                        message=issue_message(IssueType.MISSING_CATEGORY_DESCRIPTION),
                        category=cat.category,
                    )
                )
            elif not cat.description:
                issues.append(
                    Issue(
                        type=IssueType.EMPTY_CATEGORY_DESCRIPTION.value,
                        message=issue_message(IssueType.EMPTY_CATEGORY_DESCRIPTION),
                        category=cat.category,
                    )
                )

            if cat.skill_count == 0:
                issues.append(
                    Issue(
                        type=IssueType.EMPTY_CATEGORY.value,
                        message=issue_message(IssueType.EMPTY_CATEGORY),
                        category=cat.category,
                    )
                )

    @staticmethod
    def _check_entries(
        skills_root: Path,
        entries: list[SkillEntry],
        issues: list[Issue],
    ) -> None:
        """Per-skill checks: name, description, budget, and nesting."""
        for entry in entries:
            if entry.frontmatter_name != entry.skill:
                issues.append(
                    Issue(
                        type=IssueType.NAME_MISMATCH.value,
                        message=issue_message(
                            IssueType.NAME_MISMATCH,
                            name=entry.frontmatter_name,
                            dir=entry.skill,
                        ),
                        path=entry.path,
                    )
                )

            if not is_valid_skill_name(entry.skill):
                issues.append(
                    Issue(
                        type=IssueType.INVALID_SKILL_NAME.value,
                        message=issue_message(IssueType.INVALID_SKILL_NAME),
                        path=entry.path,
                    )
                )

            if not entry.description:
                issues.append(
                    Issue(
                        type=IssueType.MISSING_DESCRIPTION.value,
                        message=issue_message(IssueType.MISSING_DESCRIPTION),
                        path=entry.path,
                    )
                )
            else:
                if any(ch in entry.description for ch in ('<', '>', '"')):
                    issues.append(
                        Issue(
                            type=IssueType.INVALID_DESCRIPTION_CHARACTERS.value,
                            message=issue_message(
                                IssueType.INVALID_DESCRIPTION_CHARACTERS
                            ),
                            path=entry.path,
                        )
                    )

                if len(entry.description) > MAX_DESCRIPTION_LEN:
                    issues.append(
                        Issue(
                            type=IssueType.DESCRIPTION_TOO_LONG.value,
                            message=issue_message(
                                IssueType.DESCRIPTION_TOO_LONG,
                                length=len(entry.description),
                                max_len=MAX_DESCRIPTION_LEN,
                            ),
                            path=entry.path,
                        )
                    )

    @staticmethod
    def _check_placement(skills_root: Path, issues: list[Issue]) -> None:
        """``SKILL.md`` directly under a category, and too-deep files."""
        for path in iter_relative_skill_mds(skills_root, depth=1):
            issues.append(
                Issue(
                    type=IssueType.INVALID_PLACEMENT.value,
                    message=issue_message(IssueType.INVALID_PLACEMENT),
                    path=relpath(path, skills_root),
                )
            )

        exempt = too_deep_exempt_paths(skills_root)
        for path in iter_relative_skill_mds(skills_root, depth=3):
            # DM1 nested-pack marker: the intermediate directory carrying
            # ``pack.toml`` opts the pack in — its too-deep files are
            # skipped. Without the marker the violation stands unchanged.
            if relpath(path, skills_root) in exempt:
                continue
            issues.append(
                Issue(
                    type=IssueType.TOO_DEEP.value,
                    message=issue_message(IssueType.TOO_DEEP),
                    path=relpath(path, skills_root),
                )
            )

    @staticmethod
    def _check_duplicates(entries: list[SkillEntry], issues: list[Issue]) -> None:
        """Library-wide duplicate names and descriptions."""
        name_map: dict[str, list[str]] = {}
        desc_map: dict[str, list[str]] = {}

        for entry in entries:
            name_map.setdefault(entry.skill, []).append(entry.path)
            if entry.description:
                desc_map.setdefault(entry.description, []).append(entry.path)

        for name, paths in sorted(name_map.items()):
            if len(paths) > 1:
                issues.append(
                    Issue(
                        type=IssueType.DUPLICATE_SKILL_NAME.value,
                        message=issue_message(
                            IssueType.DUPLICATE_SKILL_NAME,
                            name=name,
                            paths=", ".join(sorted(paths)),
                        ),
                    )
                )

        for description, paths in sorted(desc_map.items()):
            if len(paths) > 1:
                issues.append(
                    Issue(
                        type=IssueType.DUPLICATE_DESCRIPTION.value,
                        message=issue_message(
                            IssueType.DUPLICATE_DESCRIPTION,
                            paths=", ".join(sorted(paths)),
                        ),
                    )
                )

    @staticmethod
    def _check_references(
        skills_root: Path,
        entries: list[SkillEntry],
        issues: list[Issue],
    ) -> None:
        """Every file in a skill's ``references/`` must be linked from SKILL.md."""
        for entry in entries:
            skill_dir = skills_root / entry.path
            references_dir = skill_dir / "references"
            if not references_dir.is_dir():
                continue

            skill_md = skill_dir / "SKILL.md"
            if not skill_md.is_file():
                continue
            body = skill_md.read_text(encoding="utf-8")

            unlinked: list[str] = []
            for ref_path in iter_files(references_dir):
                ref_name = ref_path.name
                # A reference is "linked" if its filename appears anywhere in SKILL.md.
                if ref_name not in body:
                    unlinked.append(
                        relpath(ref_path, skills_root)
                    )

            if unlinked:
                issues.append(
                    Issue(
                        type=IssueType.REFERENCE_NOT_LINKED.value,
                        message=issue_message(
                            IssueType.REFERENCE_NOT_LINKED,
                            paths=", ".join(sorted(unlinked)),
                        ),
                        path=entry.path,
                    )
                )


# Linter-local tree walkers (single-consumer, moved out of utility)

def assets_container(skills_root: Path) -> set[str]:
    """Category names that carry a declared DM2 asset-container marker.

    Linter-only: checks each non-ignored category directory for an
    ``ASSETS_MARKER_FILENAME`` whose frontmatter ``kind`` is ``assets``.
    """
    declared: set[str] = set()
    for category in category_dirs(skills_root):
        marker = category / ASSETS_MARKER_FILENAME
        if not marker.is_file():
            continue
        frontmatter = parse_frontmatter(marker)
        if frontmatter.get("kind") == "assets":
            declared.add(category.name)
    return declared


def iter_files(folder: Path) -> Iterator[Path]:
    """Yield every regular file under ``folder`` without following symlinks.

    Linter-only: deterministic (sorted names per directory); symlinked
    directories are listed but never descended, so a loop cannot hang
    the scan.
    """
    if not folder.is_dir():
        return
    for dirpath, dirnames, filenames in os.walk(folder, followlinks=False):
        dirnames.sort()
        for name in sorted(filenames):
            yield Path(dirpath) / name


def iter_relative_skill_mds(skills_root: Path, depth: int) -> Iterator[Path]:
    """Yield ``SKILL.md`` files exactly ``depth`` directories below the root.

    Linter-only: depth=1 is ``category/SKILL.md`` (invalid placement),
    depth=3 is ``category/pack/nested/SKILL.md`` (too deep). Hidden and
    ignored category directories are skipped.
    """
    pattern = "/".join(["*"] * depth + ["SKILL.md"])
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


def too_deep_exempt_paths(skills_root: Path) -> set[str]:
    """DM1 nested-pack exemption: ``category/pack/SKILL.md`` paths whose
    intermediate directory carries the ``pack.toml`` marker."""
    exempt: set[str] = set()
    for category in category_dirs(skills_root):
        for skill_md in category.glob("*/*/SKILL.md"):
            marker = skill_md.parent.parent / PACK_MARKER_FILENAME
            if marker.is_file():
                try:
                    exempt.add(str(skill_md.relative_to(skills_root)))
                except ValueError:
                    continue
    return exempt
