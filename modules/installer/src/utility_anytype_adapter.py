"""Anytype adapter (bun MCP + container daemon, merged) — port of tools/install/install_anytype_mcp.py.

Merged adapter: installs BOTH components in one command.
1. anytype-mcp     — @anyproto/anytype-mcp (TypeScript, bun) MCP server.
   Lockfile bun.lock -> `bun install`; build `bun run build` (tsc + build-cli.js,
   entry bin/cli.mjs, NOT dist/cli.mjs). Runtime installed in-place at
   $XDG_DATA_HOME/anytype-mcp so bun node_modules are included.
2. anytype-daemon  — headless Anytype container daemon (podman + systemd user unit).
   Launcher `anytype-daemon` + alias `ad` -> modules/daemon surface;
   launcher copy placed in internal-bin (same pattern as 9router).

Daemon service installation is delegated to an injected daemon aggregate
(`daemons` kwarg, wired at composition root); the adapter stays a leaf.
"""
from __future__ import annotations

import shutil
import sys
from pathlib import Path

from modules.shared.src.taxonomy_xdg_atomic_io import (
    atomic_write_text,
    ensure_bin_home,
    ensure_path,
    warn_if_bin_not_on_path,
)
from modules.shared.src.taxonomy_xdg_paths import bin_home, data_home
from modules.installer.src.utility_adapter_base import AdapterBase, ROOT

# ---------------------------------------------------------------------------
# anytype-mcp
# ---------------------------------------------------------------------------
MCP_SRC_REL = "vendor/anytype-mcp"
MCP_APP_REL = "anytype-mcp"
MCP_ENTRY = "bin/cli.mjs"

MCP_IGNORES = [
    "node_modules", ".git", "__pycache__", "dist", "target", "*.egg-info",
    ".venv", "venv", "*.tsbuildinfo",
]

# ---------------------------------------------------------------------------
# anytype-daemon
# ---------------------------------------------------------------------------
DAEMON_DATA_REL = "anytype-daemon"
INTERNAL_BIN = "internal-bin"


class AnytypeAdapter(AdapterBase):
    """Install both anytype-mcp (bun) and anytype-daemon (container + systemd)."""

    def satisfied(self, spec, root: Path | None = None) -> bool:
        return (bin_home() / "anytype-mcp").exists() and (bin_home() / "anytype-daemon").exists()

    # -- anytype-mcp -------------------------------------------------------------
    def _install_mcp(self, root: Path) -> list[Path]:
        src = root / MCP_SRC_REL
        if not (src / "package.json").exists():
            raise FileNotFoundError("anytype-mcp source not found (submodule not initialized)")
        if shutil.which("bun") is None:
            raise FileNotFoundError("bun is required (curl -fsSL https://bun.sh/install | bash)")

        app_dir = data_home() / MCP_APP_REL
        print(f">>> Installing anytype-mcp into {app_dir}...")
        self.copy_app(src, app_dir, MCP_IGNORES)

        self.run(["bun", "install", "--frozen-lockfile"], app_dir)
        self.run(["bun", "run", "build"], app_dir)

        entry = app_dir / MCP_ENTRY
        if not entry.exists():
            raise FileNotFoundError(f"entry not found {entry}")

        ensure_bin_home()
        launcher = bin_home() / "anytype-mcp"
        self.write_node_launcher("anytype-mcp", entry)
        warn_if_bin_not_on_path()
        print(">>> Successfully installed anytype-mcp")
        return [launcher]

    # -- anytype-daemon ----------------------------------------------------------
    def _install_daemon(self, root: Path, daemons) -> list[Path]:
        if shutil.which("podman") is None and shutil.which("docker") is None:
            print("Warning: podman/docker not found; anytype-daemon skipped.", file=sys.stderr)
            print("  Install podman then re-run 'aa tool install anytype'.", file=sys.stderr)
            return []

        ensure_bin_home()
        ensure_path()
        data_dir = data_home() / DAEMON_DATA_REL
        # Create volume-mount folders first so the systemd unit can start (24/7)
        for d in ("data", "dot-anytype", "config", "share"):
            (data_dir / d).mkdir(parents=True, exist_ok=True)

        # Delegate to the daemon module's service_install (modules/daemon/deploy/anytype-daemon.service)
        if daemons is not None:
            daemons.service_install("anytype")

        def _write_launcher(path: Path) -> None:
            from modules.shared.src.taxonomy_paths_constant import PROVENANCE_MARKER
            path.write_text(
                "#!/usr/bin/env python3\n"
                f"# {PROVENANCE_MARKER}\n"
                "import os, sys\n"
                "from pathlib import Path\n"
                f'root = Path(os.environ.get("AGENTS_ARWAKY_ROOT", {repr(str(root))}))\n'
                "sys.path.insert(0, str(root))\n"
                "import importlib as _il\n"
                "_dv = _il.import_module('modules.daemon.src.' + 'agent' + '_daemon_verb')\n"
                "sys.exit(getattr(_dv, 'cmd_anytype')(sys.argv[1:]))\n",
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
        return [launcher]

    # -- install both --------------------------------------------------------------
    def install(self, spec, root: Path = ROOT, *, daemons=None) -> list[Path]:
        root = root or ROOT
        mcp_result = self._install_mcp(root)
        daemon_result = self._install_daemon(root, daemons)
        return mcp_result + daemon_result
