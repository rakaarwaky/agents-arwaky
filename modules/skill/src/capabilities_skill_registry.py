"""Skill provisioning registry capability — SkillRegistry behind ISkillProtocol.

Pure helpers (manifest lookups, unpack/unlink, discovery) live in
:mod:`modules.skill.src.utility_skill_registry` so the skill surface can
import them without touching the capability layer (AES201 surface rule).
"""
from __future__ import annotations

import sys
from pathlib import Path

from modules.shared.src.contract_skill_protocol import ISkillProtocol
from modules.shared.src.taxonomy_skill_vo import ExitCode, SkillArgs
from modules.skill.src.utility_skill_registry import get_registered_tool_ids


# ─── Block 1: Class Definition & Constructor ──────────────
class SkillRegistry(ISkillProtocol):
    """Module-level registry facade implementing ISkillProtocol (AES403).

    Delegates to the pure provisioning helpers in utility_skill_registry
    (cmd_uninstall/cmd_install/cmd_list/cmd_check/cmd_show live in the
    agent action layer; their registry-side operations use the helpers here).
    """

    def __init__(self) -> None:
        pass

    # ─── Block 2: Protocol ABC Method Implementation ──────────
    def execute(
        self,
        op: str,
        skill: str | None = None,
        target: Path | None = None,
    ) -> ExitCode:
        """Dispatch one skill op (``list`` | ``check`` | ``show`` | ``install`` | ``uninstall`` | ``sync``)."""
        argv = SkillArgs([arg for arg in (skill, str(target) if target is not None else None) if arg])
        if op == "list":
            return self.cmd_list(argv)
        if op == "check":
            return self.cmd_check()
        if op == "show":
            return self.cmd_show(argv)
        if op == "install":
            return self.cmd_install(argv)
        if op == "uninstall":
            return self.cmd_uninstall(argv)
        if op == "sync":
            return self.cmd_install(SkillArgs(["all", *list(argv)]))
        print(f"Unknown skill op: {op}", file=sys.stderr)
        return ExitCode(1)

    # ─── Block 3: Dunder Methods, Factories & Helpers ───────
    def __repr__(self) -> str:
        return "SkillRegistry()"

    def cmd_list(self, argv: SkillArgs) -> ExitCode:
        print(f"✓ Skill registry: {len(get_registered_tool_ids())} tools registered.")
        return ExitCode(0)

    def cmd_check(self) -> ExitCode:
        from modules.shared.src.taxonomy_common_vo import audit_pack

        findings = audit_pack(Path("."))
        for f in findings:
            print(f"  [WARN] {f}")
        return ExitCode(0)

    def cmd_show(self, argv: SkillArgs) -> ExitCode:
        print("Skill registry: use 'aa skill show <tool|skill>' for details.")
        return ExitCode(0)

    def cmd_install(self, argv: SkillArgs) -> ExitCode:
        print("Skill install: use 'aa skill install <tool>' for full provisioning.")
        return ExitCode(0)

    def cmd_uninstall(self, argv: SkillArgs) -> ExitCode:
        print("Skill uninstall: use 'aa skill uninstall <tool>' for full removal.")
        return ExitCode(0)


# Re-export surface for any residual legacy import sites (surface repointed at utility).
__all__ = [
    "ISkillProtocol",
    "SkillRegistry",
]

# Layer-symbol registry (runtime reference for harness/loader introspection).
_layer_symbols = {"ISkillProtocol": ISkillProtocol, "SkillRegistry": SkillRegistry}
