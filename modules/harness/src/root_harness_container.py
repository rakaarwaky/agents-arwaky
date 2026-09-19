"""Harness composition root — wires the adapter registry into the three capabilities.

Adding a harness = one new ``utility_<provider>_adapter.py`` leaf + one
entry in the ``ADAPTERS`` registry below. No capability or agent change.
"""
from __future__ import annotations

from modules.harness.src.agent_harness_orchestrator import HarnessOrchestrator
from modules.harness.src.capabilities_harness_connector import HarnessConnector
from modules.harness.src.capabilities_harness_disconnector import HarnessDisconnector
from modules.harness.src.capabilities_harness_skills import HarnessSkills
from modules.harness.src.contract_harness_aggregate import IHarnessAggregate
from modules.harness.src.taxonomy_harness_constant import ALL_HARNESS_IDS
from modules.harness.src.utility_antigravity_adapter import AntigravityAdapter
from modules.harness.src.utility_grok_build_adapter import GrokBuildAdapter
from modules.harness.src.utility_hermes_adapter import HermesAdapter
from modules.harness.src.utility_opencode_adapter import OpencodeAdapter
from modules.harness.src.utility_qwencode_adapter import QwencodeAdapter


def _daemon_status_fn():
    """Liveness probe for the 9Router daemon (endpoint from the daemon feature).

    Imported lazily so the harness feature has no hard dependency on the
    daemon module; a down daemon is reported, and the rest of connect still
    lands (FR-001 failure mode).
    """
    try:
        from modules.daemon.src.capabilities_ninerouter_daemon import (
            api_ready,
            container_running,
        )
    except ImportError:
        return None

    def _probe():
        return container_running() or api_ready(timeout=2)

    return _probe


def _adapters() -> dict[str, object]:
    """Registry keyed on harness id: one leaf adapter per provider."""
    a = AntigravityAdapter()
    g = GrokBuildAdapter()
    h = HermesAdapter()
    o = OpencodeAdapter()
    q = QwencodeAdapter()
    registry: dict[str, object] = {
        a.id: a,
        g.id: g,
        h.id: h,
        o.id: o,
        q.id: q,
    }
    # Sanity: every id in the taxonomy table has an adapter.
    missing = [i for i in ALL_HARNESS_IDS if i not in registry]
    if missing:
        raise RuntimeError(f"Adapter registry missing harness ids: {missing}")
    return registry


class HarnessContainer:
    """Construct the three capabilities and the routing orchestrator."""

    def __init__(self) -> None:
        adapters = _adapters()
        # Router endpoint resolution comes from the daemon feature; the
        # connector treats an absent daemon as "reported, wiring still applied".
        connector = HarnessConnector(adapters, daemon_status_fn=_daemon_status_fn())
        disconnector = HarnessDisconnector(adapters)
        skills = HarnessSkills(adapters)
        self._orchestrator = HarnessOrchestrator(connector, disconnector, skills)

    @property
    def aggregate(self) -> IHarnessAggregate:
        return self._orchestrator


def create_harness_feature() -> IHarnessAggregate:
    """Fully-wired harness feature aggregate."""
    return HarnessContainer().aggregate
