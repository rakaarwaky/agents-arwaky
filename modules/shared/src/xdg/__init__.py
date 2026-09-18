"""XDG domain — pure path helpers + side-effect I/O (P4-A1).\n\nConsumers import from ``modules.shared.src.xdg``.\n"""
from __future__ import annotations

from modules.shared.src.xdg.utility_xdg_atomic_io import (
    atomic_write_text,
    bin_home,
    bin_on_path,
    ensure_bin_home,
    ensure_path,
    remove_tool_artifacts,
    warn_if_bin_not_on_path,
)
from modules.shared.src.xdg.utility_xdg_paths import (
    agents_arwaky_config_dir,
    cache_home,
    config_home,
    data_home,
    ensure_xdg_dirs_exist,
    runtime_dir,
    state_home,
    tool_cache_dir,
    tool_config_dir,
    tool_data_dir,
    tool_state_dir,
)

__all__ = [
    "agents_arwaky_config_dir",
    "atomic_write_text",
    "bin_home",
    "bin_on_path",
    "cache_home",
    "config_home",
    "data_home",
    "ensure_bin_home",
    "ensure_path",
    "ensure_xdg_dirs_exist",
    "remove_tool_artifacts",
    "runtime_dir",
    "state_home",
    "tool_cache_dir",
    "tool_config_dir",
    "tool_data_dir",
    "tool_state_dir",
    "warn_if_bin_not_on_path",
]
