"""Fetch-mcp adapter (bun) — unified install + update + teardown.

zcaceres/fetch-mcp is a TypeScript project built with bun. Output:
  - dist/index.js -> MCP server (fetch-mcp, mcp-fetch)
  - dist/cli.js   -> CLI mode (html/markdown/readable/txt/json/youtube/...)
The launcher dispatches CLI vs MCP based on the first argument.
"""
from __future__ import annotations

from pathlib import Path

from modules.shared.src.taxonomy_core_error import ToolUpdateError
from modules.shared.src.taxonomy_xdg_atomic_io import (
    ensure_bin_home,
    warn_if_bin_not_on_path,
)
from modules.shared.src.taxonomy_xdg_paths import bin_home, data_home
from modules.shared.src.taxonomy_paths_constant import PROVENANCE_MARKER
from modules.tools.src.utility_tool_mechanics import ROOT, copy_app, ensure_source, generic_owned, require, run

SRC_REL = "vendor/fetch-mcp"
APP_DIR = data_home() / "fetch-mcp"

# First argument meaning "CLI mode" -> run dist/cli.js, otherwise MCP.
CLI_ARGS = {"html", "markdown", "readable", "txt", "json", "youtube", "--help", "-h", "--version", "-v"}

IGNORES = [
    "node_modules", ".git", "__pycache__", "target", "*.egg-info",
    ".venv", "venv", "*.tsbuildinfo",
]


class FetchAdapter:
    """Install/update vendor/fetch-mcp (bun) into XDG data, write CLI/MCP dispatch launcher."""

    def satisfied(self, spec, root: Path | None = None) -> bool:
        return (bin_home() / "fetch-mcp").exists()

    def _write_launchers(self) -> list[Path]:
        """Write the CLI/MCP dispatch launchers (shared by install and update)."""
        index_js = APP_DIR / "dist/index.js"
        cli_js = APP_DIR / "dist/cli.js"
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
        return artifacts

    # -- install (from old installer adapter, verbatim mechanics) ----------------
    def install(self, spec, root: Path = ROOT, *, daemons=None) -> list[Path]:
        root = root or ROOT
        src = ensure_source(root, SRC_REL)
        if not (src / "package.json").exists():
            raise FileNotFoundError(f"fetch-mcp source not found (submodule not initialized): {src}")
        if not require("bun", "fetch-mcp requires bun (curl -fsSL https://bun.sh/install | bash)"):
            raise FileNotFoundError("bun is required (curl -fsSL https://bun.sh/install | bash).")

        print(f">>> Installing fetch-mcp into {APP_DIR}...")
        copy_app(src, APP_DIR, IGNORES)

        run(["bun", "install", "--frozen-lockfile"], APP_DIR)
        run(["bun", "run", "build"], APP_DIR)

        if not (APP_DIR / "dist/index.js").exists() or not (APP_DIR / "dist/cli.js").exists():
            raise FileNotFoundError(f"build output incomplete ({APP_DIR / 'dist/index.js'}, {APP_DIR / 'dist/cli.js'})")

        artifacts = self._write_launchers()
        print(">>> Successfully installed fetch-mcp")
        return artifacts

    # -- update (from old updater adapter) ---------------------------------------
    def is_pin_satisfied(self, spec, root: Path) -> tuple[bool, str]:
        source = root / SRC_REL
        if not source.exists():
            return False, "submodule not initialized"
        return False, "bun workspace (rebuild required)"

    def update(self, spec, root: Path) -> list[Path]:
        from modules.shared.src.utility_git_update import update_submodule

        source = root / SRC_REL
        if not update_submodule(root, SRC_REL):
            raise ToolUpdateError(f"submodule update failed: {SRC_REL}")
        if not (source / "package.json").exists():
            raise ToolUpdateError("fetch-mcp source not found (submodule not initialized)")
        if not require("bun", "fetch-mcp requires bun (curl -fsSL https://bun.sh/install | bash)"):
            raise ToolUpdateError("fetch-mcp requires bun (curl -fsSL https://bun.sh/install | bash)")

        print(f">>> Updating fetch-mcp into {APP_DIR}...")
        copy_app(source, APP_DIR, IGNORES)
        run(["bun", "install", "--frozen-lockfile"], APP_DIR)
        run(["bun", "run", "build"], APP_DIR)

        if not (APP_DIR / "dist/index.js").exists() or not (APP_DIR / "dist/cli.js").exists():
            raise ToolUpdateError(f"build output incomplete ({APP_DIR / 'dist/index.js'}, {APP_DIR / 'dist/cli.js'})")

        created = self._write_launchers()
        print(">>> Successfully updated fetch-mcp")
        return created

    # -- teardown data --------------------------------------------------------------
    def owned_paths(self, spec, root: Path | None = None) -> list[Path]:
        return generic_owned(spec, ["fetch-mcp", "mcp-fetch"])
