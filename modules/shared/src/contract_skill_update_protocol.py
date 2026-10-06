"""Skill-update protocol contract (capability ABC).

The update capability refreshes the shared skill pack from the source-of-truth
locations inside internal submodules (`crates/shared/skills/`,
`modules/shared/skills/`, `packages/shared/skills/`, the flat legacy layouts, or
the legacy `.agents/skills/`).

Provisioner (`ISkillProvisionProtocol`) owns lifecycle ops that touch the pack
(`provision`, `prune`, `audit`). Registry (`ISkillRegistryProtocol`) owns
informational / CLI-facing ops (`list`, `check`, `show`, `install`,
`uninstall`, `sync`). The update capability is a third seam: it pulls fresh
content upstream and merges it into the pack without touching provisioned
copies.
"""
from __future__ import annotations

from abc import ABC, abstractmethod

from modules.shared.src.taxonomy_skill_update_vo import UpdateResult


class ISkillUpdateProtocol(ABC):
    """Update capability contract: pull internal submodule skills into the pack."""

    @abstractmethod
    def update(
        self,
        tool_id: str = "",
        dry_run: bool = False,
        force: bool = False,
    ) -> UpdateResult:
        """Merge skills from the internal submodule source into the pack.

        Args:
            tool_id: When non-empty, limit the merge to one internal tool.
            dry_run: When true, only report what would be merged; write nothing.
            force: When true, overwrite pack skills whose bytes differ from
                the submodule source. Without it, conflicts are reported and
                skipped.

        Returns:
            Result reporting success, how many skills were merged, and a human-
            readable summary.
        """
        ...


__all__ = ["ISkillUpdateProtocol"]

# Layer-symbol registry (runtime reference for harness/loader introspection).
_layer_symbols = {
    "ISkillUpdateProtocol": ISkillUpdateProtocol,
}
