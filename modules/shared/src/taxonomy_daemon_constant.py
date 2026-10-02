"""Daemon-domain constants — 9Router / Anytype host service parameters (AES layer: taxonomy)."""
from __future__ import annotations

import os
from pathlib import Path

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

#: OmniRoute listen port (env-overridable). This is the port the pre-existing
#: installation already used, and its state at ``~/.omniroute`` is bound to it:
#: moving the port changes nothing about the data, but rotating
#: ``STORAGE_ENCRYPTION_KEY`` would make every stored provider credential
#: unreadable, so the key in that file is never regenerated here.
#:
#: OmniRoute serves dashboard and API from a single port unless ``API_PORT`` /
#: ``DASHBOARD_PORT`` are set separately (see ``bin/cli/commands/serve.mjs`` in
#: the pinned checkout); the existing config sets neither, so one port is used.
OMNIROUTE_PORT = os.environ.get("OMNIROUTE_PORT", "7777")
OMNIROUTE_HOST = os.environ.get("OMNIROUTE_HOST", "127.0.0.1")

#: OmniRoute XDG layout. Upstream keeps its own working directory at
#: ``~/.omniroute`` and reads ``.env`` from there — that is where the live
#: ``storage.sqlite`` (provider connections, API keys, usage history) and the
#: matching ``STORAGE_ENCRYPTION_KEY`` live, so it is the only correct location
#: to point the unit at.
OMNIROUTE_DATA_DIR = Path.home() / ".omniroute"
OMNIROUTE_CONFIG_DIR = OMNIROUTE_DATA_DIR
OMNIROUTE_ENV_FILE = OMNIROUTE_DATA_DIR / ".env"
OMNIROUTE_UNIT_FILE = UNIT_DIR / "omniroute.service"

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
