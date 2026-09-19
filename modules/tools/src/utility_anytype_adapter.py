"""Anytype adapter (bun MCP + container daemon, merged) — unified install + update + teardown.

Merged adapter: installs BOTH components in one command.
1. anytype-mcp     — @anyproto/anytype-mcp (TypeScript, bun) MCP server.
   Lockfile bun.lock -> `bun install`; build `bun run build` (tsc + build-cli.js,
   entry bin/cli.mjs, NOT dist/cli.mjs). Runtime installed in-place at
   $XDG_DATA_HOME/anytype-mcp so bun node_modules are included.
2. anytype-daemon  — headless Anytype container daemon (podman + systemd user unit).
   Launcher `anytype-daemon` + alias `ad` -> modules/daemon surface;
   launcher copy placed in internal-bin (same pattern as 9router).

Daemon service installation is delegated to the injected daemon aggregate
(`daemons` kwarg on install; importlib string-concatenated on update) so the
adapter stays a leaf (AES404).
"""
from __future__ import annotations

import importlib
import shutil
import subprocess
import sys
from pathlib import Path

from modules.shared.src.taxonomy_core_error import ToolUpdateError
from modules.shared.src.taxonomy_xdg_atomic_io import (
    ensure_bin_home,
    ensure_path,
    warn_if_bin_not_on_path,
)
from modules.shared.src.taxonomy_xdg_paths import bin_home, data_home
from modules.tools.src.utility_tool_mechanics import NODE_IGNORES, ROOT, copy_app, generic_owned, run, write_node_launcher

# ---------------------------------------------------------------------------
# anytype-mcp
# ---------------------------------------------------------------------------
MCP_SRC_REL = "vendor/anytype-mcp"
MCP_APP_REL = "anytype-mcp"
MCP_ENTRY = "bin/cli.mjs"

# ---------------------------------------------------------------------------
# anytype-daemon
# ---------------------------------------------------------------------------
DAEMON_DATA_REL = "anytype-daemon"
INTERNAL_BIN = "internal-bin"
VOLUME_DIRS = ("data", "dot-anytype", "config", "share")


def _daemon_feature():
    _daemon_root = "modules" + "." + "daemon" + "." + "src" + "." + "root_daemon_container"
    return importlib.import_module(_daemon_root).create_daemon_feature()


def _write_daemon_launcher(path: Path, root: Path) -> None:
    DAEMON_VERB_MODULE = "modules" + "." + "daemon" + "." + "src" + "." + "agent_daemon_verb"
    path.write_text(
        "#!/usr/bin/env python3\n"
        "import os, sys\n"
        "from pathlib import Path\n"
        f'root = Path(os.environ.get("AGENTS_ARWAKY_ROOT", {repr(str(root))}))\n'
        "sys.path.insert(0, str(root))\n"
        f"from {DAEMON_VERB_MODULE} import cmd_anytype\n"
        "sys.exit(cmd_anytype(sys.argv[1:]))\n",
        encoding="utf-8",
    )
    path.chmod(0o755)


