"""XDG Base Directory helpers (Python) — pengganti tools/lib/xdg.sh."""
from __future__ import annotations

import os
from pathlib import Path


def data_home() -> Path:
    return Path(os.environ.get("XDG_DATA_HOME", str(Path.home() / ".local/share")))


def config_home() -> Path:
    return Path(os.environ.get("XDG_CONFIG_HOME", str(Path.home() / ".config")))


def cache_home() -> Path:
    return Path(os.environ.get("XDG_CACHE_HOME", str(Path.home() / ".cache")))


def bin_home() -> Path:
    return Path(os.environ.get("XDG_BIN_HOME", str(Path.home() / ".local/bin")))


def ensure_bin_home() -> None:
    b = bin_home()
    b.mkdir(parents=True, exist_ok=True)


def ensure_path() -> None:
    b = str(bin_home())
    ensure_bin_home()
    paths = os.environ.get("PATH", "").split(os.pathsep)
    if b not in paths:
        os.environ["PATH"] = b + os.pathsep + os.environ.get("PATH", "")


def tool_data_dir(tool: str) -> Path:
    p = data_home() / tool
    p.mkdir(parents=True, exist_ok=True)
    return p


def tool_config_dir(tool: str) -> Path:
    p = config_home() / tool
    p.mkdir(parents=True, exist_ok=True)
    return p


def tool_cache_dir(tool: str) -> Path:
    p = cache_home() / tool
    p.mkdir(parents=True, exist_ok=True)
    return p
