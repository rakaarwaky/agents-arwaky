"""XDG domain: base-directory path helpers and side-effect I/O."""
from __future__ import annotations

from modules.shared.src.xdg.utility_xdg_atomic_io import (
    atomic_write_text,
    bin_on_path,
    ensure_bin_home,
    ensure_path,
    remove_tool_artifacts,
    warn_if_bin_not_on_path,
)
from modules.shared.src.xdg.utility_xdg_paths import (
    agent_secret_candidates,
    agents_arwaky_config_dir,
    bin_home,
    cache_home,
    config_home,
    data_home,
    state_home,
    tool_cache_dir,
    tool_cache_path,
    tool_config_dir,
    tool_config_path,
    tool_data_dir,
    tool_data_path,
    tool_state_dir,
    tool_state_path,
)

__all__ = [
    "agent_secret_candidates",
    "agents_arwaky_config_dir",
    "atomic_write_text",
    "bin_home",
    "bin_on_path",
    "cache_home",
    "config_home",
    "data_home",
    "ensure_bin_home",
    "ensure_path",
    "remove_tool_artifacts",
    "state_home",
    "tool_cache_dir",
    "tool_cache_path",
    "tool_config_dir",
    "tool_config_path",
    "tool_data_dir",
    "tool_data_path",
    "tool_state_dir",
    "tool_state_path",
    "warn_if_bin_not_on_path",
]
