"""Ponytail installer (npm, no build) — port of tools/install/install_ponytail.py.

@dietrichgebert/ponytail has NO build script and no lockfile — just copy
source to $XDG_DATA_HOME/ponytail and install ponytail-mcp dependencies via
npm. Entry MCP = ponytail-mcp/index.js.
"""
from __future__ import annotations

import shutil
import subprocess
import sys

from modules.shared.src.paths.utility_paths import repo_root
from modules.shared.src.tool.taxonomy_tool_vo import InstallResult, ToolSpec
from modules.shared.src.tool.contract_tool_protocol import IToolInstaller
from modules.shared.src.xdg.utility_xdg_atomic_io import (
    ensure_bin_home,
    warn_if_bin_not_on_path,
)
from modules.shared.src.xdg.utility_xdg_paths import bin_home, data_home


ENTRY = "ponytail-mcp/index.js"
IGNORES = shutil.ignore_patterns(
    "node_modules", ".git", "__pycache__", "*.egg-info", ".venv", "venv",
)


class PonytailInstaller(IToolInstaller):
    """Install vendor/ponytail (npm, no build) into XDG data, write MCP launcher."""

    def __init__(self, root=None) -> None:
        self._root = root or repo_root()

    def install(self, spec: ToolSpec) -> InstallResult:
        root = self._root
        if (bin_home() / "ponytail-mcp").exists():
            return InstallResult(True, spec.id, "ponytail is already installed")

        src = root / "vendor/ponytail"
        if not (src / "package.json").exists():
            return InstallResult(False, spec.id, "ponytail source not found (submodule not initialized)")
        if shutil.which("npm") is None:
            return InstallResult(False, spec.id, "npm is required (https://nodejs.org)")

        app_dir = data_home() / "ponytail"
        print(f">>> Installing ponytail (no build) into {app_dir}...")
        if app_dir.exists():
            shutil.rmtree(app_dir)
        shutil.copytree(src, app_dir, ignore=IGNORES)

        mcp_dir = app_dir / "ponytail-mcp"
        if (mcp_dir / "package.json").exists():
            subprocess.run(["npm", "ci", "--no-audit", "--no-fund"], cwd=mcp_dir, check=True)

        entry = app_dir / ENTRY
        if not entry.exists():
            return InstallResult(False, spec.id, f"entry not found {entry}")

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
        return InstallResult(True, spec.id, "ponytail installed")
