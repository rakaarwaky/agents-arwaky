"""XDG Base Directory path helpers (pure), split out from tools/lib/xdg.py.

Follows freedesktop.org XDG Base Directory Specification:
    $XDG_DATA_HOME    -> ~/.local/share   (persistent data, per-tool)
    $XDG_CONFIG_HOME  -> ~/.config        (configuration, per-tool)
    $XDG_STATE_HOME   -> ~/.local/state   (state: PID files, history, logs)
    $XDG_CACHE_HOME   -> ~/.cache         (transient: build artifacts, caches)
    $XDG_RUNTIME_DIR  -> /run/user/<uid>  (sockets/private runtime, if available)
    $XDG_BIN_HOME     -> ~/.local/bin     (de-facto convention user binaries)

All helpers here are pure (no side effects) except the mkdir variants
``*_dir()`` and ``agents_arwaky_config_dir()``.
"""
from __future__ import annotations

import os
from pathlib import Path

from modules.shared.src.common.paths.utility_paths import repo_root

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


def bin_home() -> Path:
    """User binary dir: $XDG_BIN_HOME, default ~/.local/bin (de-facto standard)."""
    return Path(os.environ.get("XDG_BIN_HOME", str(Path.home() / ".local/bin")))


# ---------------------------------------------------------------------------
# Per-tool path helpers (pure) + mkdir variants
# ---------------------------------------------------------------------------
def tool_data_path(tool: str) -> Path:
    return data_home() / tool


def tool_config_path(tool: str) -> Path:
    return config_home() / tool


def tool_state_path(tool: str) -> Path:
    return state_home() / tool


def tool_cache_path(tool: str) -> Path:
    return cache_home() / tool


def tool_data_dir(tool: str) -> Path:
    p = tool_data_path(tool)
    p.mkdir(parents=True, exist_ok=True)
    return p


def tool_config_dir(tool: str) -> Path:
    p = tool_config_path(tool)
    p.mkdir(parents=True, exist_ok=True)
    return p


def tool_state_dir(tool: str) -> Path:
    p = tool_state_path(tool)
    p.mkdir(parents=True, exist_ok=True)
    return p


def tool_cache_dir(tool: str) -> Path:
    p = tool_cache_path(tool)
    p.mkdir(parents=True, exist_ok=True)
    return p


# ---------------------------------------------------------------------------
# agents-arwaky private config (secrets/env)
# ---------------------------------------------------------------------------
def agents_arwaky_config_dir() -> Path:
    """Private config dir: $XDG_CONFIG_HOME/agents-arwaky.

    Stores secret/env (.env) per tool with mode 0700.
    """
    p = config_home() / "agents-arwaky"
    p.mkdir(parents=True, exist_ok=True, mode=0o700)
    return p


def agent_secret_candidates(tool: str, repo_config: Path | None = None) -> list[Path]:
    """Candidate env files utk sebuah tool: kanonik -> repo config."""
    candidates = [
        agents_arwaky_config_dir() / f"{tool}.env",
    ]
    if repo_config is not None:
        candidates.append(repo_config)
    return candidates


# ---------------------------------------------------------------------------
# Source-dir discovery (re-derives internal/ & vendor/ from the repo root)
# ---------------------------------------------------------------------------
def _find_source_dirs(tool: str) -> list[Path]:
    """Find source directories for a tool (internal/ or vendor/)."""
    root = repo_root()
    candidates = []
    internal_dir = root / "internal" / f"{tool}-arwaky"
    if internal_dir.is_dir():
        candidates.append(internal_dir)
    vendor_dir = root / "vendor" / tool
    if vendor_dir.is_dir():
        candidates.append(vendor_dir)
    return candidates
