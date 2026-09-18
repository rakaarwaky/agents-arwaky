"""Ponytail installer (npm, no build) — verbatim port of tools/install/install_ponytail.py.

@dietrichgebert/ponytail has NO build script and no lockfile — just copy
source to $XDG_DATA_HOME/ponytail and install ponytail-mcp dependencies
(@modelcontextprotocol/sdk, zod) via npm. Entry MCP = ponytail-mcp/index.js.
"""
from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

from modules.shared.src.common.paths.utility_paths import repo_root
from modules.shared.src.common.tool.taxonomy_tool_vo import InstallResult, ToolSpec
from modules.shared.src.common.tool.contract_tool_protocol import IToolInstaller
from modules.shared.src.xdg.utility_xdg_atomic_io import (
    ensure_bin_home,
    warn_if_bin_not_on_path,
)
from modules.shared.src.xdg.utility_xdg_paths import bin_home, data_home

ROOT = repo_root()

SRC = ROOT / "vendor/ponytail"
APP_DIR = data_home() / "ponytail"
ENTRY = "ponytail-mcp/index.js"

# Old node_modules in vendor are not copied (may be stale); deps are reinstalled
# with npm --prefix inside APP_DIR/ponytail-mcp.
IGNORES = shutil.ignore_patterns(
    "node_modules", ".git", "__pycache__", "*.egg-info", ".venv", "venv",
)


def run(cmd, cwd=None):
    subprocess.run(cmd, cwd=cwd, check=True)


def _require(tool: str, reason: str) -> bool:
    if shutil.which(tool):
        return True
    print(f"Error: {tool} not found in PATH. {reason}", file=sys.stderr)
    return False


def is_installed() -> bool:
    """Check if ponytail is already installed (binary exists)."""
    return (bin_home() / "ponytail-mcp").exists()


def _install_ponytail() -> int:
    if is_installed():
        print(">>> ponytail is already installed. Use 'aa update ponytail' to reinstall.")
        return 0

    if not (SRC / "package.json").exists():
        print("Error: ponytail source not found (submodule not initialized).", file=sys.stderr)
        return 1
    if not _require("npm", "ponytail requires npm (https://nodejs.org)"):
        return 1

    print(f">>> Installing ponytail (no build) into {APP_DIR}...")
    if APP_DIR.exists():
        shutil.rmtree(APP_DIR)
    shutil.copytree(SRC, APP_DIR, ignore=IGNORES)

    mcp_dir = APP_DIR / "ponytail-mcp"
    if (mcp_dir / "package.json").exists():
        run(["npm", "ci", "--no-audit", "--no-fund"], mcp_dir)

    entry = APP_DIR / ENTRY
    if not entry.exists():
        print(f"  Error: entry not found {entry}", file=sys.stderr)
        return 1

    ensure_bin_home()
    launcher = bin_home() / "ponytail-mcp"
    launcher.write_text(
        "#!/usr/bin/env python3\n"
        "import os, sys\n"
        f'entry = r"{entry}"\n'
        'os.execvpe("node", ["node", entry, *sys.argv[1:]], os.environ.copy())\n',
        encoding="utf-8",
    )
    launcher.chmod(0o755)
    print(f"  -> {launcher}")

    warn_if_bin_not_on_path()
    print(">>> Successfully installed ponytail")
    return 0


class PonytailInstaller(IToolInstaller):
    """Install vendor/ponytail (npm, no build) into XDG data, write MCP launcher."""

    def __init__(self, root=None) -> None:
        self._root = root or ROOT

    def install(self, spec: ToolSpec) -> InstallResult:
        rc = _install_ponytail()
        return InstallResult(
            rc == 0,
            spec.id,
            "ponytail installed" if rc == 0 else "ponytail install failed",
        )
