"""Harness agent orchestrator — routes connect/disconnect to per-harness connectors."""
from __future__ import annotations

from modules.harness.src.capabilities_harness_antigravity import (
    ALIASES as ANTIGRAVITY_ALIASES,
)
from modules.harness.src.capabilities_harness_grok_build import (
    ALIASES as GROK_BUILD_ALIASES,
)
from modules.harness.src.capabilities_harness_hermes import (
    ALIASES as HERMES_ALIASES,
)
from modules.harness.src.capabilities_harness_opencode import (
    ALIASES as OPENCODE_ALIASES,
)
from modules.harness.src.capabilities_harness_qwencode import (
    ALIASES as QWENCODE_ALIASES,
)
from modules.shared.src.harness.contract_harness_aggregate import IHarnessAggregate
from modules.shared.src.harness.contract_harness_protocol import IHarnessConnector

_ALIAS_MAP: dict[str, tuple[str, ...]] = {
    "antigravity": ANTIGRAVITY_ALIASES,
    "hermes": HERMES_ALIASES,
    "opencode": OPENCODE_ALIASES,
    "qwencode": QWENCODE_ALIASES,
    "grok-build": GROK_BUILD_ALIASES,
}


class HarnessOrchestrator(IHarnessAggregate):
    """Registry of connectors, routed by target harness id/alias.

    # Block 1: Constructor (connector registry)
    # Block 2: Target resolution
    # Block 3: Aggregate verb delegation
    """

    # -- Block 1: Constructor ---------------------------------------------------
    def __init__(self, connectors: dict[str, IHarnessConnector]) -> None:
        self._connectors = connectors
        self._aliases: dict[str, str] = {}
        for harness_id, aliases in _ALIAS_MAP.items():
            for alias in aliases:
                self._aliases[alias.lstrip("-")] = harness_id

    # -- Block 2: Target resolution -------------------------------------------------
    def resolve_targets(self, targets: tuple[str, ...]) -> tuple[str, ...]:
        """Map raw CLI targets (id/alias) onto canonical ids, deduped, drop unknown."""
        out: list[str] = []
        seen: set[str] = set()
        for target in targets:
            tid = self._aliases.get(target.lstrip("-"), target)
            if tid not in self._connectors or tid in seen:
                continue
            seen.add(tid)
            out.append(tid)
        return tuple(out)

    def all_targets(self) -> tuple[str, ...]:
        return tuple(self._connectors)

    # -- Block 3: Aggregate verb delegation ------------------------------------------
    def connect(self, targets, force: bool = False, dry_run: bool = False, mcp_only: bool = False,
                skills_only: bool = False, env_only: bool = False, copy_skills: bool = False) -> int:
        resolved = self.resolve_targets(targets)
        if not resolved:
            print("No target agent harness specified.")
            return 1
        print("Connecting agents-arwaky to agent harnesses...")
        print("-" * 66)
        for tid in resolved:
            self._connectors[tid].connect(force, dry_run, mcp_only, skills_only, env_only, copy_skills)
            print()
        print("-" * 66)
        print("\u2713 Connection complete. Agent harnesses are now synchronized with agents-arwaky.")
        return 0

    def disconnect(self, targets: tuple[str, ...], dry_run: bool = False) -> int:
        resolved = self.resolve_targets(targets)
        if not resolved:
            print("No target agent harness specified.")
            return 1
        print("Disconnecting agents-arwaky from agent harnesses...")
        print("-" * 66)
        for tid in resolved:
            self._connectors[tid].disconnect(False, dry_run)
            print()
        print("-" * 66)
        print("\u2713 Disconnect complete. agents-arwaky entries removed from selected harnesses.")
        return 0
