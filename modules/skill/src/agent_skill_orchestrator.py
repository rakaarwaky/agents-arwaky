"""Skill agent orchestrator — coordinates registry + pack provisioner."""
from __future__ import annotations

from pathlib import Path

from modules.shared.src.skill.contract_skill_aggregate import ISkillAggregate
from modules.shared.src.skill.contract_skill_protocol import ISkillProvisioner
from modules.skill.src.capabilities_skill_registry import SkillRegistry


class SkillOrchestrator(ISkillAggregate):
    """Zero-I/O routing of skill surface verbs to the capabilities.

    # Block 1: Constructor
    # Block 2: Query verbs (list/check/show)
    # Block 3: Mutation verbs (install/uninstall/sync)
    """

    # -- Block 1: Constructor ---------------------------------------------------
    def __init__(self, registry: SkillRegistry, provisioner: ISkillProvisioner) -> None:
        self._registry = registry
        self._provisioner = provisioner

    # -- Block 2: Query verbs -----------------------------------------------------
    def list_skills(self, tool_filter: str = "") -> int:
        """TODO(AES): port the tabular listing from tools/skill/skill.py cmd_list."""
        infos = self._registry.get_registered_tool_ids()
        for info in infos:
            print(f"{info.tool_id} [{info.category}]: {info.description}")
        return 0

    def check_skills(self) -> int:
        findings = self._provisioner.audit()
        for finding in findings:
            print(f"  ! {finding.code}: {finding.message}")
        if not findings:
            print("Loadability: clean (layout, names, descriptions, budget)")
            return 0
        print(f"Loadability findings ({len(findings)}).")
        return 1

    def show_skill(self, query: str) -> int:
        """TODO(AES): port the SKILL.md display from tools/skill/skill.py cmd_show."""
        if self._registry.normalize_tool_id(query):
            print(f"Tool '{query}' has skills in the shared pack (see 'aa skill list').")
            return 0
        print(f"Skill or tool '{query}' not found.")
        return 1

    # -- Block 3: Mutation verbs ----------------------------------------------------
    def install_skills(self, args: list[str]) -> int:
        """Parse the install/copy/get/add/sync args and provision skills."""
        from modules.skill.src.surface_skill_command import parse_skill_args

        parsed = parse_skill_args(args)
        if parsed.get("prune"):
            self._provisioner.prune(Path(parsed.get("target", ".")), parsed.get("dest", ""))
        target_name = parsed.get("target_name")
        if not target_name:
            print("Usage: aa skill install <tool-name|skill-name|all> [--target <dir>] [--force] [--prune]")
            return 1
        tool_id = self._registry.normalize_tool_id(target_name) or target_name
        result = self._provisioner.install(
            tool_id,
            Path(parsed.get("target", ".")),
            parsed.get("dest", ""),
            parsed.get("force", False),
            parsed.get("link", False),
            parsed.get("prune", False),
        )
        print(result.message)
        return 0 if result.success else 1

    def uninstall_skills(self, args: list[str]) -> int:
        """Parse the uninstall/unskill/remove/delete args and prune."""
        from modules.skill.src.surface_skill_command import parse_skill_args

        parsed = parse_skill_args(args)
        target_name = parsed.get("target_name")
        if not target_name:
            print("Usage: aa skill uninstall <tool-name|skill-name|all> [--target <dir>]")
            return 1
        result = self._provisioner.prune(Path(parsed.get("target", ".")), parsed.get("dest", ""))
        print(result.message)
        return 0 if result.success else 1

    def sync_skills(self, args: list[str]) -> int:
        """'sync' = install all (alias semantics from tools/skill/skill.py)."""
        return self.install_skills(["all", *args])
