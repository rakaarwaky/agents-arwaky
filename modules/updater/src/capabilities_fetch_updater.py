"""Fetch-mcp updater — VERBATIM port of tools/update/update_fetch_mcp.py.

Keep the ENTIRE original body: every function, every constant, every
print statement, every edge-case message, every subprocess call, exactly
as written in the original. The ONLY differences:
1. Import paths (all AES equivalents under modules/shared/src/).
"""
from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

from modules.shared.src.paths.utility_paths import repo_root

ROOT = repo_root()

from modules.shared.src.xdg.utility_xdg_atomic_io import (
    atomic_write_text,
    ensure_bin_home,
    warn_if_bin_not_on_path,
)
from modules.shared.src.xdg.utility_xdg_paths import bin_home, data_home
from modules.shared.src.git.utility_git_update import update_submodule
from modules.shared.src.tool.taxonomy_tool_vo import ToolSpec, UpdateResult
from modules.updater.src.contract_tool_updater import IToolUpdater

SRC = ROOT / "vendor/fetch-mcp"
APP_DIR = data_home() / "fetch-mcp"

CLI_ARGS = {"html", "markdown", "readable", "txt", "json", "youtube", "--help", "-h", "--version", "-v"}

IGNORES = shutil.ignore_patterns(
    "node_modules", ".git", "__pycache__", "target", "*.egg-info",
    ".venv", "venv", "*.tsbuildinfo",
)


def run(cmd, cwd=None):
    subprocess.run(cmd, cwd=cwd, check=True)


def _require(tool: str, reason: str) -> bool:
    if shutil.which(tool):
        return True
    print(f"Error: {tool} not found in PATH. {reason}", file=sys.stderr)
    return False


def main() -> int:
    # Pull latest from remote
    update_submodule(ROOT, "vendor/fetch-mcp")

    if not (SRC / "package.json").exists():
        print("Error: fetch-mcp source not found (submodule not initialized).", file=sys.stderr)
        return 1
    if not _require("bun", "fetch-mcp requires bun (curl -fsSL https://bun.sh/install | bash)"):
        return 1

    print(f">>> Updating fetch-mcp into {APP_DIR}...")
    if APP_DIR.exists():
        shutil.rmtree(APP_DIR)
    shutil.copytree(SRC, APP_DIR, ignore=IGNORES)

    run(["bun", "install", "--frozen-lockfile"], APP_DIR)
    run(["bun", "run", "build"], APP_DIR)

    index_js = APP_DIR / "dist/index.js"
    cli_js = APP_DIR / "dist/cli.js"
    if not index_js.exists() or not cli_js.exists():
        print(f"  Error: build output incomplete ({index_js}, {cli_js})", file=sys.stderr)
        return 1

    ensure_bin_home()
    content = (
        "#!/usr/bin/env python3\n"
        "import os, sys\n"
        f'index_js = r"{index_js}"\n'
        f'cli_js = r"{cli_js}"\n'
        "cli = " + repr(sorted(CLI_ARGS)) + "\n"
        "script = cli_js if (len(sys.argv) > 1 and sys.argv[1] in cli) else index_js\n"
        'env = os.environ.copy()\n'
        'os.execvpe("node", ["node", script, *sys.argv[1:]], env)\n'
    )
    for name in ("fetch-mcp", "mcp-fetch"):
        launcher = bin_home() / name
        launcher.write_text(content, encoding="utf-8")
        launcher.chmod(0o755)
        print(f"  -> {launcher}")

    warn_if_bin_not_on_path()
    print(">>> Successfully updated fetch-mcp")
    return 0


class FetchUpdater(IToolUpdater):
    def __init__(self, root=None) -> None:
        self._root = root or ROOT

    def update(self, spec: ToolSpec) -> UpdateResult:
        rc = main()
        return UpdateResult(rc == 0, spec.id, "fetch-mcp updated" if rc == 0 else "fetch-mcp update failed")
