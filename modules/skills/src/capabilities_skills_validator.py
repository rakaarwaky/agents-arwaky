"""Skills validator capability (AES capabilities layer).

Implements ``ISkillsValidatorProtocol``: the 13 issue checks ported from
``skills/skill-authoring/scripts/validate.py`` (itself lifted from
``librarian.py``). Issue-type strings and message templates come from
the shared rule SSOT, so the checker and the generated rules doc cannot
drift apart.

The report is unfiltered by design: ``--category`` and ``--rules-only``
narrow what the surface lists, never what the validator finds, so the
exit code cannot report a library clean while issues exist outside the
scope.
"""

from __future__ import annotations

from pathlib import Path

from modules.shared.src.skills.contract_skills_protocol import (
    ISkillsValidatorProtocol,
)
from modules.shared.src.skills.taxonomy_skills_authoring_vo import ValidationReport
from modules.shared.src.skills.taxonomy_skills_constant import (
    MAX_DESCRIPTION_LEN,
    IssueType,
    is_valid_skill_name,
    issue_message,
)
from modules.shared.src.skills.taxonomy_skills_entity import (
    CategorySummary,
    Issue,
    SkillEntry,
)
from modules.shared.src.skills.taxonomy_skills_vo import SkillsRoot
from modules.shared.src.utility_skills_tree import (
    assets_container,
    category_dirs,
    category_summaries,
    iter_files,
    iter_relative_skill_mds,
    relpath,
    skill_entries,
    too_deep_exempt_paths,
)

__all__ = ["SkillsValidator"]


# ─── Block 1: Class Definition & Constructor ──────────────
class SkillsValidator(ISkillsValidatorProtocol):
    """Runs the 13 checks over an explicit skills root."""

    # ─── Block 2: Protocol Method Implementation ──────────────
    def validate(self, root: SkillsRoot) -> ValidationReport:
        """Return the unfiltered validation report for ``root``."""
        skills_root = Path(root)
        entries = skill_entries(skills_root)
        categories = category_summaries(entries, skills_root)
        assets = assets_container(skills_root)

        issues: list[Issue] = []

        self._check_categories(categories, assets, issues)
        self._check_entries(skills_root, entries, issues)
        self._check_placement(skills_root, issues)
        self._check_duplicates(entries, issues)

        return ValidationReport(
            skills_root=skills_root,
            catalog=skills_root / "CATALOG.md",
            issues=tuple(issues),
            skills=len(entries),
            categories=len(list(category_dirs(skills_root))),
        )

    # ─── Block 3: Dunder Methods, Factories & Helpers ─────────
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

            skill_dir = skills_root / entry.path
            nested = [
                relpath(path, skills_root)
                for path in iter_files(skill_dir)
                if path.name == "SKILL.md" and path != skill_dir / "SKILL.md"
            ]

            if nested:
                issues.append(
                    Issue(
                        type=IssueType.NESTED_SKILL_MD.value,
                        message=issue_message(
                            IssueType.NESTED_SKILL_MD, paths=", ".join(nested)
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
