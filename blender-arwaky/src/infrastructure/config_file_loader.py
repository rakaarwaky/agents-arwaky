import threading
from pathlib import Path
from typing import cast

import yaml

from contract import ConfigPort, ConfigValue
from taxonomy import FilePath


class ApplicationConfigLoader(ConfigPort):
    """Loads and provides access to application configuration from config.yaml."""

    _config: dict[str, ConfigValue] | None = None
    _lock: threading.Lock = threading.Lock()

    @classmethod
    def get_project_root(cls) -> Path:
        """Returns the root directory of the project.

        Resolution order:
        1. BLENDERMCP_CONFIG_PATH (explicit config file path)
        2. BLENDER_MCP_ROOT env var (project root override)
        3. Relative to this file (works in dev: src/infrastructure/)
        4. XDG_CONFIG_HOME or ~/.config/blender-mcp (production install)
        5. Current working directory (last resort)
        """
        from os import environ

        # 1. Explicit config file path (highest priority)
        env_cfg = environ.get("BLENDERMCP_CONFIG_PATH")
        if env_cfg:
            cfg_path = Path(env_cfg).resolve()
            if cfg_path.is_file():
                return cfg_path.parent
            if cfg_path.is_dir() and (cfg_path / "config.yaml").exists():
                return cfg_path

        # 2. Env var project root override
        env_root = environ.get("BLENDER_MCP_ROOT")
        if env_root:
            return Path(env_root).resolve()

        # 3. Relative to this file (dev layout)
        file_path = Path(__file__).resolve()
        for parent in [file_path, *file_path.parents]:
            if (parent / "config.yaml").exists():
                return parent

        # 4. XDG config path (production install)
        xdg_config = environ.get("XDG_CONFIG_HOME", Path.home() / ".config")
        prod_path = Path(xdg_config) / "blender-mcp"
        if prod_path.exists():
            return prod_path

        # 5. Fallback to cwd
        return Path.cwd().resolve()

    @classmethod
    def load_config(cls) -> dict[str, ConfigValue]:
        """Loads the config.yaml file from the project root."""
        config_path: FilePath = cast(FilePath, str(cls.get_project_root() / "config.yaml"))
        if not Path(config_path).exists():
            return {}
        try:
            with open(config_path) as f:
                return cast(dict[str, ConfigValue], yaml.safe_load(f) or {})
        except Exception:
            return {}

    @classmethod
    def get_config(cls, path: str = "", default: ConfigValue = None) -> ConfigValue:
        """Retrieves a configuration value using dot notation (e.g., 'server.port')."""
        with cls._lock:
            if cls._config is None:
                cls._config = cls.load_config()

            if not path:
                return cast(ConfigValue, cls._config)

            keys = path.split(".")
            value: ConfigValue = cast(ConfigValue, cls._config)
            for key in keys:
                if isinstance(value, dict) and key in value:
                    value = cast(ConfigValue, value[key])
                else:
                    return default
            return value

    # ConfigPort implementation
    def get(self, path: str = "", default: ConfigValue = None) -> ConfigValue:
        """ConfigPort: retrieve a config value by dot-notation path."""
        return self.get_config(path, default)


# Global instance or helpers
get_project_root = ApplicationConfigLoader.get_project_root
load_config = ApplicationConfigLoader.load_config
get_config = ApplicationConfigLoader.get_config
