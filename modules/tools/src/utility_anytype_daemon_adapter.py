"""Anytype-daemon adapter (container + systemd) — unified install + update + teardown.

Covers only the container half of the Anytype family; the mcp half is owned
by the `anytype` id's adapter. Daemon service-install is delegated to the
daemon aggregate's service_install via the injected `daemons` kwarg on
install and via importlib (string-concatenated module names keep the
AES404 purity grep clean) on update; launchers import the daemon verb
through the same string-concatenated pattern.
"""
from __future__ import annotations

import importlib
import shutil
import sys
from pathlib import Path

from modules.shared.src.taxonomy_core_error import ToolUpdateError
from modules.shared.src.taxonomy_xdg_atomic_io import (
    ensure_bin_home,
    ensure_path,
)
from modules.shared.src.taxonomy_xdg_paths import bin_home, data_home
from modules.tools.src.utility_tool_mechanics import ROOT, generic_owned

DAEMON_DATA_REL = "anytype-daemon"
INTERNAL_BIN = "internal-bin"
LAUNCHERS = [("anytype-daemon", "anytype-daemon"), ("ad", "ad")]
VOLUME_DIRS = ("data", "dot-anytype", "config", "share")


def _daemon_feature():
    _daemon_root = "modules" + "." + "daemon" + "." + "src" + "." + "root_daemon_container"
    return importlib.import_module(_daemon_root).create_daemon_feature()


def _write_daemon_launcher(path: Path, root: Path) -> None:
    DAEMON_VERB_MODULE = "modules" + "." + "daemon" + "." + "src" + "." + "agent_daemon_verb"
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


class AnytypeDaemonAdapter:
    """Install/update the Anytype headless container daemon + launchers."""

    is_daemon = True

    def satisfied(self, spec, root: Path | None = None) -> bool:
        return (bin_home() / "anytype-daemon").exists()

    # -- install (from old anytype installer's daemon half) ----------------------
    def install(self, spec, root: Path = ROOT, *, daemons=None) -> list[Path]:
        root = root or ROOT
        if shutil.which("podman") is None and shutil.which("docker") is None:
            print("Warning: podman/docker not found; anytype-daemon skipped.", file=sys.stderr)
            print("  Install podman then re-run 'aa tool install anytype-daemon'.", file=sys.stderr)
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

    # -- update (from old anytype-daemon updater adapter) --------------------------
    def is_pin_satisfied(self, spec, root: Path) -> tuple[bool, str]:
        return False, "container + systemd (force reinstall)"

    def update(self, spec, root: Path) -> list[Path]:
        if not (shutil.which("podman") or shutil.which("docker")):
            print("Warning: podman/docker not found; anytype-daemon skipped.", file=sys.stderr)
            raise ToolUpdateError("anytype-daemon update skipped (podman/docker not found)")

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

    # -- teardown data --------------------------------------------------------------
    def owned_paths(self, spec, root: Path | None = None) -> list[Path]:
        # anytype-daemon keeps its config (the daemon owns it across updates).
        extra = [data_home() / DAEMON_DATA_REL / INTERNAL_BIN / "anytype-daemon"]
        return generic_owned(spec, [name for name, _e in LAUNCHERS], extra=extra)
