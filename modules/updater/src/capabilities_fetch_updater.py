"""Fetch-mcp updater (bun, force rebuild) — port of tools/update/update_fetch_mcp.py.

Always pulls vendor/fetch-mcp, removes the runtime app dir, rebuilds from
source (`bun install` + `bun run build`), and rewrites the two dispatching
node launchers (CLI vs MCP by first argument).
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


SRC_REL = "vendor/fetch-mcp"
APP_REL = "fetch-mcp"

# First argument meaning "CLI mode" -> run dist/cli.js, otherwise MCP.
CLI_ARGS = {"html", "markdown", "readable", "txt", "json", "youtube", "--help", "-h", "--version", "-v"}

IGNORES = shutil.ignore_patterns(
    "node_modules", ".git", "__pycache__", "target", "*.egg-info",
    ".venv", "venv", "*.tsbuildinfo",
)


class FetchUpdater(IToolUpdater):
    """Force-rebuild vendor/fetch-mcp (bun) and rewrite dispatch launchers."""

    def __init__(self, root=None) -> None:
        self._root = root or repo_root()

    def update(self, spec: ToolSpec) -> UpdateResult:
        root = self._root
        print(f">>> Updating fetch-mcp into {data_home() / APP_REL}...")

        if not update_submodule(root, SRC_REL):
            return UpdateResult(False, spec.id, f"submodule update failed: {SRC_REL}")

        src = root / SRC_REL
        if not (src / "package.json").exists():
            return UpdateResult(False, spec.id, "fetch-mcp source not found (submodule not initialized)")
        if shutil.which("bun") is None:
            return UpdateResult(False, spec.id, "bun is required (curl -fsSL https://bun.sh/install | bash)")

        app_dir = data_home() / APP_REL
        if app_dir.exists():
            shutil.rmtree(app_dir)
        shutil.copytree(src, app_dir, ignore=IGNORES)

        try:
            subprocess.run(["bun", "install", "--frozen-lockfile"], cwd=app_dir, check=True)
            subprocess.run(["bun", "run", "build"], cwd=app_dir, check=True)
        except subprocess.CalledProcessError as exc:
            return UpdateResult(False, spec.id, f"bun build failed: {exc}")

        index_js = app_dir / "dist/index.js"
        cli_js = app_dir / "dist/cli.js"
        if not index_js.exists() or not cli_js.exists():
            return UpdateResult(False, spec.id, f"build output incomplete ({index_js}, {cli_js})")

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
        return UpdateResult(True, spec.id, "fetch-mcp updated")
