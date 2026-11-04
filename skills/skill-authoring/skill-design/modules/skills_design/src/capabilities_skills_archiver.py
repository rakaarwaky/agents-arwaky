"""Skills archiver capability (AES capabilities layer).

Implements ``ISkillsArchiverProtocol``: plan/apply an archive of a skill
into ``_archive/`` (dry-run by default). Split from the retired
``SkillsMutator`` so each mutation verb owns one capability file.

Shared helpers (``resolve_skill_dir``, ``assert_within_root``,
``archive_root``) live in ``utility_skills_mutation`` (shared kernel)
so the archiver never imports a sibling capability.

Every computed destination is asserted to remain inside the skills root
at plan time **and** re-checked at apply time, so a symlink created
between the two fails closed instead of writing outside the pack.
"""

from __future__ import annotations

import shutil
from pathlib import Path

from skills_design.src.contract_skills_protocol import (
    ISkillsArchiverProtocol,
)
from skills_design.src.taxonomy_skills_authoring_vo import (
    MutationOutcome,
    MutationPlan,
)
from skills_design.src.taxonomy_skills_error import (
    MutationConflictError,
    SkillsUsageError,
)
from skills_design.src.taxonomy_skills_rule_vo import SkillName
from skills_design.src.taxonomy_skills_vo import SkillsRoot
from skills_design.src.utility_skills_mutation import (
    archive_root,
    assert_within_root,
    resolve_skill_dir,
)

__all__ = ["SkillsArchiver"]


# ─── Block 1: Class Definition & Constructor ──────────────
class SkillsArchiver(ISkillsArchiverProtocol):
    """Plans and applies an archive of a skill into ``_archive/``."""

    # ─── Block 2: Protocol Method Implementation ─────────────
    def plan_archive(self, skill: SkillName, root: SkillsRoot) -> MutationPlan:
        """Resolve an archive; the skill lands at ``_archive/<cat>/<skill>/``."""
        skills_root = Path(root)
        source = resolve_skill_dir(skill, skills_root)
        category = source.parent.name
        destination = archive_root(skills_root) / category / source.name

        if destination.exists():
            raise MutationConflictError(
                f"Archive destination already exists: {destination}"
            )

        assert_within_root(destination, skills_root)

        return MutationPlan(
            kind="archive",
            source=source,
            destination=destination,
            root=skills_root,
        )

    def apply_archive(self, plan: MutationPlan) -> MutationOutcome:
        """Execute an archive plan; re-checks containment first."""
        root = plan.root
        if plan.source is None or plan.destination is None:
            raise SkillsUsageError("Archive plan is missing its paths")
        # Pre-apply containment check is the TOCTOU fail-closed guard; the
        # post-mkdir re-check below is redundant (mkdir can only create dirs
        # inside an already-contained parent) and is dropped.
        assert_within_root(plan.destination, root)
        plan.destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(plan.source), str(plan.destination))
        archived_md = plan.destination / "SKILL.md"
        if archived_md.exists():
            archived_md.rename(plan.destination / "SKILL.md.archived")
        return MutationOutcome(message="archived")

    # ─── Block 3: Dunder Methods, Factories & Helpers ─────────
    def __repr__(self) -> str:
        return "SkillsArchiver()"
