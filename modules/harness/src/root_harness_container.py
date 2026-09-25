"""Harness composition root — wires the leaf-adapter registry into the three capabilities.

Adding a harness = one new ``capabilities_harness_<provider>_adapter.py``
leaf + its ``ADAPTER_UNITS`` entry in ``HARNESS_REGISTRY`` below. No
capability or agent change.
"""
from __future__ import annotations

from modules.harness.src.agent_harness_orchestrator import HarnessOrchestrator
from modules.harness.src.capabilities_harness_connector import HarnessConnector
from modules.harness.src.capabilities_harness_disconnector import HarnessDisconnector
from modules.harness.src.capabilities_harness_skills import HarnessSkills

# Root is the only layer allowed to import capabilities_* (AES201): every
# provider leaf is registered here and injected into the capabilities.
# Importing them here also wires them for the AES503 orphan check.
from modules.harness.src.capabilities_harness_antigravity_adapter import (
    ADAPTER_UNITS as _ANTIGRAVITY_UNITS,
)
from modules.harness.src.capabilities_harness_grok_build_adapter import (
    ADAPTER_UNITS as _GROK_BUILD_UNITS,
)
from modules.harness.src.capabilities_harness_hermes_adapter import (
    ADAPTER_UNITS as _HERMES_UNITS,
)
from modules.harness.src.capabilities_harness_opencode_adapter import (
    ADAPTER_UNITS as _OPENCODE_UNITS,
)
from modules.harness.src.capabilities_harness_qwencode_adapter import (
    ADAPTER_UNITS as _QWENCODE_UNITS,
)
from modules.shared.src.contract_harness_aggregate import IHarnessAggregate
from modules.shared.src.taxonomy_harness_constant import ALL_HARNESS_IDS

#: harness_id → provider spec (root composition data; each spec owns one
#: provider's paths, config format, env keys, and custom-API flag).
HARNESS_REGISTRY: dict[str, object] = {
    **_ANTIGRAVITY_UNITS,
    **_GROK_BUILD_UNITS,
    **_HERMES_UNITS,
    **_OPENCODE_UNITS,
    **_QWENCODE_UNITS,
}


def _daemon_status_fn():
    """Liveness probe for the router daemon (endpoint from the daemon feature).

    Imported lazily so the harness feature has no hard dependency on the
    daemon module; a down daemon is reported, and the rest of connect still
    lands (FR-001 failure mode). 9Router runs host-native (no Podman).
    """
    try:
        from modules.daemon.src.capabilities_9router_daemon import (
            api_ready,
            process_running,
        )
    except ImportError:
        return None

    def _probe():
        return process_running() or api_ready(timeout=2)

    return _probe


def _adapters() -> dict[str, object]:
    """Registry keyed on harness id: one provider leaf per harness."""
    registry = dict(HARNESS_REGISTRY)
    # Sanity: every id in the taxonomy table has an adapter.
    missing = [i for i in ALL_HARNESS_IDS if i not in registry]
    if missing:
        raise RuntimeError(f"Adapter registry missing harness ids: {missing}")
    return registry


class HarnessContainer:
    """Construct the three capabilities and the routing orchestrator."""

    # -- Block 1: Constructor ---------------------------------------------------
    def __init__(self) -> None:
        adapters = _adapters()
        # Router endpoint resolution comes from the daemon feature; the
        # connector treats an absent daemon as "reported, wiring still applied".
        skills = HarnessSkills(adapters)
        connector = HarnessConnector(
            adapters,
            daemon_status_fn=_daemon_status_fn(),
            skills=skills,
        )
        disconnector = HarnessDisconnector(adapters)
        self._orchestrator = HarnessOrchestrator(connector, disconnector, skills)

    @property
    def aggregate(self) -> IHarnessAggregate:
        return self._orchestrator


def create_harness_feature() -> IHarnessAggregate:
    """Fully-wired harness feature aggregate."""
    return HarnessContainer().aggregate
