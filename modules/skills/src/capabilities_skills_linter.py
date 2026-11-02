"""Skills linter capability (AES capabilities layer).

Implements ``ISkillsLinterProtocol``: a combined scan that runs the
13-rule validator plus the weed report in one pass, returning a single
``LintReport``. The lint is read-only — it reports, it never writes.

The lint supports an optional *category* filter: when provided, only
issues whose ``category`` or ``path`` belongs to that category are
included in the report. The weed lines are not filtered (they are
library-wide duplicate/empty-category signals).

The validator and weed-plan are consumed through their contract
protocols (``ISkillsValidatorProtocol`` / the shared
``utility_skills_mutation.plan_weed``), never through a sibling
capability import.
"""

from __future__ import annotations

from pathlib import Path

from modules.shared.src.skills.contract_skills_protocol import (
    ISkillsLinterProtocol,
    ISkillsValidatorProtocol,
)
from modules.shared.src.skills.taxonomy_skills_authoring_vo import (
    LintReport,
    ValidationReport,
)
from modules.shared.src.skills.taxonomy_skills_vo import SkillsRoot
from modules.skills.src.utility_skills_mutation import plan_weed

__all__ = ["SkillsLinter"]


class SkillsLinter(ISkillsLinterProtocol):
    """Combined lint: validator checks + weed report, optionally category-filtered."""

    def __init__(self, validator: ISkillsValidatorProtocol) -> None:
        self._validator = validator

    def lint(
        self, root: SkillsRoot, category: str | None = None
    ) -> LintReport:
        """Run the full lint over *root*; optionally filter by *category*.

        Delegates to the validator for the 13-rule checks and to the
        shared ``plan_weed`` helper for the weed lines. When *category* is
        set, issues are narrowed to that category; weed lines are kept
        as-is (library-wide signals).
        """
        skills_root = Path(root)

        # ── 1. Validator: 13-rule checks ─────────────────────────
        report: ValidationReport = self._validator.validate(skills_root)

        # ── 2. Weed report ───────────────────────────────────────
        weed_plan = plan_weed(skills_root)
        weed_lines = weed_plan.lines

        # ── 3. Category filter ───────────────────────────────────
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
