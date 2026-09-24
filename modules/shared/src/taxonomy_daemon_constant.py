"""Daemon-domain constants — 9Router / Anytype host service parameters (AES layer: taxonomy)."""
from __future__ import annotations

import os

from modules.shared.src.taxonomy_common_constant import REPO_ROOT
from modules.shared.src.taxonomy_common_vo import config_home, data_home, state_home

#: Repository root for deploy unit sources.
ROOT = REPO_ROOT

#: 9Router gateway listen port (env-overridable).
PORT = os.environ.get("NINEROUTER_PORT", "20128")

#: 9Router XDG data root.
DATA_DIR = data_home() / "9router"

#: systemd user unit directory and 9Router unit path.
UNIT_DIR = config_home() / "systemd/user"
UNIT_FILE = UNIT_DIR / "9router.service"

#: Known-weak / placeholder INITIAL_PASSWORD values (warn on install).
WEAK_PASSWORDS = frozenset(
    {"change-me-to-a-strong-password", "", "password", "admin"}
)

#: Anytype headless container identity.
CONTAINER_NAME = "anytype-daemon"
IMAGE_NAME = "localhost/anytype-daemon:latest"

#: Anytype API port parsed from ANYTYPE_API_BASE_URL (default 31012).
ANYTYPE_PORT = os.environ.get(
    "ANYTYPE_API_BASE_URL", "http://127.0.0.1:31012"
).split(":")[-1].strip("/")

#: Anytype XDG layout.
ANYTYPE_DATA_DIR = data_home() / "anytype-mcp"
DOT_ANYTYPE = data_home() / "anytype"
ANYTYPE_CONFIG_DIR = config_home() / "anytype"
SHARE_DIR = data_home() / "anytype" / "share"
LOCAL_BIN = data_home() / "anytype-mcp/bin"
ANYTYPE_SCRIPT_DIR = ROOT / "modules/daemon/deploy"
ANYTYPE_UNIT_FILE = UNIT_DIR / "anytype-daemon.service"
DATA_ROOT = data_home() / "anytype-mcp"
PID_FILE = state_home() / "anytype-daemon.pid"

__all__ = [
    "ANYTYPE_CONFIG_DIR",
    "ANYTYPE_DATA_DIR",
    "ANYTYPE_PORT",
    "ANYTYPE_SCRIPT_DIR",
    "ANYTYPE_UNIT_FILE",
    "CONTAINER_NAME",
    "DATA_DIR",
    "DATA_ROOT",
    "DOT_ANYTYPE",
    "IMAGE_NAME",
    "LOCAL_BIN",
    "PID_FILE",
    "PORT",
    "ROOT",
    "SHARE_DIR",
    "UNIT_DIR",
    "UNIT_FILE",
    "WEAK_PASSWORDS",
]
