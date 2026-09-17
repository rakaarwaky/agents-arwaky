"""Codegraph updater (npm, force rebuild) — port of tools/update/update_codegraph.py.

Always pulls vendor/codegraph, removes the runtime app dir, rebuilds from
source (`npm ci` + `npm run build`), and rewrites the two node launchers.
"""
from __future__ import annotations

import shutil
import subprocess

from modules.shared.src.git.utility_git_update import update_submodule
from modules.shared.src.paths.utility_paths import repo_root
from modules.shared.src.tool.taxonomy_tool_vo import ToolSpec, UpdateResult
from modules.shared.src.tool.contract_tool_protocol import IToolUpdater
from modules.shared.src.xdg.utility_xdg_atomic_io import (
    atomic_write_text,
    ensure_bin_home,
    warn_if_bin_not_on_path,
)
from modules.shared.src.xdg.utility_xdg_paths import bin_home, data_home


SRC_REL = "vendor/codegraph"
APP_REL = "codegraph"
ENTRY = "dist/bin/codegraph.js"
LAUNCHERS = ["codegraph-mcp", "codegraph"]

IGNORES = shutil.ignore_patterns(
    "node_modules", ".git", "__pycache__", "target", "*.egg-info",
    ".venv", "venv", "*.tsbuildinfo",
)


class CodegraphUpdater(IToolUpdater):
    """Force-rebuild vendor/codegraph (npm) and rewrite launchers."""

    def __init__(self, root=None) -> None:
        self._root = root or repo_root()

    def update(self, spec: ToolSpec) -> UpdateResult:
        root = self._root
        print(f">>> Updating codegraph into {data_home() / APP_REL}...")

        if not update_submodule(root, SRC_REL):
            return UpdateResult(False, spec.id, f"submodule update failed: {SRC_REL}")

        src = root / SRC_REL
        if not (src / "package.json").exists():
            return UpdateResult(False, spec.id, "codegraph source not found (submodule not initialized)")
        if shutil.which("npm") is None:
            return UpdateResult(False, spec.id, "npm is required (https://nodejs.org)")

        app_dir = data_home() / APP_REL
        if app_dir.exists():
            shutil.rmtree(app_dir)
        shutil.copytree(src, app_dir, ignore=IGNORES)

        try:
            subprocess.run(["npm", "ci", "--no-audit", "--no-fund"], cwd=app_dir, check=True)
            subprocess.run(["npm", "run", "build"], cwd=app_dir, check=True)
        except subprocess.CalledProcessError as exc:
            return UpdateResult(False, spec.id, f"npm build failed: {exc}")

        entry = app_dir / ENTRY
        if not entry.exists():
            return UpdateResult(False, spec.id, f"entry not found {entry}")

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
        print(">>> Successfully updated codegraph")
        return UpdateResult(True, spec.id, "codegraph updated")
