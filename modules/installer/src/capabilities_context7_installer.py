"""Context7 installer (pnpm workspace) — verbatim port of tools/install/install_context7.py.

@upstash/context7 is a pnpm workspace (MCP server + CLI). pnpm blocks
postinstall deps by default, so the copied pnpm-workspace.yaml is patched with
`dangerouslyAllowAllBuilds: true`. Runtime is installed in-place to
$XDG_DATA_HOME/context7; launchers point at packages/{mcp,cli}/dist/index.js.
"""
from __future__ import annotations

import shutil
import subprocess
import sys

from modules.shared.src.utility_paths import repo_root
from modules.shared.src.taxonomy_tool_vo import InstallResult, ToolSpec
from modules.installer.src.contract_tool_installer_protocol import IToolInstaller
from modules.shared.src.taxonomy_xdg_atomic_io import (
    atomic_write_text,
    ensure_bin_home,
    warn_if_bin_not_on_path,
)
from modules.shared.src.taxonomy_xdg_paths import bin_home, data_home

ROOT = repo_root()

SRC = ROOT / "vendor/context7"
APP_DIR = data_home() / "context7"
# Vendor artifacts that must not be included: stale node_modules (may contain
# broken symlinks), git, old build output, etc.
IGNORES = shutil.ignore_patterns(
    "node_modules", ".git", ".old_modules*", "__pycache__", "mcpb",
    "dist", "target", "*.egg-info", ".venv", "venv", ".next", ".turbo",
)

LAUNCHERS = {
    "context7-mcp": "packages/mcp/dist/index.js",
    "ctx7": "packages/cli/dist/index.js",
}


# ─── Block 1: Class Definition & Constructor ──────────────
class Context7Installer(IToolInstaller):
    """Install vendor/context7 (pnpm workspace) into XDG data, build, write launchers."""

    def __init__(self, root=None) -> None:
        self._root = root or ROOT

    # ─── Block 2: Protocol ABC Method Implementation ──────────

    def install(self, spec: ToolSpec) -> InstallResult:
        rc = _install_context7()
        return InstallResult(
            rc == 0,
            spec.id,
            "context7 installed" if rc == 0 else "context7 install failed",
        )

    # ─── Block 3: Dunder Methods, Factories & Helpers ───────
    def __repr__(self) -> str:
        return f"{self.__class__.__name__}()"
def run(cmd, cwd=None):
    subprocess.run(cmd, cwd=cwd, check=True)


def is_installed() -> bool:
    """Check if context7 is already installed (binary exists)."""
    return (bin_home() / "context7-mcp").exists()


def _install_context7() -> int:
    if is_installed():
        print(">>> context7 is already installed. Use 'aa update context7' to reinstall.")
        return 0

    if not (SRC / "pnpm-workspace.yaml").exists():
        print("Error: context7 source not found (submodule not initialized).", file=sys.stderr)
        return 1
    if not shutil.which("pnpm"):
        print("Error: pnpm is required (context7 is a pnpm workspace).", file=sys.stderr)
        return 1

    print(f">>> Installing context7 (pnpm workspace) into {APP_DIR}...")
    if APP_DIR.exists():
        shutil.rmtree(APP_DIR)
    shutil.copytree(SRC, APP_DIR, ignore=IGNORES)

    # pnpm blocks postinstall deps by default -> allow in this copy only
    ws = APP_DIR / "pnpm-workspace.yaml"
    if "dangerouslyAllowAllBuilds" not in ws.read_text(encoding="utf-8", errors="replace"):
        with ws.open("a", encoding="utf-8") as f:
            f.write("\ndangerouslyAllowAllBuilds: true\n")

    run(["pnpm", "install", "--frozen-lockfile"], APP_DIR)
    run(["pnpm", "run", "build"], APP_DIR)

    ensure_bin_home()
    for name, entry in LAUNCHERS.items():
        target = APP_DIR / entry
        if not target.exists():
            print(f"  Warning: entry not found {target}", file=sys.stderr)
            continue
        launcher = bin_home() / name
        atomic_write_text(launcher,
            "#!/usr/bin/env python3\n"
            "import os, sys\n"
            f'entry = r"{target}"\n'
            'os.execvpe("node", ["node", entry, *sys.argv[1:]], os.environ.copy())\n')
        print(f"  -> {launcher}")

    warn_if_bin_not_on_path()
    print(">>> Successfully installed context7")
    return 0



