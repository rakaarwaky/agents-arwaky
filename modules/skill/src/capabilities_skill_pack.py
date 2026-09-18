"""Skill pack provisioning capability — delegates to the shared skill_pack domain.

All pack logic (install/prune/check/audit, provenance, loadability) lives in
:mod:`modules.skill.src.capabilities_skill_registry` — a 1:1 verbatim port of
``tools/skill/skill.py``. This module adapts it to the ``ISkillProvisioner``
capability contract so the orchestrator stays thin.
"""
from __future__ import annotations

from pathlib import Path

from modules.shared.src.paths.utility_paths import repo_root
from modules.shared.src.skill.contract_skill_protocol import ISkillProvisioner
from modules.shared.src.skill.taxonomy_skill_vo import SkillProvisionResult
from modules.shared.src.skill_pack.capabilities_skill_pack import (
    PackFinding,
    prune_provisioned,
)

from modules.skill.src import capabilities_skill_registry as _reg


class SkillPackProvisioner(ISkillProvisioner):
    """Thin delegate over the shared skill_pack domain for a single tool.

    # Block 1: Constructor
    # Block 2: Install / prune
    # Block 3: Audit
    """

    # -- Block 1: Constructor ---------------------------------------------------
    def __init__(self) -> None:
        self._pack_root = repo_root() / "skills"

    # -- Block 2: Install / prune ----------------------------------------------------
    def install(self, tool_id: str, target_dir: Path, custom_dest: str = "", force: bool = False, link: bool = False, prune: bool = False) -> SkillProvisionResult:
        """Provision every pack skill into the target workspace (original cmd_install body)."""
        argv: list[str] = []
        if prune:
            argv.append("--prune")
        argv.append(tool_id)
        argv += ["--target", str(target_dir)]
        if custom_dest:
            argv += ["--dest", custom_dest]
        if force:
            argv.append("--force")
        if link:
            argv.append("--link")
        rc = _reg.cmd_install(argv)
        return SkillProvisionResult(rc == 0, tool_id, 0, f"install exit code {rc}")

    def prune(self, target_dir: Path, custom_dest: str = "") -> SkillProvisionResult:
        base = _reg._provision_base(target_dir, custom_dest)
        removed = prune_provisioned(base, _reg.PACK_ROOT)
        return SkillProvisionResult(True, "pack", len(removed), f"removed {len(removed)} stale provisioned skill(s)")

    # -- Block 3: Audit --------------------------------------------------------------
    def audit(self) -> list[PackFinding]:
        """Pack loadability findings; empty means clean."""
        return _reg.audit_pack(self._pack_root)
