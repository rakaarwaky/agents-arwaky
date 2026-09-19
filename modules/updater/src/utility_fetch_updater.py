"""Fetch-mcp updater adapter — leaf utility for one manifest tool.

Mirrors the original tools/update/update_fetch_mcp.py mechanics: submodule
bump, bun workspace build into XDG data dir, node launcher rewrite.
"""
from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

from modules.shared.src.taxonomy_core_error import ToolUpdateError
from modules.shared.src.taxonomy_xdg_atomic_io import (
    ensure_bin_home,
    warn_if_bin_not_on_path,
)
from modules.shared.src.taxonomy_xdg_paths import bin_home, data_home
from modules.shared.src.utility_git_update import update_submodule
from modules.shared.src.taxonomy_tool_vo import ToolSpec

APP_DIR = data_home() / "fetch-mcp"
CLI_ARGS = {"html", "markdown", "readable", "txt", "json", "youtube", "--help", "-h", "--version", "-v"}
IGNORES = shutil.ignore_patterns(
    "node_modules", ".git", "__pycache__", "target", "*.egg-info",
    ".venv", "venv", "*.tsbuildinfo",
)


def _run(cmd: list[str], cwd: Path | None = None) -> None:
    subprocess.run(cmd, cwd=cwd, check=True)


class FetchUpdaterAdapter:
    """Fetch-mcp (bun) update sequence."""

    def is_pin_satisfied(self, spec: ToolSpec, root: Path) -> tuple[bool, str]:
        source = root / "vendor/fetch-mcp"
        if not source.exists():
            return False, "submodule not initialized"
        return False, "bun workspace (rebuild required)"

    def update(self, spec: ToolSpec, root: Path) -> list[Path]:
        source = root / "vendor/fetch-mcp"
        if not update_submodule(root, "vendor/fetch-mcp"):
            raise ToolUpdateError(f"submodule update failed: vendor/fetch-mcp")
        if not (source / "package.json").exists():
            raise ToolUpdateError("fetch-mcp source not found (submodule not initialized)")
        if not shutil.which("bun"):
            raise ToolUpdateError("fetch-mcp requires bun (curl -fsSL https://bun.sh/install | bash)")

        print(f">>> Updating fetch-mcp into {APP_DIR}...")
        if APP_DIR.exists():
            shutil.rmtree(APP_DIR)
        shutil.copytree(source, APP_DIR, ignore=IGNORES)

        _run(["bun", "install", "--frozen-lockfile"], APP_DIR)
        _run(["bun", "run", "build"], APP_DIR)

        index_js = APP_DIR / "dist/index.js"
        cli_js = APP_DIR / "dist/cli.js"
        if not index_js.exists() or not cli_js.exists():
            raise ToolUpdateError(f"build output incomplete ({index_js}, {cli_js})")

        ensure_bin_home()
        content = (
            "#!/usr/bin/env python3\n"
            "import os, sys\n"
            f'index_js = r"{index_js}"\n'
            f'cli_js = r"{cli_js}"\n'
            "cli = " + repr(sorted(CLI_ARGS)) + "\n"
            "script = cli_js if (len(sys.argv) > 1 and sys.argv[1] in cli) else index_js\n"
            "env = os.environ.copy()\n"
            'os.execvpe("node", ["node", script, *sys.argv[1:]], env)\n'
        )
        created = []
        for name in ("fetch-mcp", "mcp-fetch"):
            launcher = bin_home() / name
            launcher.write_text(content, encoding="utf-8")
            launcher.chmod(0o755)
            created.append(launcher)
            print(f"  -> {launcher}")

        warn_if_bin_not_on_path()
        print(">>> Successfully updated fetch-mcp")
        return created
