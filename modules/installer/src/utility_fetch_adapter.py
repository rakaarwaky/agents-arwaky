"""Fetch-mcp adapter (bun) — verbatim port of tools/install/install_fetch_mcp.py.

zcaceres/fetch-mcp is a TypeScript project built with bun. Output:
  - dist/index.js -> MCP server (fetch-mcp, mcp-fetch)
  - dist/cli.js   -> CLI mode (html/markdown/readable/txt/json/youtube/...)
The launcher dispatches CLI vs MCP based on the first argument.
"""
from __future__ import annotations

from pathlib import Path

from modules.shared.src.taxonomy_xdg_atomic_io import (
    ensure_bin_home,
    warn_if_bin_not_on_path,
)
from modules.shared.src.taxonomy_xdg_paths import bin_home, data_home
from modules.shared.src.taxonomy_tool_vo import ToolSpec
from modules.shared.src.taxonomy_paths_constant import PROVENANCE_MARKER
from modules.installer.src.utility_adapter_base import AdapterBase, ROOT

SRC_REL = "vendor/fetch-mcp"
APP_DIR = data_home() / "fetch-mcp"

# First argument meaning "CLI mode" -> run dist/cli.js, otherwise MCP.
CLI_ARGS = {"html", "markdown", "readable", "txt", "json", "youtube", "--help", "-h", "--version", "-v"}

IGNORES = [
    "node_modules", ".git", "__pycache__", "target", "*.egg-info",
    ".venv", "venv", "*.tsbuildinfo",
]


class FetchAdapter(AdapterBase):
    """Install vendor/fetch-mcp (bun) into XDG data, build, write CLI/MCP dispatch launcher."""

    def satisfied(self, spec, root: Path | None = None) -> bool:
        return (bin_home() / "fetch-mcp").exists()

    def install(self, spec: ToolSpec, root: Path = ROOT, *, daemons=None) -> list[Path]:
        root = root or ROOT
        src = self.ensure_source(root, SRC_REL)
        if not (src / "package.json").exists():
            raise FileNotFoundError(f"fetch-mcp source not found (submodule not initialized): {src}")
        if not self.require("bun", "fetch-mcp requires bun (curl -fsSL https://bun.sh/install | bash)"):
            raise FileNotFoundError("bun is required (curl -fsSL https://bun.sh/install | bash).")

        print(f">>> Installing fetch-mcp into {APP_DIR}...")
        self.copy_app(src, APP_DIR, IGNORES)

        self.run(["bun", "install", "--frozen-lockfile"], APP_DIR)
        self.run(["bun", "run", "build"], APP_DIR)

        index_js = APP_DIR / "dist/index.js"
        cli_js = APP_DIR / "dist/cli.js"
        if not index_js.exists() or not cli_js.exists():
            raise FileNotFoundError(f"build output incomplete ({index_js}, {cli_js})")

        ensure_bin_home()
        content = (
            "#!/usr/bin/env python3\n"
            f"# {PROVENANCE_MARKER}\n"
            "import os, sys\n"
            f'index_js = r"{index_js}"\n'
            f'cli_js = r"{cli_js}"\n'
            "cli = " + repr(sorted(CLI_ARGS)) + "\n"
            "script = cli_js if (len(sys.argv) > 1 and sys.argv[1] in cli) else index_js\n"
            'env = os.environ.copy()\n'
            'os.execvpe("node", ["node", script, *sys.argv[1:]], env)\n'
        )
        artifacts = []
        for name in ("fetch-mcp", "mcp-fetch"):
            launcher = bin_home() / name
            launcher.write_text(content, encoding="utf-8")
            launcher.chmod(0o755)
            artifacts.append(launcher)
            print(f"  -> {launcher}")

        warn_if_bin_not_on_path()
        print(">>> Successfully installed fetch-mcp")
        return artifacts
