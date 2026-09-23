"""Skill pack provisioning capability — delegates to the shared skill_pack domain.

All pack logic (install/prune/check/audit, provenance, loadability) lives in
:mod:`modules.skill.src.capabilities_skill_registry` — a 1:1 exact port of
``tools/skill/skill.py``. This module adapts it to the single
``ISkillProtocol`` capability contract so the orchestrator stays thin.
"""
from __future__ import annotations

import importlib
import sys
from pathlib import Path

from modules.shared.src.contract_skill_protocol import ISkillProtocol
from modules.shared.src.taxonomy_common_vo import PackFinding
from modules.shared.src.taxonomy_skill_vo import (
    ExitCode,
    SkillProvisionResult,
    ToolFilter,
)
from modules.shared.src.utility_paths_resolver import repo_root
from modules.skill.src.utility_skill_pack import prune_provisioned

__all__ = [
    "PackFinding",
    "SkillPackProvisioner",
    "prune_provisioned",
]

_reg = importlib.import_module("modules.skill.src.capabilities_skill_registry")


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
