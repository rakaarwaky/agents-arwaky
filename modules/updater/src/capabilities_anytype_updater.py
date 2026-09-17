"""Anytype updater (bun mcp + container daemon, force) — port of tools/update/update_anytype_mcp.py.

Always pulls vendor/anytype-mcp, force-rebuilds the mcp runtime in place,
re-writes the anytype-mcp launcher, and force-updates the anytype-daemon
(container + systemd user service) half. The original script exec'd
`tools/daemons/anytype_daemon.py service-install` and wrote a launcher that
pointed at that script; in the AES layout the daemon logic lives in
modules/daemon, so this delegates to AnytypeDaemonManager.service_install()
and the launcher imports cmd_anytype from the daemon surface (same as the
installer).
"""
from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

from modules.shared.src.git.utility_git_update import update_submodule
from modules.shared.src.paths.utility_paths import repo_root
from modules.shared.src.tool.taxonomy_tool_vo import ToolSpec, UpdateResult
from modules.shared.src.tool.contract_tool_protocol import IToolUpdater
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
DAEMON_DATA_REL = "anytype-daemon"
INTERNAL_BIN = "internal-bin"


def _run(cmd: list[str], cwd: Path | None = None) -> None:
    subprocess.run(cmd, cwd=cwd, check=True)


def _require(tool: str, reason: str) -> bool:
    if shutil.which(tool):
        return True
    print(f"Error: {tool} not found in PATH. {reason}", file=sys.stderr)
    return False


class AnytypeUpdater(IToolUpdater):
    """Force-rebuild anytype-mcp (bun) and anytype-daemon (container + systemd)."""

    def __init__(self, root=None) -> None:
        self._root = root or repo_root()

    # -- Block 1: anytype-mcp ----------------------------------------------------
    def _update_mcp(self, spec: ToolSpec) -> UpdateResult:
        root = self._root
        src = root / MCP_SRC_REL
        if not (src / "package.json").exists():
            return UpdateResult(False, spec.id, "anytype-mcp source not found (submodule not initialized)")
        if not _require("bun", "anytype-mcp requires bun (curl -fsSL https://bun.sh/install | bash)"):
            return UpdateResult(False, spec.id, "bun is required for anytype-mcp")

        app_dir = data_home() / MCP_APP_REL
        print(f">>> Updating anytype-mcp into {app_dir}...")
        if app_dir.exists():
            shutil.rmtree(app_dir)
        shutil.copytree(src, app_dir, ignore=MCP_IGNORES)

        _run(["bun", "install", "--frozen-lockfile"], app_dir)
        _run(["bun", "run", "build"], app_dir)

        entry = app_dir / MCP_ENTRY
        if not entry.exists():
            return UpdateResult(False, spec.id, f"entry not found {entry}")

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
        print(">>> Successfully updated anytype-mcp")
        return UpdateResult(True, spec.id, "anytype-mcp updated")

    # -- Block 2: anytype-daemon ---------------------------------------------------
    def _update_daemon(self, spec: ToolSpec) -> UpdateResult:
        root = self._root
        if not (shutil.which("podman") or shutil.which("docker")):
            print("Warning: podman/docker not found; anytype-daemon skipped.", file=sys.stderr)
            return UpdateResult(True, spec.id, "anytype-daemon update skipped (podman/docker not found)")

        ensure_bin_home()
        ensure_path()
        data_dir = data_home() / DAEMON_DATA_REL
        # Create volume-mount folders first so the systemd unit can start (24/7)
        for d in ("data", "dot-anytype", "config", "share"):
            (data_dir / d).mkdir(parents=True, exist_ok=True)

        # Delegate to the daemon module's service_install (tools/deploy/anytype-daemon.service)
        from modules.daemon.src.capabilities_daemon_anytype import AnytypeDaemonManager

        print(">>> Updating anytype-daemon (container + systemd user service)...")
        rc = AnytypeDaemonManager().service_install()
        if rc != 0:
            print(f"  Warning: anytype-daemon service-install exited {rc}")

        def _write_launcher(path: Path) -> None:
            path.write_text(
                "#!/usr/bin/env python3\n"
                "import os, sys\n"
                "from pathlib import Path\n"
                f'root = Path(os.environ.get("AGENTS_ARWAKY_ROOT", {repr(str(root))}))\n'
                "sys.path.insert(0, str(root))\n"
                'from modules.daemon.src.surface_daemon_command import cmd_anytype\n'
                'sys.exit(cmd_anytype(sys.argv[1:]))\n',
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

        print(f">>> Successfully updated anytype-daemon -> {launcher} (alias ad)")
        return UpdateResult(True, spec.id, "anytype-daemon updated")

    # -- Block 3: update both -------------------------------------------------------
    def update(self, spec: ToolSpec) -> UpdateResult:
        # Pull latest from remote
        if not update_submodule(self._root, MCP_SRC_REL):
            return UpdateResult(False, spec.id, f"submodule update failed: {MCP_SRC_REL}")

        mcp_result = self._update_mcp(spec)
        if not mcp_result.success:
            return mcp_result
        return self._update_daemon(spec)
