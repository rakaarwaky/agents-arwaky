"""Capability — 9router tool adapter (host-native daemon + launcher).

Exports the `9router`
`AdapterUnit` merged into `TOOLS_REGISTRY` by the root container.
Shared mechanics live in `utility_tool_mechanics`.
"""
from __future__ import annotations

import importlib
import shutil
import sys
from pathlib import Path

from modules.shared.src.contract_tools_protocol import ToolsAdapterBody
from modules.shared.src.taxonomy_common_constant import PROVENANCE_MARKER
from modules.shared.src.taxonomy_common_vo import (
    agents_arwaky_config_dir,
    atomic_write_text,
    bin_home,
    data_home,
    ensure_bin_home,
    ensure_path,
)
from modules.shared.src.taxonomy_tools_constant import (
    NINEROUTER_DATA_DIR_NAME,
    NINEROUTER_INTERNAL_BIN,
    NINEROUTER_LAUNCHERS,
    ROOT_ENV_VAR,
)
from modules.shared.src.taxonomy_tools_vo import AdapterUnit
from modules.shared.src.utility_tool_mechanics import (
    make_install,
    make_owned,
    make_pin_check,
    make_satisfied,
    make_update,
)

# ─── Block 1: Class Definition & Constructor ──────────────
class NinerouterToolsAdapter(ToolsAdapterBody):
    """9router actions behind the tools adapter protocol (AES403 implementor)."""

    _display = '9router'

    def __init__(self, units: dict[str, AdapterUnit] | None = None) -> None:
        """Default to this adapter's own unit registry when *units* is omitted."""
        super().__init__(dict(ADAPTER_UNITS) if units is None else units)

# ---------------------------------------------------------------------------
# Lifecycle helpers (host-native daemon service + launcher)
# ---------------------------------------------------------------------------
def _ninerouter_daemon_feature():
    _daemon_root = "modules.daemon.src.root_daemon_container"
    return importlib.import_module(_daemon_root).create_daemon_feature()

def _ninerouter_write_launcher(launcher: Path, root: Path) -> None:
    content = (
        "#!/usr/bin/env python3\n"
        f"# {PROVENANCE_MARKER}\n"
        "import os, sys\n"
        "from pathlib import Path\n"
        f'root = Path(os.environ.get("{ROOT_ENV_VAR}", {str(root)!r}))\n'
        "sys.path.insert(0, str(root))\n"
        "import importlib as _il\n"
        "_dv = _il.import_module('modules.daemon.src.' + 'surface' + '_daemon_command')\n"
        "_cmd_9router = getattr(_dv, 'cmd_' + '9router')\n"
        "sys.exit(_cmd_9router(sys.argv[1:]))\n"
    )
    atomic_write_text(launcher, content)
    launcher.chmod(0o755)

def _ninerouter_lifecycle(action: str, root: Path, daemons) -> list[Path]:
    is_update = action == "update"
    progress_ed = "updated" if is_update else "installed"
    ensure_bin_home()
    ensure_path()
    data_dir = data_home() / NINEROUTER_DATA_DIR_NAME
    data_dir.mkdir(parents=True, exist_ok=True)

    if is_update:
        _feature = _ninerouter_daemon_feature()
        print(">>> Updating 9Router host-native service...")
        rc = _feature.install_unit("9router.service")
        if rc != 0:
            print(f"  Warning: 9router service-install exited {rc}")
    else:
        if daemons is not None:
            rc = daemons.install_unit("9router.service")
            if rc != 0:
                print(f"9router service-install exited {rc} (see 'aa 9router logs')", file=sys.stderr)
                return []

    launcher = bin_home() / "9router"
    _ninerouter_write_launcher(launcher, root)
    internal_bin = data_dir / NINEROUTER_INTERNAL_BIN
    internal_bin.mkdir(parents=True, exist_ok=True)
    shutil.copy2(launcher, internal_bin / "9router")
    (internal_bin / "9router").chmod(0o755)
    print(f">>> Successfully {progress_ed} 9Router -> {launcher}")

    if is_update:
        return [launcher, internal_bin / "9router"]
    return [launcher]

ninerouter_satisfied = make_satisfied("9router")
ninerouter_is_pin_satisfied = make_pin_check("", "daemon service + launcher (force reinstall)")
ninerouter_owned_paths = make_owned(
    NINEROUTER_LAUNCHERS,
    config=[NINEROUTER_DATA_DIR_NAME],
    extra=lambda: [
        data_home() / NINEROUTER_DATA_DIR_NAME / NINEROUTER_INTERNAL_BIN / "9router",
        agents_arwaky_config_dir() / "ninerouter.env",
    ],
)
ninerouter_install = make_install(_ninerouter_lifecycle)
ninerouter_update = make_update(_ninerouter_lifecycle)

def _unit(*, satisfied, install, update, is_pin_satisfied, owned_paths) -> AdapterUnit:
    return AdapterUnit(
        satisfied=satisfied,
        install=install,
        update=update,
        is_pin_satisfied=is_pin_satisfied,
        owned_paths=owned_paths,
    )

#: tool_id → unit for 9router (merged by root_tools_container).
ADAPTER_UNITS: dict[str, AdapterUnit] = {
    "9router": _unit(
        satisfied=ninerouter_satisfied,
        install=ninerouter_install,
        update=ninerouter_update,
        is_pin_satisfied=ninerouter_is_pin_satisfied,
        owned_paths=ninerouter_owned_paths,
    ),
}

__all__ = [
    "ADAPTER_UNITS",
    "NinerouterToolsAdapter",
    "ninerouter_install",
    "ninerouter_is_pin_satisfied",
    "ninerouter_owned_paths",
    "ninerouter_satisfied",
    "ninerouter_update",
]
