"""Context7 updater (pnpm workspace, force rebuild) — port of tools/update/update_context7.py.

Always pulls vendor/context7, removes the runtime app dir, rebuilds from
source (pnpm install + build, with the dangerouslyAllowAllBuilds patch),
and rewrites the two node launchers.
"""
from __future__ import annotations

import shutil
import subprocess
import sys

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


SRC_REL = "vendor/context7"
APP_REL = "context7"

IGNORES = shutil.ignore_patterns(
    "node_modules", ".git", ".old_modules*", "__pycache__", "mcpb",
    "dist", "target", "*.egg-info", ".venv", "venv", ".next", ".turbo",
)

LAUNCHERS = {
    "context7-mcp": "packages/mcp/dist/index.js",
    "ctx7": "packages/cli/dist/index.js",
}


class Context7Updater(IToolUpdater):
    """Force-rebuild vendor/context7 (pnpm workspace) and rewrite launchers."""

    def __init__(self, root=None) -> None:
        self._root = root or repo_root()

    def update(self, spec: ToolSpec) -> UpdateResult:
        root = self._root
        print(f">>> Updating context7 (pnpm workspace) into {data_home() / APP_REL}...")

        if not update_submodule(root, SRC_REL):
            return UpdateResult(False, spec.id, f"submodule update failed: {SRC_REL}")

        src = root / SRC_REL
        if not (src / "pnpm-workspace.yaml").exists():
            return UpdateResult(False, spec.id, "context7 source not found (submodule not initialized)")
        if shutil.which("pnpm") is None:
            return UpdateResult(False, spec.id, "pnpm is required (context7 is a pnpm workspace)")

        app_dir = data_home() / APP_REL
        if app_dir.exists():
            shutil.rmtree(app_dir)
        shutil.copytree(src, app_dir, ignore=IGNORES)

        # pnpm blocks postinstall deps by default -> allow in this copy only
        ws = app_dir / "pnpm-workspace.yaml"
        if "dangerouslyAllowAllBuilds" not in ws.read_text(encoding="utf-8", errors="replace"):
            with ws.open("a", encoding="utf-8") as f:
                f.write("\ndangerouslyAllowAllBuilds: true\n")

        try:
            subprocess.run(["pnpm", "install", "--frozen-lockfile"], cwd=app_dir, check=True)
            subprocess.run(["pnpm", "run", "build"], cwd=app_dir, check=True)
        except subprocess.CalledProcessError as exc:
            return UpdateResult(False, spec.id, f"pnpm build failed: {exc}")

        ensure_bin_home()
        for name, entry in LAUNCHERS.items():
            target = app_dir / entry
            if not target.exists():
                print(f"  Warning: entry not found {target}", file=sys.stderr)
                continue
            atomic_write_text(
                bin_home() / name,
                "#!/usr/bin/env python3\n"
                "import os, sys\n"
                f'entry = r"{target}"\n'
                'os.execvpe("node", ["node", entry, *sys.argv[1:]], os.environ.copy())\n',
            )
            print(f"  -> {bin_home() / name}")

        warn_if_bin_not_on_path()
        print(">>> Successfully updated context7")
        return UpdateResult(True, spec.id, "context7 updated")
