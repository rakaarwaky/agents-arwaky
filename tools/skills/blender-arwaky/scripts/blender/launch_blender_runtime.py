"""Cross-platform Blender launcher with sensible display defaults.

Replaces the previous ``launch_blender.sh`` script. On Linux/BSD it sets
``DISPLAY``/``WAYLAND_DISPLAY`` defaults for headless sessions; on Windows
and macOS the environment is passed through unchanged.

Usage:
    uv run python scripts/blender/launch_blender_runtime.py [-- <blender args>...]

Environment:
    BLENDER_EXECUTABLE  Absolute path to the Blender binary. Falls back to
                        ``blender`` on ``PATH`` (or platform defaults).
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

IS_WINDOWS = sys.platform.startswith("win")
IS_MACOS = sys.platform == "darwin"
IS_LINUX = sys.platform.startswith("linux")

BLENDER_DEFAULT = (
    r"C:\Program Files\Blender Foundation\Blender\blender.exe"
    if IS_WINDOWS
    else "/Applications/Blender.app/Contents/MacOS/Blender"
    if IS_MACOS
    else "/usr/bin/blender"
)


def resolve_blender() -> str:
    """Return the Blender binary path (env override, then PATH, then default)."""
    env_path = os.environ.get("BLENDER_EXECUTABLE")
    if env_path and Path(env_path).exists():
        return env_path
    on_path = shutil.which("blender")
    if on_path:
        return on_path
    return BLENDER_DEFAULT


def build_environment() -> dict[str, str]:
    """Return environment with display defaults for Linux only."""
    env = os.environ.copy()
    if IS_LINUX:
        env.setdefault("DISPLAY", ":0")
        env.setdefault("WAYLAND_DISPLAY", "wayland-1")
    return env


def split_extra_args(argv: list[str]) -> list[str]:
    """Extract args after ``--`` so callers can forward flags to Blender."""
    if "--" in argv:
        sep = argv.index("--")
        return argv[sep + 1 :]
    return []


def main() -> int:
    blender = resolve_blender()
    extra_args = split_extra_args(sys.argv[1:])

    env = build_environment()
    cmd = [blender, *extra_args]
    print(f"Launching: {' '.join(cmd)}")
    completed = subprocess.run(cmd, env=env, check=False)
    return completed.returncode


if __name__ == "__main__":
    sys.exit(main())
