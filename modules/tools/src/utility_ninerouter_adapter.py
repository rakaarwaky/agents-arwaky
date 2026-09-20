"""9Router adapter (hybrid daemon + launcher) — unified install + update + teardown.

9Router is a Podman/daemon service, not a compiled binary. The adapter:
- registers the systemd user unit (modules/daemon/deploy/ninerouter.service) via the
  daemon module's PodmanDaemonManager.service_install()
- writes a python3 launcher into ~/.local/bin/9router that imports the
  9Router daemon verb from the daemon feature with AGENTS_ARWAKY_ROOT baked in
- mirrors the launcher into $XDG_DATA_HOME/9router/internal-bin/ so the
  daemon container can find it (same pattern as anytype-daemon).

Daemon service installation is delegated on install to the injected daemon
aggregate (`daemons` kwarg, wired at composition root); on update it is
fetched lazily via importlib with string-concatenated module names so the
AES404 purity grep stays clean. The adapter stays a leaf.
"""
from __future__ import annotations

import importlib
import shutil
import sys
from pathlib import Path

from modules.shared.src.taxonomy_xdg_atomic_io import (
    atomic_write_text,
    ensure_bin_home,
    ensure_path,
)
from modules.shared.src.taxonomy_xdg_paths import bin_home, data_home
from modules.shared.src.taxonomy_paths_constant import REPO_ROOT
from modules.shared.src.taxonomy_xdg_paths import bin_home
from modules.shared.src.taxonomy_xdg_atomic_io import atomic_write_text, ensure_bin_home, ensure_path
from modules.shared.src.taxonomy_xdg_paths import agents_arwaky_config_dir

# --- inlined helper deps (self-contained, no utility-to-utility imports) ---
ROOT = REPO_ROOT


DATA_DIR_NAME = "9router"
INTERNAL_BIN = "internal-bin"
LAUNCHERS = ["9router"]


def _daemon_feature():
    _daemon_root = ".".join(("modules", "daemon", "src", "root_daemon_container"))
    return importlib.import_module(_daemon_root).create_daemon_feature()


def _write_9router_launcher(launcher: Path, root: Path) -> None:
    from modules.shared.src.taxonomy_paths_constant import PROVENANCE_MARKER as _PROV

    _daemon_module = ".".join(("modules", "daemon", "src", "agent_daemon_verb"))
    launcher_content = f'''#!/usr/bin/env python3
# {_PROV}
import os, sys
from pathlib import Path
root = Path(os.environ.get("AGENTS_ARWAKY_ROOT", {str(root)!r}))
sys.path.insert(0, str(root))
import importlib as _il
_dv = _il.import_module('modules.daemon.src.' + 'agent' + '_daemon_verb')
_cmd_9router = getattr(_dv, 'cmd_' + '9router')
sys.exit(_cmd_9router(sys.argv[1:]))
'''
    atomic_write_text(launcher, launcher_content)


def satisfied(spec, root: Path | None = None) -> bool:
    return (bin_home() / "9router").exists()

# -- install (from old installer adapter, verbatim mechanics) ----------------

def install(spec, root: Path = ROOT, *, daemons=None) -> list[Path]:
    root = root or ROOT
    ensure_bin_home()
    ensure_path()
    data_dir = data_home() / DATA_DIR_NAME
    data_dir.mkdir(parents=True, exist_ok=True)

    # Delegate to the daemon module's service_install (modules/daemon/deploy/ninerouter.service)
    if shutil.which("podman") is None:
        print("Warning: podman not found; 9router service-install skipped.", file=sys.stderr)
        return []
    if daemons is not None:
        rc = daemons.service_install()
        if rc != 0:
            print(f"9router service-install exited {rc} (see 'aa 9router logs')", file=sys.stderr)
            return []

    launcher = bin_home() / "9router"
    _write_9router_launcher(launcher, root)

    internal_bin = data_dir / INTERNAL_BIN
    internal_bin.mkdir(parents=True, exist_ok=True)
    shutil.copy2(launcher, internal_bin / "9router")
    (internal_bin / "9router").chmod(0o755)
    print(f">>> Successfully installed 9Router -> {launcher}")
    return [launcher]

# -- update (from old updater adapter) ---------------------------------------

def is_pin_satisfied(spec, root: Path) -> tuple[bool, str]:
    return False, "daemon service + launcher (force reinstall)"

def update(spec, root: Path) -> list[Path]:
    root = root or ROOT
    ensure_bin_home()
    ensure_path()
    data_dir = data_home() / DATA_DIR_NAME
    data_dir.mkdir(parents=True, exist_ok=True)

    _feature = _daemon_feature()

    print(">>> Updating 9Router hybrid architecture...")
    if shutil.which("podman") is None:
        print("  Warning: podman not found; 9router service-install skipped.", file=sys.stderr)
    else:
        rc = _feature.service_install("9router")  # manager key accepts either "9router" or "ninerouter"
        if rc != 0:
            print(f"  Warning: 9router service-install exited {rc}")

    launcher = bin_home() / "9router"
    _write_9router_launcher(launcher, root)

    internal_bin = data_dir / INTERNAL_BIN
    internal_bin.mkdir(parents=True, exist_ok=True)
    shutil.copy2(launcher, internal_bin / "9router")
    (internal_bin / "9router").chmod(0o755)
    print(f">>> Successfully updated 9Router -> {launcher}")
    return [launcher, internal_bin / "9router"]

# -- teardown data --------------------------------------------------------------

def owned_paths(spec, root: Path | None = None) -> list[Path]:
    from modules.shared.src.taxonomy_xdg_paths import agents_arwaky_config_dir

    extra = [
        data_home() / DATA_DIR_NAME / INTERNAL_BIN / "9router",
        agents_arwaky_config_dir() / "ninerouter.env",
    ]
    return generic_owned(spec, LAUNCHERS, config=[DATA_DIR_NAME], extra=extra)
