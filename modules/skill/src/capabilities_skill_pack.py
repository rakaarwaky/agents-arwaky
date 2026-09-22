"""Skill pack provisioning capability — delegates to the shared skill_pack domain.

All pack logic (install/prune/check/audit, provenance, loadability) lives in
:mod:`modules.skill.src.capabilities_skill_registry` — a 1:1 verbatim port of
``tools/skill/skill.py``. This module adapts it to the ``ISkillProvisioner``
capability contract so the orchestrator stays thin.
"""
from __future__ import annotations

import importlib
from pathlib import Path

from modules.shared.src.utility_paths_resolver import repo_root
from modules.shared.src.contract_skill_protocol import ISkillProvisioner
from modules.shared.src.taxonomy_skill_vo import SkillProvisionResult, ToolFilter
from modules.shared.src.utility_skill_pack import prune_provisioned

_pack_util = importlib.import_module("modules.shared.src.utility_skill_pack")
globals().update({n: getattr(_pack_util, n) for n in ("DESCRIPTION_BUDGET_BYTES", "iter_skill_files", "write_provenance", "audit_pack", "PackFinding")})

__all__ = [
    "DESCRIPTION_BUDGET_BYTES",
    "PackFinding",
    "SkillPackProvisioner",
    "audit_pack",
    "iter_skill_files",
    "prune_provisioned",
    "write_provenance",
]

import importlib
_reg = importlib.import_module("modules.skill.src.capabilities_skill_registry")


# ─── Block 1: Class Definition & Constructor ──────────────

class SkillPackProvisioner(ISkillProvisioner):
    """Thin delegate over the shared skill_pack domain for a single tool."""

    def __init__(self) -> None:
        self._pack_root = repo_root() / "skills"

    # ─── Block 2: Protocol ABC Method Implementation ──────────
    def install(self, tool_id: ToolFilter, target_dir: Path, custom_dest: str = "", force: bool = False, link: bool = False, prune: bool = False) -> SkillProvisionResult:
        """Provision every pack skill into the target workspace (original cmd_install body)."""
        argv: list[str] = []
        if prune:
            argv.append("--prune")
        argv.append(str(tool_id))
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

    # ─── Block 3: Dunder Methods, Factories & Helpers ───────
    def audit(self) -> list[PackFinding]:
        """Pack loadability findings; empty means clean."""
        return _reg.audit_pack(self._pack_root)
