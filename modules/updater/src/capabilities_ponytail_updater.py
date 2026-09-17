"""Ponytail updater (npm, no build) — port of tools/update/update_ponytail.py.

Always pulls vendor/ponytail, removes the runtime app dir, copies source,
installs ponytail-mcp dependencies via npm, and rewrites the MCP launcher.
"""
from __future__ import annotations

import shutil
import subprocess

from modules.shared.src.git.utility_git_update import update_submodule
from modules.shared.src.paths.utility_paths import repo_root
from modules.shared.src.tool.taxonomy_tool_vo import ToolSpec, UpdateResult
from modules.shared.src.tool.contract_tool_protocol import IToolUpdater
from modules.shared.src.xdg.utility_xdg_atomic_io import (
    ensure_bin_home,
    warn_if_bin_not_on_path,
)
from modules.shared.src.xdg.utility_xdg_paths import bin_home, data_home


SRC_REL = "vendor/ponytail"
APP_REL = "ponytail"
ENTRY = "ponytail-mcp/index.js"

IGNORES = shutil.ignore_patterns(
    "node_modules", ".git", "__pycache__", "*.egg-info", ".venv", "venv",
)


class PonytailUpdater(IToolUpdater):
    """Force-reinstall vendor/ponytail (npm, no build) and rewrite the launcher."""

    def __init__(self, root=None) -> None:
        self._root = root or repo_root()

    def update(self, spec: ToolSpec) -> UpdateResult:
        root = self._root
        print(f">>> Updating ponytail (no build) into {data_home() / APP_REL}...")

        if not update_submodule(root, SRC_REL):
            return UpdateResult(False, spec.id, f"submodule update failed: {SRC_REL}")

        src = root / SRC_REL
        if not (src / "package.json").exists():
            return UpdateResult(False, spec.id, "ponytail source not found (submodule not initialized)")
        if shutil.which("npm") is None:
            return UpdateResult(False, spec.id, "npm is required (https://nodejs.org)")

        app_dir = data_home() / APP_REL
        if app_dir.exists():
            shutil.rmtree(app_dir)
        shutil.copytree(src, app_dir, ignore=IGNORES)

        mcp_dir = app_dir / "ponytail-mcp"
        if (mcp_dir / "package.json").exists():
            subprocess.run(["npm", "ci", "--no-audit", "--no-fund"], cwd=mcp_dir, check=True)

        entry = app_dir / ENTRY
        if not entry.exists():
            return UpdateResult(False, spec.id, f"entry not found {entry}")

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
        print(">>> Successfully updated ponytail")
        return UpdateResult(True, spec.id, "ponytail updated")
