"""Config feature — public symbols.

Re-exports the orchestrator, capabilities, and surface entry point so feature
consumers can import from ``modules.config`` directly. The composition root
(``root_config_container``) is imported by callers directly, not re-exported
here, to keep the agent/capability package free of a root re-export cycle
(AES205).
"""
from __future__ import annotations

from modules.config.src.agent_config_orchestrator import ConfigOrchestrator
from modules.config.src.capabilities_config_engine import ConfigModifier, ConfigWriter
from modules.config.src.surface_config_command import ConfigCommand, cmd_config

__all__ = [
    "ConfigCommand",
    "ConfigModifier",
    "ConfigOrchestrator",
    "ConfigWriter",
    "cmd_config",
]
