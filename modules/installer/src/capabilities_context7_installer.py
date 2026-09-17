"""Context7 installer (pnpm workspace) — port of tools/install/install_context7.py.

@upstash/context7 is a pnpm workspace (MCP server + CLI). pnpm blocks
postinstall deps by default, so the copied pnpm-workspace.yaml is patched with
`dangerouslyAllowAllBuilds: true`. Runtime is installed in-place to
$XDG_DATA_HOME/context7; launchers point at packages/{mcp,cli}/dist/index.js.
"""
from __future__ import annotations

import shutil
import subprocess

from modules.shared.src.paths.utility_paths import repo_root
from modules.shared.src.tool.taxonomy_tool_vo import InstallResult, ToolSpec
from modules.shared.src.tool.contract_tool_protocol import IToolInstaller
from modules.shared.src.xdg.utility_xdg_atomic_io import (
    atomic_write_text,
    ensure_bin_home,
    warn_if_bin_not_on_path,
)
from modules.shared.src.xdg.utility_xdg_paths import bin_home, data_home


IGNORES = shutil.ignore_patterns(
    "node_modules", ".git", ".old_modules*", "__pycache__", "mcpb",
    "dist", "target", "*.egg-info", ".venv", "venv", ".next", ".turbo",
)

LAUNCHERS = {
    "context7-mcp": "packages/mcp/dist/index.js",
    "ctx7": "packages/cli/dist/index.js",
}


class Context7Installer(IToolInstaller):
    """Install vendor/context7 (pnpm workspace) into XDG data, build, write launchers."""

    def __init__(self, root=None) -> None:
        self._root = root or repo_root()

    def install(self, spec: ToolSpec) -> InstallResult:
        root = self._root
        if (bin_home() / "context7-mcp").exists():
            return InstallResult(True, spec.id, "context7 is already installed")

        src = root / "vendor/context7"
        if not (src / "pnpm-workspace.yaml").exists():
            return InstallResult(False, spec.id, "context7 source not found (submodule not initialized)")
        if shutil.which("pnpm") is None:
            return InstallResult(False, spec.id, "pnpm is required (context7 is a pnpm workspace)")

        app_dir = data_home() / "context7"
        print(f">>> Installing context7 (pnpm workspace) into {app_dir}...")
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
            return InstallResult(False, spec.id, f"pnpm build failed: {exc}")

        ensure_bin_home()
        for name, entry in LAUNCHERS.items():
            target = app_dir / entry
            if not target.exists():
                print(f"  Warning: entry not found {target}", file=__import__("sys").stderr)
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
        return InstallResult(True, spec.id, "context7 installed")
