"""Harness agent orchestrator — the single agent for the harness feature.

Resolves raw CLI tokens (ids, aliases, ``--all``) to canonical harness ids
using the alias table in :mod:`taxonomy_harness_constant`, dedupes, and
surfaces unknown tokens to the CLI instead of raising. Each action is routed
through its capability's single ``execute`` method; the adapter registry is
injected by the root layer.
"""
from __future__ import annotations

from modules.shared.src.contract_harness_aggregate import IHarnessAggregate
from modules.shared.src.contract_harness_protocol import IHarnessProtocol
from modules.shared.src.taxonomy_harness_constant import ALIASES, ALL_HARNESS_IDS
from modules.shared.src.taxonomy_harness_vo import ExitCode


# ─── Block 1: Class Definition & Constructor ──────────────
class HarnessOrchestrator(IHarnessAggregate):
    """Resolve raw CLI tokens and route each action to its capability."""

    def __init__(
        self,
        connector: IHarnessProtocol,
        disconnector: IHarnessProtocol,
        skills: IHarnessProtocol,
    ) -> None:
        """Compose the three capabilities behind the orchestrator interface."""
        self._connector = connector
        self._disconnector = disconnector
        self._skills = skills

    # ─── Block 2: Aggregate Method Implementation ──────────
    def resolve_targets(self, targets: tuple[str, ...]) -> tuple[str, ...]:
        """Map raw CLI tokens (id / alias / --all) onto canonical ids, deduped.

        Unknown tokens are DROPPED here; the CLI surface surfaces them
        before calling this method. ``--all`` expands to every supported id.
        """
        out: list[str] = []
        seen: set[str] = set()
        for target in targets:
            tid = ALIASES.get(target.lstrip("-"), target)
            if tid not in ALL_HARNESS_IDS or tid in seen:
                continue
            seen.add(tid)
            out.append(tid)
        return tuple(out)

    def all_targets(self) -> tuple[str, ...]:
        """Every supported harness id (canonical)."""
        return tuple(ALL_HARNESS_IDS)

    def connect(
        self,
        targets: tuple[str, ...],
        force: bool = False,
        dry_run: bool = False,
        mcp_only: bool = False,
        skills_only: bool = False,
        env_only: bool = False,
        router: bool = False,
        copy_skills: bool = False,
    ) -> ExitCode:
        """Route the connect action through the connector's execute."""
        resolved = self.resolve_targets(targets)
        return self._connector.execute("connect", resolved, {
            "force": force,
            "dry_run": dry_run,
            "mcp_only": mcp_only,
            "skills_only": skills_only,
            "env_only": env_only,
            "router": router,
            "copy_skills": copy_skills,
        })

    def disconnect(self, targets: tuple[str, ...], dry_run: bool = False) -> ExitCode:
        """Route the disconnect action through the disconnector's execute."""
        resolved = self.resolve_targets(targets)
        return self._disconnector.execute("disconnect", resolved, {"dry_run": dry_run})

    def provision_skills(
        self,
        targets: tuple[str, ...],
        copy: bool = False,
        dry_run: bool = False,
    ) -> ExitCode:
        """Route the provision_skills action through the skills capability's execute."""
        resolved = self.resolve_targets(targets)
        return self._skills.execute(
            "provision_skills",
            resolved,
            {"copy": copy, "dry_run": dry_run},
        )

    # ─── Block 3: Dunder Methods, Factories & Helpers ─────
    def __repr__(self) -> str:
        return "HarnessOrchestrator()"


__all__ = ["ExitCode", "HarnessOrchestrator", "IHarnessAggregate", "IHarnessProtocol"]

# Layer-symbol registry (runtime reference for harness/loader introspection).
_layer_symbols = {
    "ExitCode": ExitCode,
    "HarnessOrchestrator": HarnessOrchestrator,
    "IHarnessAggregate": IHarnessAggregate,
    "IHarnessProtocol": IHarnessProtocol,
}
