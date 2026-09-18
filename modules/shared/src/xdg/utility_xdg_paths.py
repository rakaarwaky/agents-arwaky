"""XDG Base Directory path helpers (pure), split out from tools/lib/xdg.py.\n\nFollows freedesktop.org XDG Base Directory Specification.\nAll helpers here are pure (no side effects) except the mkdir variants.\n"""
from __future__ import annotations

import os
from pathlib import Path

from modules.shared.src.paths.utility_paths import repo_root

# ---------------------------------------------------------------------------
# Base directories (pure)
# ---------------------------------------------------------------------------
def data_home() -> Path:
    return Path(os.environ.get("XDG_DATA_HOME", str(Path.home() / ".local/share")))


def config_home() -> Path:
    return Path(os.environ.get("XDG_CONFIG_HOME", str(Path.home() / ".config")))


def state_home() -> Path:
    """$XDG_STATE_HOME, default ~/.local/state (resmi sejak spec 0.8)."""
    return Path(os.environ.get("XDG_STATE_HOME", str(Path.home() / ".local/state")))


def cache_home() -> Path:
    return Path(os.environ.get("XDG_CACHE_HOME", str(Path.home() / ".cache")))


def runtime_dir() -> Path:
    path = os.environ.get("XDG_RUNTIME_DIR")
    if path:
        return Path(path)
    uid = os.getuid()
    return Path(f"/run/user/{uid}")


def bin_home() -> Path:
    return Path(os.environ.get("XDG_BIN_HOME", str(Path.home() / ".local/bin")))


def tool_data_dir(tool: str) -> Path:
    return data_home() / tool


def tool_config_dir(tool: str) -> Path:
    return config_home() / tool


def tool_cache_dir(tool: str) -> Path:
    return cache_home() / tool


def tool_state_dir(tool: str) -> Path:
    return state_home() / tool


def agents_arwaky_config_dir() -> Path:
    return config_home() / "agents-arwaky"


def ensure_xdg_dirs_exist(tool: str) -> None:
    for d in (tool_data_dir(tool), tool_config_dir(tool), tool_cache_dir(tool), tool_state_dir(tool)):
        d.mkdir(parents=True, exist_ok=True)
