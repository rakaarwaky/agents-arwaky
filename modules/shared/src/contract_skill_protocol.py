"""Skill-domain protocol contracts (capability ABCs).

The skill feature exposes two orthogonal capability roles:

- **Provisioner** owns the lifecycle ops that touch the shared skill pack
  (`provision`, `prune`, `audit`). `SkillPackProvisioner` implements this
  protocol.
- **Registry** owns the informational / CLI-facing ops (`list`, `check`,
  `show`, `install`, `uninstall`, `sync`). `SkillRegistry` /
  `SkillRegistryAdapter` implement this protocol.

Consumers route to the right role via the single ``ISkillAggregate.execute``
entry point; no single capability owns all ops (AES405).
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path

from modules.shared.src.taxonomy_common_vo import PackFinding
from modules.shared.src.taxonomy_skill_vo import (
    DEST_EMPTY,
    FILTER_EMPTY,
    QUERY_EMPTY,
    ExitCode,
    PackFindingList,
    SkillArgs,
    SkillDest,
    SkillProvisionResult,
    SkillQuery,
    ToolFilter,
)


class ISkillProvisionProtocol(ABC):
    """Provisioner capability contract: one method per pack lifecycle op."""

    @abstractmethod
    def provision(
        self,
        tool_id: ToolFilter,
        target_dir: Path,
        custom_dest: SkillDest = DEST_EMPTY,
        force: bool = False,
        link: bool = False,
        prune: bool = False,
    ) -> SkillProvisionResult:
        """Provision every pack skill for *tool_id* into *target_dir*.

        Return the provisioning result reporting how many skills landed.
        """
        ...

    @abstractmethod
    def prune(self, target_dir: Path, custom_dest: SkillDest = DEST_EMPTY) -> SkillProvisionResult:
        """Remove provisioned entries the pack no longer provides.

        Return the result reporting how many stale entries were removed.
        """
        ...

    @abstractmethod
    def audit(self) -> PackFindingList:
        """Pack loadability findings; an empty list means the pack is clean."""
        ...


class ISkillRegistryProtocol(ABC):
    """Registry capability contract: one method per listing / install op."""

    @abstractmethod
    def list(self, tool_filter: ToolFilter = FILTER_EMPTY) -> ExitCode:
        """List tools and their skills. Return the exit code."""
        ...

    @abstractmethod
    def check(self) -> ExitCode:
        """Audit per-tool skill coverage and pack loadability. Return the exit code."""
        ...

    @abstractmethod
    def show(self, query: SkillQuery = QUERY_EMPTY) -> ExitCode:
        """Display a skill's SKILL.md. Return the exit code."""
        ...

    @abstractmethod
    def install(self, args: SkillArgs) -> ExitCode:
        """Parse *args* and provision skills. Return the exit code."""
        ...

    @abstractmethod
    def uninstall(self, args: SkillArgs) -> ExitCode:
        """Parse *args* and remove provisioned skills. Return the exit code."""
        ...

    @abstractmethod
    def sync(self, args: SkillArgs) -> ExitCode:
        """Provision all skills for all tools. Return the exit code."""
        ...


__all__ = [
    "DEST_EMPTY",
    "FILTER_EMPTY",
    "QUERY_EMPTY",
    "ExitCode",
    "ISkillProvisionProtocol",
    "ISkillRegistryProtocol",
    "PackFinding",
    "PackFindingList",
    "SkillArgs",
    "SkillDest",
    "SkillProvisionResult",
    "SkillQuery",
    "ToolFilter",
]

# Layer-symbol registry (runtime reference for harness/loader introspection).
_layer_symbols = {
    "DEST_EMPTY": DEST_EMPTY,
    "FILTER_EMPTY": FILTER_EMPTY,
    "QUERY_EMPTY": QUERY_EMPTY,
    "ExitCode": ExitCode,
    "ISkillProvisionProtocol": ISkillProvisionProtocol,
    "ISkillRegistryProtocol": ISkillRegistryProtocol,
    "PackFinding": PackFinding,
    "PackFindingList": PackFindingList,
    "SkillArgs": SkillArgs,
    "SkillDest": SkillDest,
    "SkillProvisionResult": SkillProvisionResult,
    "SkillQuery": SkillQuery,
    "ToolFilter": ToolFilter,
}
