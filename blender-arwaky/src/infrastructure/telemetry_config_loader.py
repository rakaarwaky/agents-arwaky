"""Telemetry configuration — reads from config.yaml, supports env override."""

import logging
import os

from contract import ConfigPort, ConfigValue
from taxonomy import EnabledFlag

from .config_file_loader import ApplicationConfigLoader

logger = logging.getLogger("BlenderMCPServer")


class TelemetryConfig(ConfigPort):
    """Configuration for telemetry — local JSONL storage, no Supabase.

    Resolution order (first wins):
    1. DISABLE_TELEMETRY / BLENDER_MCP_DISABLE_TELEMETRY env var
    2. config.yaml → telemetry.enabled
    3. Default: disabled (opt-in)
    """

    def __init__(self) -> None:
        # Check env override first
        disable_env: bool = (
            os.getenv("DISABLE_TELEMETRY", "").lower() == "true"
            or os.getenv("BLENDER_MCP_DISABLE_TELEMETRY", "").lower() == "true"
        )
        if disable_env:
            self.enabled: bool = False
        else:
            # Read from config.yaml via ApplicationConfigLoader
            cfg_enabled = ApplicationConfigLoader.get_config("telemetry.enabled")
            self.enabled = bool(cfg_enabled) if cfg_enabled is not None else False

        # Performance/Privacy settings
        self.max_prompt_length: int = 500

        logger.debug("Telemetry enabled=%s", self.enabled)

    def get(self, path: str = "", default: ConfigValue = None) -> ConfigValue:
        """ConfigPort: retrieve a config value by dot-notation path."""
        if path == "enabled":
            return self.enabled
        if path == "max_prompt_length":
            return self.max_prompt_length
        return default

    def is_enabled(self) -> bool:
        return bool(EnabledFlag(self.enabled))
