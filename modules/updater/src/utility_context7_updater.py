"""Context7 updater adapter — leaf utility for one manifest tool.

Mirrors the original tools/update/update_context7.py mechanics: submodule
bump, pnpm workspace build into XDG data dir, node launcher rewrite.
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


def _run(cmd: list[str], cwd: Path | None = None) -> None:
    """Subprocess with check (module-level helper for adapters in this tree)."""
    subprocess.run(cmd, cwd=cwd, check=True)


APP_DIR = data_home() / "context7"
IGNORES = shutil.ignore_patterns(
    "node_modules", ".git", ".old_modules*", "__pycache__", "mcpb",
    "dist", "target", "*.egg-info", ".venv", "venv", ".next", ".turbo",
)
LAUNCHERS = {
    "context7-mcp": "packages/mcp/dist/index.js",
    "ctx7": "packages/cli/dist/index.js",
}


class Context7UpdaterAdapter:
    """Context7 (pnpm workspace) update sequence."""

    def is_pin_satisfied(self, spec: ToolSpec, root: Path) -> tuple[bool, str]:
        source = root / "vendor/context7"
        if not source.exists():
            return False, "submodule not initialized"
        return False, "pnpm workspace (rebuild required)"

    def update(self, spec: ToolSpec, root: Path) -> list[Path]:
        source = root / "vendor/context7"
        if not update_submodule(root, "vendor/context7"):
            raise ToolUpdateError(f"submodule update failed: vendor/context7")
        if not (source / "pnpm-workspace.yaml").exists():
            raise ToolUpdateError("context7 source not found (submodule not initialized)")
        if not shutil.which("pnpm"):
            raise ToolUpdateError("pnpm is required (context7 is a pnpm workspace)")

        print(f">>> Updating context7 (pnpm workspace) into {APP_DIR}...")
        if APP_DIR.exists():
            shutil.rmtree(APP_DIR)
        shutil.copytree(source, APP_DIR, ignore=IGNORES)

        workspace = APP_DIR / "pnpm-workspace.yaml"
        if "dangerouslyAllowAllBuilds" not in workspace.read_text(encoding="utf-8", errors="replace"):
            with workspace.open("a", encoding="utf-8") as fh:
                fh.write("\ndangerouslyAllowAllBuilds: true\n")

        self._run(["pnpm", "install", "--frozen-lockfile"], APP_DIR)
        self._run(["pnpm", "run", "build"], APP_DIR)

        ensure_bin_home()
        created: list[Path] = []
        for name, entry in LAUNCHERS.items():
            target = APP_DIR / entry
            if not target.exists():
                print(f"  Warning: entry not found {target}", file=sys.stderr)
                continue
            launcher = bin_home() / name
            atomic_write_text(
                launcher,
                "#!/usr/bin/env python3\n"
                "import os, sys\n"
                f'entry = r"{target}"\n'
                'os.execvpe("node", ["node", entry, *sys.argv[1:]], os.environ.copy())\n',
            )
            created.append(launcher)
            print(f"  -> {launcher}")

        warn_if_bin_not_on_path()
        print(">>> Successfully updated context7")
        return created

    @staticmethod
    def _run(cmd: list[str], cwd: Path) -> None:
        subprocess.run(cmd, cwd=cwd, check=True)
