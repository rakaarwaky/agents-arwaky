"""Skill pack provisioning capability — delegates to shared skill_pack helpers.

Pack logic (provision/remove/prune/audit) lives in
:mod:`modules.shared.src.utility_skill_registry` (utility layer, shared with the
skill surface under AES201). This module adapts it to the single
``ISkillProtocol`` capability contract so the orchestrator stays thin.
"""
from __future__ import annotations

import sys
from pathlib import Path

from modules.shared.src.contract_skill_protocol import ISkillProtocol
from modules.shared.src.taxonomy_common_vo import PackFinding, audit_pack
from modules.shared.src.taxonomy_skill_vo import (
    ExitCode,
    SkillProvisionResult,
    ToolFilter,
)
from modules.shared.src.utility_paths_resolver import repo_root
from modules.shared.src.utility_skill_registry import (
    PACK_ROOT,
    get_tool_skills,
    provision_base,
    provision_single_skill,
    prune_provisioned,
)

__all__ = [
    "PackFinding",
    "SkillPackProvisioner",
    "prune_provisioned",
]


# ─── Block 1: Class Definition & Constructor ──────────────
class SkillPackProvisioner(ISkillProtocol):
    """Thin delegate over the shared skill_pack domain for a single tool."""

    def __init__(self) -> None:
        self._pack_root = repo_root() / "skills"

    # ─── Block 2: Protocol ABC Method Implementation ──────────
    def execute(
        self,
        op: str,
        skill: str | None = None,
        target: Path | None = None,
    ) -> ExitCode:
        """Dispatch one skill op (``provision`` | ``prune`` | ``audit``) to internal methods."""
        if op in {"provision", "install"}:
            result = self.install(
                ToolFilter(skill or "all"),
                Path(target) if target is not None else Path.cwd(),
            )
            return ExitCode(0 if result.success else 1)
        if op in {"prune", "remove"}:
            result = self.prune(Path(target) if target is not None else Path.cwd())
            return ExitCode(0 if result.success else 1)
        if op == "audit":
            return ExitCode(1 if self.audit() else 0)
        print(f"Unknown skill op: {op}", file=sys.stderr)
        return ExitCode(1)

    def install(
        self,
        tool_id: ToolFilter,
        target_dir: Path,
        custom_dest: str = "",
        force: bool = False,
        link: bool = False,
        prune: bool = False,
    ) -> SkillProvisionResult:
        """Provision every pack skill into the target workspace."""
        if prune:
            self.prune(target_dir, custom_dest)
        skills = get_tool_skills(str(tool_id)) if str(tool_id) != "all" else get_tool_skills("all")
        ok = 0
        for sf in skills:
            if provision_single_skill(sf, target_dir, custom_dest, force, link):
                ok += 1
        return SkillProvisionResult(
            ok > 0 or not skills,
            tool_id,
            ok,
            f"provisioned {ok} skill(s)",
        )

    # ─── Block 3: Dunder Methods, Factories & Helpers ───────
    def __repr__(self) -> str:
        return "SkillPackProvisioner()"

    def prune(self, target_dir: Path, custom_dest: str = "") -> SkillProvisionResult:
        base = provision_base(target_dir, custom_dest)
        removed = prune_provisioned(base, PACK_ROOT)
        # prune_provisioned returns a count (int) in current utility; older
        # call sites treated it as a list — normalise both shapes.
        n = removed if isinstance(removed, int) else len(removed)
        return SkillProvisionResult(
            True, "pack", n, f"removed {n} stale provisioned skill(s)"
        )

    def audit(self) -> list[PackFinding]:
        """Pack loadability findings; empty means clean."""
        return audit_pack(self._pack_root)
