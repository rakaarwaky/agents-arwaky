"""Skill-domain protocol contracts (one feature per capability ABC).

Provisioners and registries implement every feature ABC in their role;
injectors may type a full surface as the composites ``ISkillProvisioner`` /
``ISkillRegistry``.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path

from modules.shared.src.taxonomy_skill_vo import (
    ExitCode,
    SkillArgs,
    SkillDest,
    SkillProvisionResult,
    ToolFilter,
)


class ISkillInstallProtocol(ABC):
    """FR: provision skills into a project workspace."""

    @abstractmethod
    def install(
        self,
        tool_id: ToolFilter,
        target_dir: Path,
        custom_dest: SkillDest = SkillDest(""),
        force: bool = False,
        link: bool = False,
        prune: bool = False,
    ) -> SkillProvisionResult:
        """Provision skills into a project workspace."""
        ...


class ISkillPruneProtocol(ABC):
    """FR: remove provisioned skill copies the pack no longer provides."""

    @abstractmethod
    def prune(
        self,
        target_dir: Path,
        custom_dest: SkillDest = SkillDest(""),
    ) -> SkillProvisionResult:
        """Remove provisioned skill copies the pack no longer provides."""
        ...


class ISkillAuditProtocol(ABC):
    """FR: audit pack loadability findings."""

    @abstractmethod
    def audit(self) -> list[str]:
        """Return pack loadability finding strings; empty means clean."""
        ...


class ISkillListProtocol(ABC):
    """FR: list installed skills."""

    @abstractmethod
    def cmd_list(self, argv: SkillArgs) -> ExitCode:
        """List installed skills."""
        ...


class ISkillCheckProtocol(ABC):
    """FR: audit pack loadability via the registry command."""

    @abstractmethod
    def cmd_check(self) -> ExitCode:
        """Audit pack loadability."""
        ...


class ISkillShowProtocol(ABC):
    """FR: show a single skill's content."""

    @abstractmethod
    def cmd_show(self, argv: SkillArgs) -> ExitCode:
        """Show a single skill's content."""
        ...


class ISkillInstallCmdProtocol(ABC):
    """FR: install a skill into a project via the registry command."""

    @abstractmethod
    def cmd_install(self, argv: SkillArgs) -> ExitCode:
        """Install a skill into a project."""
        ...


class ISkillUninstallCmdProtocol(ABC):
    """FR: remove a provisioned skill via the registry command."""

    @abstractmethod
    def cmd_uninstall(self, argv: SkillArgs) -> ExitCode:
        """Remove a provisioned skill."""
        ...


class ISkillProvisioner(
    ISkillInstallProtocol,
    ISkillPruneProtocol,
    ISkillAuditProtocol,
):
    """Composite DI type: full provisioner surface (no methods of its own)."""


class ISkillRegistry(
    ISkillListProtocol,
    ISkillCheckProtocol,
    ISkillShowProtocol,
    ISkillInstallCmdProtocol,
    ISkillUninstallCmdProtocol,
):
    """Composite DI type: full registry surface (no methods of its own)."""


__all__ = [
    "ExitCode",
    "ISkillAuditProtocol",
    "ISkillCheckProtocol",
    "ISkillInstallCmdProtocol",
    "ISkillInstallProtocol",
    "ISkillListProtocol",
    "ISkillPruneProtocol",
    "ISkillProvisioner",
    "ISkillRegistry",
    "ISkillShowProtocol",
    "ISkillUninstallCmdProtocol",
    "SkillArgs",
    "SkillDest",
    "SkillProvisionResult",
    "ToolFilter",
]

# Layer-symbol registry (runtime reference for harness/loader introspection).
_layer_symbols = {
    "ExitCode": ExitCode,
    "ISkillAuditProtocol": ISkillAuditProtocol,
    "ISkillCheckProtocol": ISkillCheckProtocol,
    "ISkillInstallCmdProtocol": ISkillInstallCmdProtocol,
    "ISkillInstallProtocol": ISkillInstallProtocol,
    "ISkillListProtocol": ISkillListProtocol,
    "ISkillPruneProtocol": ISkillPruneProtocol,
    "ISkillProvisioner": ISkillProvisioner,
    "ISkillRegistry": ISkillRegistry,
    "ISkillShowProtocol": ISkillShowProtocol,
    "ISkillUninstallCmdProtocol": ISkillUninstallCmdProtocol,
    "SkillArgs": SkillArgs,
    "SkillDest": SkillDest,
    "SkillProvisionResult": SkillProvisionResult,
    "ToolFilter": ToolFilter,
}
