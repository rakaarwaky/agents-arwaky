"""Ponytail updater adapter — leaf utility for one manifest tool.

Mirrors the original tools/update/update_ponytail.py mechanics: submodule
bump, npm build into XDG data dir, node launcher rewrite.
"""
from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

from modules.shared.src.taxonomy_core_error import ToolUpdateError
from modules.shared.src.taxonomy_xdg_atomic_io import (
    atomic_write_text,
    ensure_bin_home,
    warn_if_bin_not_on_path,
)
from modules.shared.src.taxonomy_xdg_paths import bin_home, data_home
from modules.shared.src.utility_git_update import update_submodule
from modules.shared.src.taxonomy_tool_vo import ToolSpec

APP_DIR = data_home() / "ponytail"
ENTRY = "ponytail-mcp/index.js"
IGNORES = shutil.ignore_patterns(
    "node_modules", ".git", "__pycache__", "*.egg-info", ".venv", "venv",
)


def _run(cmd: list[str], cwd: Path | None = None) -> None:
    subprocess.run(cmd, cwd=cwd, check=True)


class PonytailUpdaterAdapter:
    """Ponytail (npm) update sequence."""

    def is_pin_satisfied(self, spec: ToolSpec, root: Path) -> tuple[bool, str]:
        source = root / "vendor/ponytail"
        if not source.exists():
            return False, "submodule not initialized"
        return False, "npm workspace (rebuild required)"

    def update(self, spec: ToolSpec, root: Path) -> list[Path]:
        source = root / "vendor/ponytail"
        if not update_submodule(root, "vendor/ponytail"):
            raise ToolUpdateError(f"submodule update failed: vendor/ponytail")
        if not (source / "package.json").exists():
            raise ToolUpdateError("ponytail source not found (submodule not initialized)")
        if not shutil.which("npm"):
            raise ToolUpdateError("ponytail requires npm (https://nodejs.org)")

        print(f">>> Updating ponytail into {APP_DIR}...")
        if APP_DIR.exists():
            shutil.rmtree(APP_DIR)
        shutil.copytree(source, APP_DIR, ignore=IGNORES)

        mcp_dir = APP_DIR / "ponytail-mcp"
        if (mcp_dir / "package.json").exists():
            _run(["npm", "ci", "--no-audit", "--no-fund"], mcp_dir)

        entry = APP_DIR / ENTRY
        if not entry.exists():
            raise ToolUpdateError(f"entry not found {entry}")

        ensure_bin_home()
        launcher = bin_home() / "ponytail-mcp"
        atomic_write_text(
            launcher,
            "#!/usr/bin/env python3\n"
            "import os, sys\n"
            f'entry = r"{entry}"\n'
            'os.execvpe("node", ["node", entry, *sys.argv[1:]], os.environ.copy())\n',
        )
        print(f"  -> {launcher}")

        warn_if_bin_not_on_path()
        print(">>> Successfully updated ponytail")
        return [launcher]