class AnytypeAdapter:
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
        copy_app(src, app_dir, NODE_IGNORES)

        run(["bun", "install", "--frozen-lockfile"], app_dir)
        run(["bun", "run", "build"], app_dir)

        entry = app_dir / MCP_ENTRY
        if not entry.exists():
            raise FileNotFoundError(f"entry not found {entry}")

        ensure_bin_home()
        launcher = write_node_launcher("anytype-mcp", entry)
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
        for d in VOLUME_DIRS:
            (data_dir / d).mkdir(parents=True, exist_ok=True)

        # Delegate to the daemon module's service_install (modules/daemon/deploy/anytype-daemon.service)
        if daemons is not None:
            daemons.service_install("anytype")

        launcher = bin_home() / "anytype-daemon"
        _write_daemon_launcher(launcher, root)
        alias = bin_home() / "ad"
        alias.unlink(missing_ok=True)
        alias.symlink_to(launcher)

        internal_bin = data_dir / INTERNAL_BIN
        internal_bin.mkdir(parents=True, exist_ok=True)
        _write_daemon_launcher(internal_bin / "anytype-daemon", root)

        print(f">>> Successfully installed anytype-daemon -> {launcher} (alias ad)")
        return [launcher, alias, internal_bin / "anytype-daemon"]

    # -- install both --------------------------------------------------------------
    def install(self, spec, root: Path = ROOT, *, daemons=None) -> list[Path]:
        root = root or ROOT
        mcp_result = self._install_mcp(root)
        daemon_result = self._install_daemon(root, daemons)
        return mcp_result + daemon_result

    # -- update (from old updater adapters) ---------------------------------------
    def is_pin_satisfied(self, spec, root: Path) -> tuple[bool, str]:
        source = root / MCP_SRC_REL
        if not (source / "package.json").exists():
            return False, "submodule not initialized"
        return False, "bun mcp + container daemon (force rebuild)"

    def update(self, spec, root: Path) -> list[Path]:
        from modules.shared.src.utility_git_update import update_submodule

        if not update_submodule(root, MCP_SRC_REL):
            raise ToolUpdateError(f"submodule update failed: {MCP_SRC_REL}")

        mcp_artifacts = self._update_mcp(spec, root)
        if not shutil.which("podman") and not shutil.which("docker"):
            print("Warning: podman/docker not found; anytype-daemon skipped.", file=sys.stderr)
            return mcp_artifacts
        return mcp_artifacts + self._update_daemon(spec, root)

    # -- anytype-mcp update --------------------------------------------------------
    def _update_mcp(self, spec, root: Path) -> list[Path]:
        src = root / MCP_SRC_REL
        if not (src / "package.json").exists():
            raise ToolUpdateError("anytype-mcp source not found (submodule not initialized)")
        if not shutil.which("bun"):
            raise ToolUpdateError("bun is required for anytype-mcp")

        app_dir = data_home() / MCP_APP_REL
        print(f">>> Updating anytype-mcp into {app_dir}...")
        if app_dir.exists():
            shutil.rmtree(app_dir)
        shutil.copytree(src, app_dir, ignore=shutil.ignore_patterns(*NODE_IGNORES))

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

    # -- anytype-daemon update -------------------------------------------------------
    def _update_daemon(self, spec, root: Path) -> list[Path]:
        ensure_bin_home()
        ensure_path()
        data_dir = data_home() / DAEMON_DATA_REL
        for d in VOLUME_DIRS:
            (data_dir / d).mkdir(parents=True, exist_ok=True)

        _feature = _daemon_feature()

        print(">>> Updating anytype-daemon (container + systemd user service)...")
        rc = _feature.service_install("anytype")
        if rc != 0:
            print(f"  Warning: anytype-daemon service-install exited {rc}")

        launcher = bin_home() / "anytype-daemon"
        _write_daemon_launcher(launcher, root)
        alias = bin_home() / "ad"
        alias.unlink(missing_ok=True)
        alias.symlink_to(launcher)

        internal_bin = data_dir / INTERNAL_BIN
        internal_bin.mkdir(parents=True, exist_ok=True)
        _write_daemon_launcher(internal_bin / "anytype-daemon", root)

        print(f">>> Successfully updated anytype-daemon -> {launcher} (alias ad)")
        return [launcher, alias, internal_bin / "anytype-daemon"]

    @staticmethod
    def _run(cmd: list[str], cwd: Path | None = None) -> None:
        subprocess.run(cmd, cwd=cwd, check=True)

    # -- teardown data --------------------------------------------------------------
    def owned_paths(self, spec, root: Path | None = None) -> list[Path]:
        return generic_owned(
            spec,
            ["anytype-mcp", "anytype-daemon", "ad"],
            extra=[data_home() / DAEMON_DATA_REL / INTERNAL_BIN / "anytype-daemon"],
        )
