"""Skill provisioning registry capability — SkillRegistry behind ISkillRegistryProtocol.

Pure helpers (manifest lookups, unpack/unlink, discovery) live in
:mod:`modules.shared.src.utility_skill_registry` so the skill surface can
import them without touching the capability layer (AES201 surface rule).
"""
from __future__ import annotations

from pathlib import Path

from modules.shared.src.contract_skill_protocol import ISkillRegistryProtocol
from modules.shared.src.taxonomy_skill_vo import ExitCode, SkillArgs
from modules.shared.src.utility_skill_registry import get_registered_tool_ids


# ─── Block 1: Class Definition & Constructor ──────────────
class SkillRegistry(ISkillRegistryProtocol):
    """Module-level registry facade implementing ISkillRegistryProtocol (AES403).

    Delegates to the pure provisioning helpers in utility_skill_registry
    (cmd_uninstall/cmd_install/cmd_list/cmd_check/cmd_show live in the
    agent action layer; their registry-side operations use the helpers here).
    """

    def __init__(self) -> None:
        pass

    # ─── Block 2: Protocol Method Implementation ──────────────
    def list(self, tool_filter: str = "") -> ExitCode:
        """Report the count of tools registered in the shared pack."""
        print(f"✓ Skill registry: {len(get_registered_tool_ids())} tools registered.")
        return ExitCode(0)

    def check(self) -> ExitCode:
        """Audit pack loadability and print any findings."""
        from modules.shared.src.taxonomy_common_vo import audit_pack

        findings = audit_pack(Path("."))
        for f in findings:
            print(f"  [WARN] {f}")
        return ExitCode(0)

    def show(self, query: str = "") -> ExitCode:
        """Point the caller to the CLI surface for skill detail views."""
        print("Skill registry: use 'aa skill show <tool|skill>' for details.")
        return ExitCode(0)

    def install(self, args: SkillArgs) -> ExitCode:
        """Point the caller to the CLI surface for full provisioning."""
        print("Skill install: use 'aa skill install <tool>' for full provisioning.")
        return ExitCode(0)

    def uninstall(self, args: SkillArgs) -> ExitCode:
        """Point the caller to the CLI surface for full removal."""
        print("Skill uninstall: use 'aa skill uninstall <tool>' for full removal.")
        return ExitCode(0)

    def sync(self, args: SkillArgs) -> ExitCode:
        """Point the caller to the CLI surface for a sync (alias for install all)."""
        print("Skill sync: use 'aa skill sync' for full provisioning.")
        return ExitCode(0)

    # ─── Block 3: Dunder Methods, Factories & Helpers ─────────
    def __repr__(self) -> str:
        return "SkillRegistry()"


# Re-export surface for any residual legacy import sites (surface repointed at utility).
__all__ = [
    "ISkillRegistryProtocol",
    "SkillRegistry",
]

# Layer-symbol registry (runtime reference for harness/loader introspection).
_layer_symbols = {"ISkillRegistryProtocol": ISkillRegistryProtocol, "SkillRegistry": SkillRegistry}
