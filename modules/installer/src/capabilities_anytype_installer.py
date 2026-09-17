"""Anytype installer (bun, merged) — port of tools/install/install_anytype_mcp.py.

Merged installer: installs BOTH components in one command.
1. anytype-mcp     — @anyproto/anytype-mcp (TypeScript, bun) MCP server.
   Lockfile bun.lock -> `bun install`; build `bun run build` (tsc + build-cli.js,
   entry bin/cli.mjs, NOT dist/cli.mjs). Runtime installed in-place at
   $XDG_DATA_HOME/anytype-mcp so bun node_modules are included.
2. anytype-daemon  — headless Anytype container daemon (podman + systemd user unit).
   Launcher `anytype-daemon` + alias `ad` -> tools/daemons/anytype_daemon.py;
   launcher copy placed in internal-bin (same pattern as 9router).
"""
from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

from modules.shared.src.paths.utility_paths import repo_root
from modules.shared.src.tool.taxonomy_tool_vo import InstallResult, ToolSpec
from modules.shared.src.tool.contract_tool_protocol import IToolInstaller
from modules.shared.src.xdg.utility_xdg_atomic_io import (
    ensure_bin_home,
    ensure_path,
    warn_if_bin_not_on_path,
)
from modules.shared.src.xdg.utility_xdg_paths import bin_home, data_home


# ---------------------------------------------------------------------------
# anytype-mcp
# ---------------------------------------------------------------------------
MCP_SRC_REL = "vendor/anytype-mcp"
MCP_APP_REL = "anytype-mcp"
MCP_ENTRY = "bin/cli.mjs"

MCP_IGNORES = shutil.ignore_patterns(
    "node_modules", ".git", "__pycache__", "dist", "target", "*.egg-info",
    ".venv", "venv", "*.tsbuildinfo",
)

# ---------------------------------------------------------------------------
# anytype-daemon
# ---------------------------------------------------------------------------
DAEMON_TOOL_DIR_REL = "tools/daemons"
DAEMON_DATA_REL = "anytype-daemon"
INTERNAL_BIN = "internal-bin"


class AnytypeInstaller(IToolInstaller):
    """Install both anytype-mcp (bun) and anytype-daemon (container + systemd)."""

    def __init__(self, root=None) -> None:
        self._root = root or repo_root()

    # -- Block 1: anytype-mcp ----------------------------------------------------
    def _install_mcp(self, spec: ToolSpec) -> InstallResult:
        root = self._root
        src = root / MCP_SRC_REL
        if not (src / "package.json").exists():
            return InstallResult(False, spec.id, "anytype-mcp source not found (submodule not initialized)")
        if shutil.which("bun") is None:
            return InstallResult(False, spec.id, "bun is required (curl -fsSL https://bun.sh/install | bash)")

        app_dir = data_home() / MCP_APP_REL
        print(f">>> Installing anytype-mcp into {app_dir}...")
        if app_dir.exists():
            shutil.rmtree(app_dir)
        shutil.copytree(src, app_dir, ignore=MCP_IGNORES)

        subprocess.run(["bun", "install", "--frozen-lockfile"], cwd=app_dir, check=True)
        subprocess.run(["bun", "run", "build"], cwd=app_dir, check=True)

        entry = app_dir / MCP_ENTRY
        if not entry.exists():
            return InstallResult(False, spec.id, f"entry not found {entry}")

        ensure_bin_home()
        launcher = bin_home() / "anytype-mcp"
        launcher.write_text(
            "#!/usr/bin/env python3\n"
            "import os, sys\n"
            f'entry = r"{entry}"\n'
            'os.execvpe("node", ["node", entry, *sys.argv[1:]], os.environ.copy())\n',
            encoding="utf-8",
        )
        launcher.chmod(0o755)
        print(f"  -> {launcher}")
        warn_if_bin_not_on_path()
        print(">>> Successfully installed anytype-mcp")
        return InstallResult(True, spec.id, "anytype-mcp installed")

    # -- Block 2: anytype-daemon ---------------------------------------------------
    def _install_daemon(self, spec: ToolSpec) -> InstallResult:
        root = self._root
        if shutil.which("podman") is None and shutil.which("docker") is None:
            print("Warning: podman/docker not found; anytype-daemon skipped.", file=sys.stderr)
            print("  Install podman then re-run 'aa tool install anytype'.", file=sys.stderr)
            return InstallResult(True, spec.id, "anytype-daemon skipped (podman/docker not found)")

        ensure_bin_home()
        ensure_path()
        data_dir = data_home() / DAEMON_DATA_REL
        # Create volume-mount folders first so the systemd unit can start (24/7)
        for d in ("data", "dot-anytype", "config", "share"):
            (data_dir / d).mkdir(parents=True, exist_ok=True)

        daemon_py = root / DAEMON_TOOL_DIR_REL / "anytype_daemon.py"
        print(">>> Setting up anytype-daemon (container + systemd user service)...")
        if daemon_py.exists():
            subprocess.run([sys.executable, str(daemon_py), "service-install"], check=False)

        def _write_launcher(path: Path) -> None:
            path.write_text(
                "#!/usr/bin/env python3\n"
                "import os, sys\n"
                "from pathlib import Path\n"
                f'root = Path(os.environ.get("AGENTS_ARWAKY_ROOT", {repr(str(root))}))\n'
                'daemon = root / "tools/daemons/anytype_daemon.py"\n'
                'os.execvpe("python3", ["python3", str(daemon), *sys.argv[1:]], os.environ.copy())\n',
                encoding="utf-8",
            )
            path.chmod(0o755)

        launcher = bin_home() / "anytype-daemon"
        _write_launcher(launcher)
        alias = bin_home() / "ad"
        alias.unlink(missing_ok=True)
        alias.symlink_to(launcher)

        internal_bin = data_dir / INTERNAL_BIN
        internal_bin.mkdir(parents=True, exist_ok=True)
        _write_launcher(internal_bin / "anytype-daemon")

        print(f">>> Successfully installed anytype-daemon -> {launcher} (alias ad)")
        return InstallResult(True, spec.id, "anytype-daemon installed")

    # -- Block 3: install both -------------------------------------------------------
    def install(self, spec: ToolSpec) -> InstallResult:
        root = self._root
        mcp_ok = (bin_home() / "anytype-mcp").exists()
        daemon_ok = (bin_home() / "anytype-daemon").exists()
        if mcp_ok and daemon_ok:
            return InstallResult(True, spec.id, "anytype is already installed")

        mcp_result = self._install_mcp(spec)
        if not mcp_result.success:
            return mcp_result
        return self._install_daemon(spec)
