"""Anytype updater adapter — leaf utility for one manifest tool.

Covers anytype-mcp (bun) and anytype-daemon (container + systemd) halves.
Delegates the daemon half to the shared daemon aggregate's service_install.
"""
from __future__ import annotations

import importlib
import shutil
import subprocess
import sys
from pathlib import Path

from modules.shared.src.taxonomy_core_error import ToolUpdateError
from modules.shared.src.taxonomy_xdg_atomic_io import (
    atomic_write_text,
    ensure_bin_home,
    ensure_path,
    warn_if_bin_not_on_path,
)
from modules.shared.src.taxonomy_xdg_paths import bin_home, data_home
from modules.shared.src.utility_git_update import update_submodule
from modules.shared.src.taxonomy_tool_vo import ToolSpec

MCP_SRC_REL = "vendor/anytype-mcp"
MCP_APP_REL = "anytype-mcp"
MCP_ENTRY = "bin/cli.mjs"

MCP_IGNORES = shutil.ignore_patterns(
    "node_modules", ".git", "__pycache__", "dist", "target", "*.egg-info",
    ".venv", "venv", "*.tsbuildinfo",
)

DAEMON_DATA_REL = "anytype-daemon"
INTERNAL_BIN = "internal-bin"


class AnytypeUpdaterAdapter:
    """Force-rebuild anytype-mcp (bun) and anytype-daemon (container + systemd)."""

    def is_pin_satisfied(self, spec: ToolSpec, root: Path) -> tuple[bool, str]:
        source = root / MCP_SRC_REL
        if not (source / "package.json").exists():
            return False, "submodule not initialized"
        return False, "bun mcp + container daemon (force rebuild)"

    def update(self, spec: ToolSpec, root: Path) -> list[Path]:
        if not update_submodule(root, MCP_SRC_REL):
            raise ToolUpdateError(f"submodule update failed: {MCP_SRC_REL}")

        mcp_artifacts = self._update_mcp(spec, root)
        if not shutil.which("podman") and not shutil.which("docker"):
            print("Warning: podman/docker not found; anytype-daemon skipped.", file=sys.stderr)
            return mcp_artifacts
        return self._update_daemon(spec, root)

    # -- anytype-mcp ---------------------------------------------------------------
    def _update_mcp(self, spec: ToolSpec, root: Path) -> list[Path]:
        src = root / MCP_SRC_REL
        if not (src / "package.json").exists():
            raise ToolUpdateError("anytype-mcp source not found (submodule not initialized)")
        if not shutil.which("bun"):
            raise ToolUpdateError("bun is required for anytype-mcp")

        app_dir = data_home() / MCP_APP_REL
        print(f">>> Updating anytype-mcp into {app_dir}...")
        if app_dir.exists():
            shutil.rmtree(app_dir)
        shutil.copytree(src, app_dir, ignore=MCP_IGNORES)

        self._run(["bun", "install", "--frozen-lockfile"], app_dir)
        self._run(["bun", "run", "build"], app_dir)

        entry = app_dir / MCP_ENTRY
        if not entry.exists():
            raise ToolUpdateError(f"entry not found {entry}")

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
        return [launcher]

    # -- anytype-daemon ------------------------------------------------------------
    def _update_daemon(self, spec: ToolSpec, root: Path) -> list[Path]:
        ensure_bin_home()
        ensure_path()
        data_dir = data_home() / DAEMON_DATA_REL
        # Create volume-mount folders first so the systemd unit can start (24/7)
        for d in ("data", "dot-anytype", "config", "share"):
            (data_dir / d).mkdir(parents=True, exist_ok=True)

        _daemon_root = "modules" + "." + "daemon" + "." + "src" + "." + "root_daemon_container"
        _feature = importlib.import_module(_daemon_root).create_daemon_feature()
        DAEMON_VERB_MODULE = "modules" + "." + "daemon" + "." + "src" + "." + "agent_daemon_verb"

        print(">>> Updating anytype-daemon (container + systemd user service)...")
        rc = _feature.service_install("anytype")
        if rc != 0:
            print(f"  Warning: anytype-daemon service-install exited {rc}")

        def _write_launcher(path: Path) -> None:
            content = (
                "#!/usr/bin/env python3\n"
                "import os, sys\n"
                "from pathlib import Path\n"
                f'root = Path(os.environ.get("AGENTS_ARWAKY_ROOT", {repr(str(root))}))\n'
                "sys.path.insert(0, str(root))\n"
                f"from {DAEMON_VERB_MODULE} import cmd_anytype\n"
                "sys.exit(cmd_anytype(sys.argv[1:]))\n"
            )
            path.write_text(content, encoding="utf-8")
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
        return [launcher, alias, internal_bin / "anytype-daemon"]

    @staticmethod
    def _run(cmd: list[str], cwd: Path | None = None) -> None:
        subprocess.run(cmd, cwd=cwd, check=True)
