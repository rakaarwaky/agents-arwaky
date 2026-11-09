"""Skills mover capability (AES capabilities layer).

Implements ``ISkillsMoverProtocol``: plan/apply a move of a skill to
another category (dry-run by default). Split from the retired
``SkillsMutator`` so each mutation verb owns one capability file.

Shared helpers (``resolve_skill_dir``, ``validate_category_name``,
``assert_within_root``) live in ``utility_skills_mutation`` (shared
kernel) so the mover never imports a sibling capability.

Every computed destination is asserted to remain inside the skills root
at plan time **and** re-checked at apply time, so a symlink created
between the two fails closed instead of writing outside the pack.
"""

from __future__ import annotations

import shutil
from pathlib import Path

from shared.src.common.taxonomy_common_error import (
    MutationConflictError,
    SkillsUsageError,
)
from shared.src.common.taxonomy_common_vo import (
    CategoryName,
    SkillName,
)
from shared.src.design.contract_skills_protocol import (
    ISkillsMoverProtocol,
)
from shared.src.design.taxonomy_skills_request import SkillsRoot
from shared.src.design.taxonomy_skills_vo import (
    MutationOutcome,
    MutationPlan,
)
from shared.src.discovery.utility_discovery_core import relpath
from shared.src.maintenance.utility_skills_mutation import (
    assert_within_root,
    resolve_skill_dir,
    validate_category_name,
)

__all__ = ["SkillsMover"]


# ─── Block 1: Class Definition & Constructor ──────────────
class SkillsMover(ISkillsMoverProtocol):
    """Plans and applies a move of a skill to another category."""

    # ─── Block 2: Protocol Method Implementation ─────────────
    def plan_move(
        self, skill: SkillName, target: CategoryName, root: SkillsRoot
    ) -> MutationPlan:
        """Resolve a move; the returned plan takes no action."""
        skills_root = Path(root)
        source = resolve_skill_dir(skill, skills_root)
        validate_category_name(target)

        target_dir = skills_root / target

        if not target_dir.is_dir():
            raise SkillsUsageError(
                f"Target category does not exist: {target}. "
                "Create it first with sac skills create category."
            )

        destination = target_dir / source.name

        if source.parent.resolve() == target_dir.resolve():
            return MutationPlan(
                kind="move",
                source=source,
                destination=destination,
                already_in_category=True,
                root=skills_root,
            )

        if destination.exists():
            raise MutationConflictError(
                f"Destination already exists: {relpath(destination, skills_root)}"
            )

        assert_within_root(destination, skills_root)

        return MutationPlan(
            kind="move",
            source=source,
            destination=destination,
            root=skills_root,
        )

    def apply_move(self, plan: MutationPlan) -> MutationOutcome:
        """Execute a move plan; re-checks containment first."""
        root = plan.root
        if plan.source is None or plan.destination is None:
            raise SkillsUsageError("Move plan is missing its paths")
        if root is not None:
            assert_within_root(plan.destination, root)
        shutil.move(str(plan.source), str(plan.destination))
        return MutationOutcome(message="moved")

    # ─── Block 3: Dunder Methods, Factories & Helpers ─────────
    def __repr__(self) -> str:
        return "SkillsMover()"
