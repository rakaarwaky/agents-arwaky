"""Skill agent orchestrator — coordinates registry + pack provisioner.

Dispatches every surface action to the original command handlers, ported
as-is from tools/skill/skill.py into the registry adapter (injected as a
concrete capability object by the root composition layer).
"""
from __future__ import annotations

from pathlib import Path
from typing import Protocol

from modules.shared.src.contract_skill_aggregate import ISkillAggregate
from modules.shared.src.contract_skill_protocol import ISkillProtocol
from modules.shared.src.taxonomy_skill_vo import (
    FILTER_EMPTY,
    QUERY_EMPTY,
    ExitCode,
    SkillArgs,
    SkillQuery,
    ToolFilter,
)


class _SkillRegistry(Protocol):
    """Registry surface the orchestrator drives (named ops beyond ``execute``)."""

    def list(self, argv: SkillArgs) -> ExitCode:
        """List all registered skill tools, optionally filtered by tool name."""
        ...
    def check(self) -> ExitCode:
        """Check that all provisioned skills are loadable and valid."""
        ...
    def show(self, argv: SkillArgs) -> ExitCode:
        """Show metadata for one or more skill tools."""
        ...
    def install(self, argv: SkillArgs) -> ExitCode:
        """Install or update skill tools into the target harness."""
        ...
    def uninstall(self, argv: SkillArgs) -> ExitCode:
        """Remove provisioned skill tools from the target harness."""
        ...
    def sync(self, argv: SkillArgs) -> ExitCode:
        """Sync skills from the pack to the target harness."""
        ...
    def execute(
        self,
        op: str,
        skill: str | None = None,
        target: Path | None = None,
    ) -> ExitCode:
        """Execute a skill op by name with optional args and target."""
        ...


# ─── Block 1: Class Definition & Constructor ──────────────
class SkillOrchestrator(ISkillAggregate):
    """Routing of skill surface actions to the capabilities (original bodies)."""

    def __init__(self, provisioner: ISkillProtocol, registry: _SkillRegistry) -> None:
        self._provisioner = provisioner
        self._registry = registry

    # ─── Block 2: Aggregate Method Implementation ──────────
    def list(self, tool_filter: ToolFilter = FILTER_EMPTY) -> ExitCode:
        """Port of tools/skill/skill.py cmd_list."""
        argv = SkillArgs([str(tool_filter)] if tool_filter else [])
        return ExitCode(self._registry.list(argv))

    def check(self) -> ExitCode:
        """Port of tools/skill/skill.py cmd_check."""
        return ExitCode(self._registry.check())

    def show(self, query: SkillQuery = QUERY_EMPTY) -> ExitCode:
        """Port of tools/skill/skill.py cmd_show."""
        return ExitCode(self._registry.show(SkillArgs([str(query)] if query else [])))

    def install(self, args: SkillArgs) -> ExitCode:
        """Port of tools/skill/skill.py cmd_install."""
        return ExitCode(self._registry.install(args))

    def uninstall(self, args: SkillArgs) -> ExitCode:
        """Port of tools/skill/skill.py cmd_uninstall."""
        return ExitCode(self._registry.uninstall(args))

    def sync(self, args: SkillArgs) -> ExitCode:
        """'sync' = install all (alias semantics from tools/skill/skill.py)."""
        return ExitCode(self._registry.sync(args))

    # ─── Block 3: Dunder Methods, Factories & Helpers ─────
    def execute(
        self,
        op: str,
        skill: str | None = None,
        target: Path | None = None,
    ) -> ExitCode:
        """Dispatch one skill op to the provisioner or registry capability."""
        if op in {"provision", "prune", "remove", "audit"}:
            return ExitCode(self._provisioner.execute(op, skill, target))
        return ExitCode(self._registry.execute(op, skill, target))

    def __repr__(self) -> str:
        return "SkillOrchestrator()"


__all__ = [
    "ExitCode",
    "ISkillAggregate",
    "ISkillProtocol",
    "SkillArgs",
    "SkillQuery",
    "ToolFilter",
]

# Layer-symbol registry (runtime reference for harness/loader introspection).
_layer_symbols = {
    "ExitCode": ExitCode,
    "SkillArgs": SkillArgs,
    "SkillQuery": SkillQuery,
    "ToolFilter": ToolFilter,
}
