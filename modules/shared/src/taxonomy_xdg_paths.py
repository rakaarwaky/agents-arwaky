"""XDG path resolution — pure functions over environment variables (taxonomy layer).

Stateless, dependency-free: only the standard library. Utility-layer files
import from here instead of importing other utility modules (AES201 rule 4).
"""
from __future__ import annotations

import os
from pathlib import Path


def data_home() -> Path:
    """XDG_DATA_HOME (default ~/.local/share)."""
    p = os.environ.get("XDG_DATA_HOME")
    return Path(p).expanduser() if p else Path.home() / ".local" / "share"


def config_home() -> Path:
    """XDG_CONFIG_HOME (default ~/.config)."""
    p = os.environ.get("XDG_CONFIG_HOME")
    return Path(p).expanduser() if p else Path.home() / ".config"


def cache_home() -> Path:
    """XDG_CACHE_HOME (default ~/.cache)."""
    p = os.environ.get("XDG_CACHE_HOME")
    return Path(p).expanduser() if p else Path.home() / ".cache"


def state_home() -> Path:
    """XDG_STATE_HOME (default ~/.local/state)."""
    p = os.environ.get("XDG_STATE_HOME")
    return Path(p).expanduser() if p else Path.home() / ".local" / "state"


def bin_home() -> Path:
    """XDG_BIN_HOME launcher dir (default ~/.local/bin)."""
    p = os.environ.get("XDG_BIN_HOME")
    return Path(p).expanduser() if p else Path.home() / ".local" / "bin"


def tool_data_dir(tool: str) -> Path:
    """XDG data dir for one tool."""
    return data_home() / tool


def tool_config_dir(tool: str) -> Path:
    """XDG config dir for one tool."""
    return config_home() / tool


def tool_cache_dir(tool: str) -> Path:
    """XDG cache dir for one tool."""
    return cache_home() / tool


def tool_state_dir(tool: str) -> Path:
    """XDG data dir with state suffix for one tool."""
    return data_home() / f"{tool}.state"


def agents_arwaky_config_dir() -> Path:
    """Config dir of the agents-arwaky orchestrator itself."""
    return config_home() / "agents-arwaky"
