"""Config composition root — wires writer + modifier behind the aggregate."""
from __future__ import annotations

from modules.config.src.agent_config_orchestrator import ConfigOrchestrator
from modules.config.src.capabilities_config_engine import ConfigModifier, ConfigWriter
from modules.shared.src.contract_config_aggregate import IConfigAggregate
from modules.shared.src.contract_config_protocol import IConfigProtocol


def config_writer() -> IConfigProtocol:
    """Concrete writer capability (ConfigWriter) behind the protocol type."""
    return ConfigWriter()


def config_modifier() -> IConfigProtocol:
    """Concrete modifier capability (ConfigModifier) behind the protocol type."""
    return ConfigModifier()


class ConfigContainer:
    """Construct the two config capabilities and the orchestrator."""

    def __init__(self) -> None:
        writer = ConfigWriter()
        modifier = ConfigModifier()
        self._orchestrator = ConfigOrchestrator(writer, modifier)

    @property
    def aggregate(self) -> IConfigAggregate:
        """Expose the config orchestrator as the feature's public aggregate."""
        return self._orchestrator


def create_config_feature() -> IConfigAggregate:
    """Fully-wired config feature aggregate."""
    return ConfigContainer().aggregate
