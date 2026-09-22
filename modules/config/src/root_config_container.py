"""Config composition root — wires the config engine behind its contract."""
from __future__ import annotations

from modules.config.src.capabilities_config_engine import ConfigWriter
from modules.shared.src.contract_config_protocol import IConfigWriter


def config_writer() -> IConfigWriter:
    """Concrete IConfigWriter (ConfigWriter) behind the contract type."""
    return ConfigWriter()
