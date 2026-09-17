"""Codegraph installer (npm) — port of tools/install/install_codegraph.py.

@colbymchenry/codegraph is a TypeScript project built with npm. Lockfile
package-lock.json -> `npm ci`; build `npm run build` (tsc + copy-assets +
build:ui) produces dist/bin/codegraph.js. Launchers codegraph-mcp &
codegraph both point at dist/bin/codegraph.js (tool dispatches mode via args).
"""
from __future__ import annotations

import shutil
import subprocess
import sys

from modules.shared.src.paths.utility_paths import repo_root
from modules.shared.src.tool.taxonomy_tool_vo import InstallResult, ToolSpec
from modules.shared.src.tool.contract_tool_protocol import IToolInstaller
from modules.shared.src.xdg.utility_xdg_atomic_io import (
    atomic_write_text,
    ensure_bin_home,
    warn_if_bin_not_on_path,
)
from modules.shared.src.xdg.utility_xdg_paths import bin_home, data_home


ENTRY = "dist/bin/codegraph.js"
LAUNCHERS = ["codegraph-mcp", "codegraph"]

IGNORES = shutil.ignore_patterns(
    "node_modules", ".git", "__pycache__", "target", "*.egg-info",
    ".venv", "venv", "*.tsbuildinfo",
)


class CodegraphInstaller(IToolInstaller):
    """Install vendor/codegraph (npm) into XDG data, build, write launchers."""

    def __init__(self, root=None) -> None:
        self._root = root or repo_root()

    def install(self, spec: ToolSpec) -> InstallResult:
        root = self._root
        if (bin_home() / "codegraph-mcp").exists():
            return InstallResult(True, spec.id, "codegraph is already installed")

        src = root / "vendor/codegraph"
        if not (src / "package.json").exists():
            return InstallResult(False, spec.id, "codegraph source not found (submodule not initialized)")
        if shutil.which("npm") is None:
            return InstallResult(False, spec.id, "npm is required (https://nodejs.org)")

        app_dir = data_home() / "codegraph"
        print(f">>> Installing codegraph into {app_dir}...")
        if app_dir.exists():
            shutil.rmtree(app_dir)
        shutil.copytree(src, app_dir, ignore=IGNORES)

        try:
            subprocess.run(["npm", "ci", "--no-audit", "--no-fund"], cwd=app_dir, check=True)
            subprocess.run(["npm", "run", "build"], cwd=app_dir, check=True)
        except subprocess.CalledProcessError as exc:
            return InstallResult(False, spec.id, f"npm build failed: {exc}")

        entry = app_dir / ENTRY
        if not entry.exists():
            return InstallResult(False, spec.id, f"entry not found {entry}")

        ensure_bin_home()
        for name in LAUNCHERS:
            launcher = bin_home() / name
            atomic_write_text(
                launcher,
                "#!/usr/bin/env python3\n"
                "import os, sys\n"
                f'entry = r"{entry}"\n'
                'os.execvpe("node", ["node", entry, *sys.argv[1:]], os.environ.copy())\n',
            )
            print(f"  -> {launcher}")

        warn_if_bin_not_on_path()
        return InstallResult(True, spec.id, "codegraph installed")
