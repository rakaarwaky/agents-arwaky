"""Fetch-mcp installer (bun) — port of tools/install/install_fetch_mcp.py.

zcaceres/fetch-mcp is a TypeScript project built with bun. Output:
  - dist/index.js -> MCP server (fetch-mcp, mcp-fetch)
  - dist/cli.js   -> CLI mode (html/markdown/readable/txt/json/youtube/...)
The launcher dispatches CLI vs MCP based on the first argument.
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


# First argument meaning "CLI mode" -> run dist/cli.js, otherwise MCP.
CLI_ARGS = {"html", "markdown", "readable", "txt", "json", "youtube", "--help", "-h", "--version", "-v"}

IGNORES = shutil.ignore_patterns(
    "node_modules", ".git", "__pycache__", "target", "*.egg-info",
    ".venv", "venv", "*.tsbuildinfo",
)


class FetchInstaller(IToolInstaller):
    """Install vendor/fetch-mcp (bun) into XDG data, build, write CLI/MCP dispatch launcher."""

    def __init__(self, root=None) -> None:
        self._root = root or repo_root()

    def install(self, spec: ToolSpec) -> InstallResult:
        root = self._root
        if (bin_home() / "fetch-mcp").exists():
            return InstallResult(True, spec.id, "fetch-mcp is already installed")

        src = root / "vendor/fetch-mcp"
        if not (src / "package.json").exists():
            return InstallResult(False, spec.id, "fetch-mcp source not found (submodule not initialized)")
        if shutil.which("bun") is None:
            return InstallResult(False, spec.id, "bun is required (curl -fsSL https://bun.sh/install | bash)")

        app_dir = data_home() / "fetch-mcp"
        print(f">>> Installing fetch-mcp into {app_dir}...")
        if app_dir.exists():
            shutil.rmtree(app_dir)
        shutil.copytree(src, app_dir, ignore=IGNORES)

        try:
            subprocess.run(["bun", "install", "--frozen-lockfile"], cwd=app_dir, check=True)
            subprocess.run(["bun", "run", "build"], cwd=app_dir, check=True)
        except subprocess.CalledProcessError as exc:
            return InstallResult(False, spec.id, f"bun build failed: {exc}")

        index_js = app_dir / "dist/index.js"
        cli_js = app_dir / "dist/cli.js"
        if not index_js.exists() or not cli_js.exists():
            return InstallResult(False, spec.id, f"build output incomplete ({index_js}, {cli_js})")

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
        return InstallResult(True, spec.id, "fetch-mcp installed")
