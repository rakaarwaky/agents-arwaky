"""Config engine: jsonc/toml utilities, contracts, I/O + adapters (moved from tools/lib/engine.py)."""
from __future__ import annotations

from modules.shared.src.config.capabilities_config_engine import (
    ConfigModifier,
    ConfigWriter,
    arwaky_server_names,
    default_server_names,
    detect_format,
    get_mcp_map,
    list_mcp_servers,
    load_file,
    main,
    merge_mcp_servers,
    remove_env_keys,
    remove_mcp_servers,
    save_file,
    set_env_keys,
)
from modules.shared.src.config.contract_config_protocol import IConfigModifier, IConfigWriter
from modules.shared.src.config.utility_jsonc import strip_jsonc_comments
from modules.shared.src.config.utility_toml_write import (
    quote_key,
    toml_section,
    write_toml,
    write_toml_table,
    write_toml_value,
)

__all__ = [
    "ConfigModifier",
    "ConfigWriter",
    "IConfigModifier",
    "IConfigWriter",
    "arwaky_server_names",
    "default_server_names",
    "detect_format",
    "get_mcp_map",
    "list_mcp_servers",
    "load_file",
    "main",
    "merge_mcp_servers",
    "remove_env_keys",
    "remove_mcp_servers",
    "save_file",
    "set_env_keys",
    "strip_jsonc_comments",
    "quote_key",
    "toml_section",
    "write_toml",
    "write_toml_table",
    "write_toml_value",
]
