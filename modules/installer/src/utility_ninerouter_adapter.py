"""9Router adapter (hybrid daemon + launcher) — port of tools/install/install_ninerouter.py.

9Router is a Podman/daemon service, not a compiled binary. The adapter:
- registers the systemd user unit (modules/daemon/deploy/ninerouter.service) via the
  daemon module's PodmanDaemonManager.service_install()
- writes a python3 launcher into ~/.local/bin/9router that imports the
  9Router daemon verb from the daemon feature with AGENTS_ARWAKY_ROOT baked in
- mirrors the launcher into $XDG_DATA_HOME/9router/internal-bin/ so the
  daemon container can find it (same pattern as anytype-daemon).

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
)
from modules.shared.src.taxonomy_xdg_paths import bin_home, data_home
from modules.installer.src.utility_adapter_base import AdapterBase, ROOT

DATA_DIR_NAME = "9router"
INTERNAL_BIN = "internal-bin"


class NinerouterAdapter(AdapterBase):
    """Set up the 9Router hybrid daemon + launcher (no compile step)."""

    def satisfied(self, spec, root: Path | None = None) -> bool:
        return (bin_home() / "9router").exists()

    def install(self, spec, root: Path = ROOT, *, daemons=None) -> list[Path]:
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

        from modules.shared.src.taxonomy_paths_constant import PROVENANCE_MARKER as _PROV
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
        launcher = bin_home() / "9router"
        atomic_write_text(launcher, launcher_content)

        internal_bin = data_dir / INTERNAL_BIN
        internal_bin.mkdir(parents=True, exist_ok=True)
        shutil.copy2(launcher, internal_bin / "9router")
        (internal_bin / "9router").chmod(0o755)
        print(f">>> Successfully installed 9Router -> {launcher}")
        return [launcher]
