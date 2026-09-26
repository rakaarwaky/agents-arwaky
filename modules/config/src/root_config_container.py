"""Config composition root — wires writer + modifier behind the aggregate."""
from __future__ import annotations

from modules.config.src.agent_config_orchestrator import ConfigOrchestrator
from modules.config.src.capabilities_config_modifier import ConfigModifier
from modules.config.src.capabilities_config_writer import ConfigWriter
from modules.shared.src.contract_config_aggregate import IConfigAggregate
from modules.shared.src.contract_config_protocol import (
    IConfigModifierProtocol,
    IConfigReaderProtocol,
)
from modules.shared.src.taxonomy_common_vo import HelpText

#: Usage text used by both writer and modifier when responding to ``help``.
_USAGE = HelpText(
    "Usage: aa config <op> ...\n"
    "  load PATH                    Read config; print data + detected format\n"
    "  save PATH DATA [--fmt FMT]   Write DATA (JSON) back in detected/explicit format\n"
    "  merge_servers PATH SERVERS   Merge SERVERS (JSON map) into the MCP config\n"
    "  set_env PATH PAIRS           Upsert PAIRS (JSON map) into the env file\n"
    "  remove_entries PATH KEYS...  Drop named server/env entries (--dry-run supported)\n"
    "  inspect PATH                 Print a read-only snapshot (format, data, servers)\n"
    "  help                         Print this usage\n"
)


def config_writer() -> IConfigReaderProtocol:
    """Concrete writer capability (ConfigWriter) behind the protocol type."""
    return ConfigWriter(_USAGE)


def config_modifier() -> IConfigModifierProtocol:
    """Concrete modifier capability (ConfigModifier) behind the protocol type."""
    return ConfigModifier(_USAGE)


class ConfigContainer:
    """Construct the two config capabilities and the orchestrator."""

    def __init__(self) -> None:
        writer = config_writer()
        modifier = config_modifier()
        self._orchestrator = ConfigOrchestrator(writer, modifier)

    @property
    def aggregate(self) -> IConfigAggregate:
        """Expose the config orchestrator as the feature's public aggregate."""
        return self._orchestrator


def create_config_feature() -> IConfigAggregate:
    """Fully-wired config feature aggregate."""
    return ConfigContainer().aggregate
