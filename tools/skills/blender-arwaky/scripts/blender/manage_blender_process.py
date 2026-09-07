"""Cross-platform Blender process manager.

Starts Blender in background mode running ``run_server_headless.py`` and waits
for the MCP TCP port to open.

Usage:
    uv run python scripts/blender/manage_blender_process.py

Environment:
    BLENDER_EXECUTABLE  Absolute path to the Blender binary. If unset, the
                        script falls back to ``blender`` on ``PATH``.
"""

from __future__ import annotations

import os
import socket
import subprocess
import sys
import time
from pathlib import Path
from typing import Final

IS_WINDOWS: Final[bool] = sys.platform.startswith("win")
IS_MACOS: Final[bool] = sys.platform == "darwin"

SCRIPT_DIR: Final[Path] = Path(__file__).parent.resolve()
PROJECT_ROOT: Final[Path] = SCRIPT_DIR.parent.parent
BLENDER_DEFAULT: Final[str] = (
    r"C:\Program Files\Blender Foundation\Blender\blender.exe"
    if IS_WINDOWS
    else "/Applications/Blender.app/Contents/MacOS/Blender"
    if IS_MACOS
    else "/usr/bin/blender"
)
BLENDER_PATH: Final[str] = os.environ.get("BLENDER_EXECUTABLE", BLENDER_DEFAULT)
HEADLESS_SCRIPT: Final[Path] = SCRIPT_DIR / "run_server_headless.py"
LOG_PATH: Final[Path] = PROJECT_ROOT / "log" / "blender.log"
MCP_PORT: Final[int] = 9876
PORT_WAIT_SECONDS: Final[int] = 30


def is_port_open(port: int, host: str = "localhost") -> bool:
    """Return ``True`` if a TCP connection to ``host:port`` succeeds."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(0.5)
        return sock.connect_ex((host, port)) == 0


def kill_existing_blender() -> None:
    """Terminate any running Blender instance (cross-platform)."""
    if IS_WINDOWS:
        # /F = force, /IM = image name
        subprocess.run(
            ["taskkill", "/F", "/IM", "blender.exe"],
            capture_output=True,
            check=False,
        )
    else:
        subprocess.run(["pkill", "-x", "blender"], capture_output=True, check=False)
    time.sleep(1)


def build_environment() -> dict[str, str]:
    """Return a copy of the environment with sensible display defaults."""
    env = os.environ.copy()
    if IS_WINDOWS or IS_MACOS:
        return env
    # Linux/BSD: provide X11/Wayland defaults for headless sessions.
    env.setdefault("DISPLAY", ":0")
    env.setdefault("WAYLAND_DISPLAY", "wayland-1")
    return env


def start_blender() -> bool:
    """Start Blender in the background and block until the MCP port is open."""
    if not HEADLESS_SCRIPT.exists():
        print(f"ERROR: Headless script not found at {HEADLESS_SCRIPT}")
        return False

    kill_existing_blender()
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    env = build_environment()

    print(f"Starting Blender with log: {LOG_PATH}")
    # The log file handle is dup'd by Popen into the child process, so it
    # remains valid for the detached Blender even after the context manager
    # closes the parent's handle.
    with open(LOG_PATH, "w", encoding="utf-8") as log_file:
        popen_kwargs: dict[str, object] = {
            "stdout": log_file,
            "stderr": subprocess.STDOUT,
            "env": env,
        }
        if IS_WINDOWS:
            # Detach into a new process group so the manager can exit independently.
            popen_kwargs["creationflags"] = subprocess.CREATE_NEW_PROCESS_GROUP
        else:
            popen_kwargs["preexec_fn"] = os.setpgrp

        process = subprocess.Popen(
            [BLENDER_PATH, "--background", "--python", str(HEADLESS_SCRIPT)],
            **popen_kwargs,
        )
        print(f"Started Blender (PID: {process.pid})")

        print(f"Waiting for port {MCP_PORT}...")
        for _ in range(PORT_WAIT_SECONDS):
            if is_port_open(MCP_PORT):
                print(f"Port {MCP_PORT} is OPEN!")
                return True
            time.sleep(1)
            if process.poll() is not None:
                print("Process died unexpectedly — check log/blender.log")
                return False

    print(f"Timed out waiting for port {MCP_PORT}.")
    return False

    print(f"Timed out waiting for port {MCP_PORT}.")
    return False


if __name__ == "__main__":
    sys.exit(0 if start_blender() else 1)
