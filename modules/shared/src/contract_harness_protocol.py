"""Harness-domain capability contracts — one ABC per seam (AES102 `_protocol`).

Each seam is one capability's own operations, declared side by side in this
one file. A capability implements exactly one class here, and all of it — the
method set of a seam is small enough that no implementor ever carries a stub.

- `IHarnessConnectProtocol` — the connect business action.
- `IHarnessDisconnectProtocol` — the disconnect business action.
- `IHarnessSkillsProtocol` — the skill-provisioning business action.
- `IHarnessProviderProtocol` — the provider-data lookup the per-harness leaves
  expose. The leaves know nothing about business actions, so they implement
  only this one class.
"""
from __future__ import annotations

from abc import ABC, abstractmethod

from modules.shared.src.taxonomy_harness_vo import (
    ExitCode,
    HarnessTargets,
)


class IHarnessConnectProtocol(ABC):
    """Connect seam: wire MCP servers, env keys, and the router provider."""

    @abstractmethod
    def connect(self, targets: HarnessTargets, force: bool, dry_run: bool,
                mcp_only: bool, skills_only: bool, env_only: bool,
                router: bool, copy_skills: bool) -> ExitCode:
        """FR-001: connect to the resolved harness targets; return exit code.

        Skill provisioning is a clause of connect (the ``skills_only`` /
        ``copy_skills`` flags select its scope), so it is declared on its own
        seam (``IHarnessSkillsProtocol``) instead of forcing the connect
        capability to carry an owned-but-delegated method.
        """
        ...


class IHarnessDisconnectProtocol(ABC):
    """Disconnect seam: remove exactly what connect wrote."""

    @abstractmethod
    def disconnect(self, targets: HarnessTargets, dry_run: bool) -> ExitCode:
        """FR-002: disconnect from the resolved harness targets; return exit code."""
        ...


class IHarnessSkillsProtocol(ABC):
    """Skill-provisioning seam: make the pack discoverable to each target."""

    @abstractmethod
    def provision_skills(self, targets: HarnessTargets, copy: bool, dry_run: bool,
                         force: bool = False) -> ExitCode:
        """FR-003: provision the skill pack into the resolved targets; return exit code."""
        ...


class IHarnessProviderProtocol(ABC):
    """Provider-data seam: resolve one provider-scoped op against a unit map."""

    @abstractmethod
    def execute(
        self,
        op: str,
        targets: tuple[str, ...],
        flags: dict[str, bool] | None = None,
    ) -> ExitCode:
        """Run a provider-scoped *op* against this leaf's units; return exit code."""
        ...


__all__ = [
    "ExitCode",
    "IHarnessConnectProtocol",
    "IHarnessDisconnectProtocol",
    "IHarnessProviderProtocol",
    "IHarnessSkillsProtocol",
    "HarnessTargets",
]

# Layer-symbol registry (runtime reference for harness/loader introspection).
_layer_symbols = {
    "ExitCode": ExitCode,
    "IHarnessConnectProtocol": IHarnessConnectProtocol,
    "IHarnessDisconnectProtocol": IHarnessDisconnectProtocol,
    "IHarnessProviderProtocol": IHarnessProviderProtocol,
    "IHarnessSkillsProtocol": IHarnessSkillsProtocol,
    "HarnessTargets": HarnessTargets,
}
