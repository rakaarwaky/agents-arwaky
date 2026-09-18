"""Harness composition root — creates all 5 connectors and the orchestrator."""
from __future__ import annotations

from modules.harness.src.agent_harness_orchestrator import HarnessOrchestrator
from modules.harness.src.capabilities_harness_antigravity import AntigravityConnector
from modules.harness.src.capabilities_harness_grok_build import GrokBuildConnector
from modules.harness.src.capabilities_harness_hermes import HermesConnector
from modules.harness.src.capabilities_harness_opencode import OpencodeConnector
from modules.harness.src.capabilities_harness_qwencode import QwencodeConnector
from modules.harness.src.contract_harness_aggregate import IHarnessAggregate
from modules.harness.src.contract_harness_protocol import IHarnessConnector
from modules.harness.src.taxonomy_harness_constant import HARNESSES


class HarnessContainer:
    """Construct the 5 harness connectors and the routing orchestrator."""

    def __init__(self) -> None:
        # P4-A21: adapters register themselves; attach callables to the
        # shared HARNESSES tables consumed by the agent-layer verb dispatch.
        from modules.harness.src.capabilities_harness_antigravity import register as _r_antigravity
        from modules.harness.src.capabilities_harness_grok_build import register as _r_grok_build
        from modules.harness.src.capabilities_harness_hermes import register as _r_hermes
        from modules.harness.src.capabilities_harness_opencode import register as _r_opencode
        from modules.harness.src.capabilities_harness_qwencode import register as _r_qwencode
        for _reg, _entry in ((_r_antigravity, HARNESSES["antigravity"]),
                             (_r_hermes, HARNESSES["hermes"]),
                             (_r_opencode, HARNESSES["opencode"]),
                             (_r_qwencode, HARNESSES["qwencode"]),
                             (_r_grok_build, HARNESSES["grok-build"])):
            _entry["connect"] = _reg()["connect"]
            _entry["disconnect"] = _reg()["disconnect"]

        from modules.config.src.capabilities_config_engine import ConfigWriter
        _config_writer = lambda: ConfigWriter()

        connectors: dict[str, IHarnessConnector] = {
            "antigravity": AntigravityConnector(),
            "hermes": HermesConnector(),
            "opencode": OpencodeConnector(),
            "qwencode": QwencodeConnector(),
            "grok-build": GrokBuildConnector(config_writer_factory=_config_writer),
        }
        self._orchestrator = HarnessOrchestrator(connectors)

    @property
    def aggregate(self) -> IHarnessAggregate:
        return self._orchestrator


def create_harness_feature() -> IHarnessAggregate:
    """Fully-wired harness feature aggregate."""
    return HarnessContainer().aggregate
