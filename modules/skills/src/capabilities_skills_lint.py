"""Skills lint capability (AES capabilities layer).

Implements ``ISkillsLintProtocol``: a combined scan that runs the
13-rule validator plus the weed report in one pass, returning a single
``LintReport``. The lint is read-only — it reports, it never writes.

The lint supports an optional *category* filter: when provided, only
issues whose ``category`` or ``path`` belongs to that category are
included in the report. The weed lines are not filtered (they are
library-wide duplicate/empty-category signals).
"""

from __future__ import annotations

from pathlib import Path

from modules.shared.src.skills.contract_skills_protocol import (
    ISkillsLintProtocol,
    ISkillsMutatorProtocol,
    ISkillsValidatorProtocol,
)
from modules.shared.src.skills.taxonomy_skills_authoring_vo import (
    LintReport,
    MutationPlan,
    ValidationReport,
)
from modules.shared.src.skills.taxonomy_skills_vo import SkillsRoot

__all__ = ["SkillsLint"]


class SkillsLint(ISkillsLintProtocol):
    """Combined lint: validator checks + weed report, optionally category-filtered."""

    def __init__(
        self,
        validator: ISkillsValidatorProtocol | None = None,
        mutator: ISkillsMutatorProtocol | None = None,
    ) -> None:
        self._validator = validator
        self._mutator = mutator

    def lint(
        self, root: SkillsRoot, category: str | None = None
    ) -> LintReport:
        """Run the full lint over *root*; optionally filter by *category*.

        Delegates to the validator for the 13-rule checks and to the
        mutator's ``plan_weed`` for the weed lines. When *category* is
        set, issues are narrowed to that category; weed lines are kept
        as-is (library-wide signals).
        """
        skills_root = Path(root)

        # ── 1. Validator: 13-rule checks ─────────────────────────
        if self._validator is not None:
            report: ValidationReport = self._validator.validate(skills_root)
        else:
            # Lazy default: instantiate the concrete validator directly.
            from modules.skills.src.capabilities_skills_validator import SkillsValidator
            report = SkillsValidator().validate(skills_root)

        # ── 2. Mutator: weed report ──────────────────────────────
        weed_lines: tuple[str, ...] = ()
        if self._mutator is not None:
            plan: MutationPlan = self._mutator.plan_weed(skills_root)
            weed_lines = plan.lines
        else:
            from modules.skills.src.capabilities_skills_mutator import SkillsMutator
            plan = SkillsMutator().plan_weed(skills_root)
            weed_lines = plan.lines

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
