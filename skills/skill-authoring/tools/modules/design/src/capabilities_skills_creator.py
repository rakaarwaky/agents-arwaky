"""Skills creator capability (AES capabilities layer).

Implements ``ISkillsCreatorProtocol``: create skills and categories in the
pack (dry-run by default). Absorbs the old ``create`` and ``new-category``
verbs from the retired ``SkillsMutator``.

Shared helpers (``validate_category_name``, ``assert_within_root``,
``write_category_description``) live in ``utility_skills_mutation``
(shared kernel) so the creator never imports a sibling capability.

Every computed destination is asserted to remain inside the skills root
at plan time **and** re-checked at apply time, so a symlink created
between the two fails closed instead of writing outside the pack.
"""

from __future__ import annotations

from pathlib import Path

from shared.src.common.taxonomy_common_constant import (
    CATEGORY_DESCRIPTION_FILENAME,
)
from shared.src.common.taxonomy_common_vo import (
    CategoryName,
    SkillName,
)
from shared.src.design.contract_skills_protocol import (
    ISkillsCreatorProtocol,
)
from shared.src.design.taxonomy_skills_request import SkillsRoot
from shared.src.design.taxonomy_skills_vo import (
    NewCategoryPlan,
    SkillCreatePlan,
)
from shared.src.maintenance.utility_skills_mutation import (
    assert_within_root,
    validate_category_name,
    write_category_description,
)

__all__ = ["SkillsCreator"]


# ─── Block 1: Module Declaration ───
class SkillsCreator(ISkillsCreatorProtocol):
    """Creates skills and categories in the pack (dry-run by default)."""

    # ─── Block 2: Module Contract ───
    def create_skill(
        self,
        skill: SkillName,
        category: str,
        description: str,
        when_to_use: str,
        argument_hint: str,
        body: str,
        root: SkillsRoot,
        apply: bool,
    ) -> SkillCreatePlan:
        """Plan (or apply) creating a new skill SKILL.md.

        When ``apply`` is False the returned plan is a preview.
        When True, the file is written.
        """
        skills_root = Path(root)
        directory = skills_root / category / skill
        skill_md = directory / "SKILL.md"

        plan = SkillCreatePlan(
            skill=skill,
            category=category,
            description=description,
            when_to_use=when_to_use,
            argument_hint=argument_hint,
            body=body,
            directory=directory,
            skill_md=skill_md,
            already_exists=skill_md.exists(),
            root=skills_root,
        )

        if plan.already_exists or not apply:
            return plan

        directory.mkdir(parents=True, exist_ok=True)
        frontmatter = (
            "---\n"
            f"name: {skill}\n"
            f"description: {description}\n"
            f'when-to-use: "{when_to_use}"\n'
            f"argument-hint: {argument_hint}\n"
            "---\n\n"
        )
        skill_md.write_text(frontmatter + body, encoding="utf-8")
        return plan

    def create_category(
        self,
        name: CategoryName,
        description: str,
        root: SkillsRoot,
        force: bool,
        apply: bool,
    ) -> NewCategoryPlan:
        """Plan (or apply) creating a category folder + DESCRIPTION.md.

        When ``apply`` is False the returned plan is a preview.
        When True, the directory and description file are written.
        """
        skills_root = Path(root)
        validate_category_name(name)

        category = skills_root / name
        resolved_description = description or f"Skills in the {name} category."
        desc_file = category / CATEGORY_DESCRIPTION_FILENAME
        will_write = not (desc_file.exists() and not force)

        assert_within_root(category, skills_root)

        plan = NewCategoryPlan(
            name=name,
            description=resolved_description,
            directory=category,
            description_file=desc_file,
            will_write=will_write,
            root=skills_root,
        )

        if not apply:
            return plan

        plan.directory.mkdir(exist_ok=True)
        if plan.root is not None:
            assert_within_root(plan.description_file, plan.root)
        wrote = write_category_description(
            plan.directory, plan.description, force=plan.will_write
        )
        return NewCategoryPlan(
            name=plan.name,
            description=plan.description,
            directory=plan.directory,
            description_file=plan.description_file,
            will_write=plan.will_write,
            created=wrote,
            root=plan.root,
        )

    # ─── Block 3: Module Helpers ───
    def __repr__(self) -> str:
        return "SkillsCreator()"
