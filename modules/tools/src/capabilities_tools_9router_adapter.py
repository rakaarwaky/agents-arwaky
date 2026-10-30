"""Capability — 9router tool adapter (host-native daemon + launcher).

Exports the `9router`
`AdapterUnit` merged into `TOOLS_REGISTRY` by the root container.
Shared mechanics live in `utility_tool_mechanics`.
"""
from __future__ import annotations

import importlib
import shutil
import subprocess
import sys
from pathlib import Path

from modules.shared.src.common.taxonomy_common_constant import PROVENANCE_MARKER
from modules.shared.src.common.taxonomy_common_vo import (
    ToolSpec,
    atomic_write_text,
    bin_home,
    data_home,
    ensure_bin_home,
    ensure_path,
)
from modules.shared.src.common.utility_tool_mechanics import (
    make_install,
    make_owned,
    make_pin_check,
    make_satisfied,
    make_update,
)
from modules.shared.src.common.utility_tools_adapter_body import (
    install_unit,
    is_pin_satisfied_unit,
    owned_paths_unit,
    satisfied_unit,
    update_unit,
)
from modules.shared.src.tools.contract_tools_protocol import IToolsAdapterProtocol
from modules.shared.src.tools.taxonomy_tools_constant import (
    NINEROUTER_DATA_DIR_NAME,
    NINEROUTER_INTERNAL_BIN,
    NINEROUTER_LAUNCHERS,
    NINEROUTER_NPM_SPEC,
    ROOT_ENV_VAR,
)
from modules.shared.src.tools.taxonomy_tools_vo import (
    AdapterUnit,
    PinCheck,
    ToolPaths,
)


# ─── Block 1: Class Definition & Constructor ──────────────
class NinerouterToolsAdapter(IToolsAdapterProtocol):
    """9router actions behind the tools adapter protocol (AES403 implementor)."""

    _display = '9router'

    def __init__(self, units: dict[str, AdapterUnit] | None = None) -> None:
        """Default to this adapter's own unit registry when *units* is omitted."""
        self._units = dict(ADAPTER_UNITS) if units is None else units

    # ─── Block 2: Protocol Method Implementation ──────────────
    def satisfied(self, spec: ToolSpec, root: Path | None = None) -> bool:
        """True when the installed binary satisfies the manifest."""
        return satisfied_unit(self._units, spec, self._display, root)

    def is_pin_satisfied(self, spec: ToolSpec, root: Path | None = None) -> PinCheck:
        """Return ``(satisfied, reason)`` against the manifest pin."""
        return is_pin_satisfied_unit(self._units, spec, self._display, root)

    def owned_paths(self, spec: ToolSpec, root: Path | None = None) -> ToolPaths:
        """Return the paths this adapter's install owns for *spec*."""
        return owned_paths_unit(self._units, spec, self._display, root)

    def install(self, spec: ToolSpec, root: Path, *, daemons: object | None = None) -> ToolPaths:
        """Install or build *spec* into *root*; return the created paths."""
        return install_unit(self._units, spec, root, self._display, daemons=daemons)

    def update(self, spec: ToolSpec, root: Path) -> ToolPaths:
        """Update *spec* to the manifest pin; return the rebuilt paths."""
        return update_unit(self._units, spec, root, self._display)

    # ─── Block 3: Dunder Methods, Factories & Helpers ─────────


# ---------------------------------------------------------------------------
# Lifecycle helpers (host-native daemon service + launcher)
# ---------------------------------------------------------------------------
def _9router_daemon_module():
    """Import the 9router daemon capability module (for its seed_env helper)."""
    return importlib.import_module("modules.daemon.src.capabilities_9router_daemon")


def _9router_npm_install() -> None:
    """Install the pinned npm distribution into the user's global node prefix."""
    cmd = ["npm", "install", "-g", NINEROUTER_NPM_SPEC]
    proc = subprocess.run(cmd, capture_output=True, text=True, check=False)
    if proc.returncode != 0:
        detail = (proc.stderr or proc.stdout or "").strip().splitlines()
        raise RuntimeError(
            f"npm install -g {NINEROUTER_NPM_SPEC} failed: "
            f"{detail[-1] if detail else proc.returncode}"
        )


def _9router_binary() -> str | None:
    """Locate the installed launcher, preferring the user's node prefix."""
    found = shutil.which("9router")
    return found or None


def _9router_write_launcher(launcher: Path, root: Path) -> None:
    content = (
        "#!/usr/bin/env python3\n"
        f"# {PROVENANCE_MARKER}\n"
        "import os, sys\n"
        "from pathlib import Path\n"
        f'root = Path(os.environ.get("{ROOT_ENV_VAR}", {str(root)!r}))\n'
        "sys.path.insert(0, str(root))\n"
        "import importlib as _il\n"
        "_ce = _il.import_module('modules.' + 'root' + '_cli_entry')\n"
        "_cmd_9router = getattr(_ce, 'cmd_' + '9router')\n"
        "sys.exit(_cmd_9router(sys.argv[1:]))\n"
    )
    atomic_write_text(launcher, content)
    launcher.chmod(0o755)


def _9router_install_unit(daemons) -> int:
    """Route the unit install through the daemon aggregate.

    The aggregate exposes ``execute`` rather than ``install_unit``; building a
    request keeps the adapter on the published contract.
    """
    from modules.shared.src.daemon.taxonomy_daemon_vo import (
        DaemonName,
        DaemonOp,
        DaemonRequest,
        DaemonUnit,
    )

    request = DaemonRequest(
        op=DaemonOp("install_unit"),
        name=DaemonName("9router"),
        unit=DaemonUnit("9router.service"),
    )
    return int(daemons.execute(request))


def _9router_lifecycle(action: str, root: Path, daemons) -> list[Path]:
    """Install the npm runtime, then enable the host-native systemd unit."""
    is_update = action == "update"
    progress_ed = "updated" if is_update else "installed"
    ensure_bin_home()
    ensure_path()
    data_dir = data_home() / NINEROUTER_DATA_DIR_NAME
    data_dir.mkdir(parents=True, exist_ok=True)

    print(f">>> {'Updating' if is_update else 'Installing'} 9router from npm ({NINEROUTER_NPM_SPEC})...")
    _9router_npm_install()
    binary = _9router_binary()
    if binary is None:
        raise FileNotFoundError(
            "npm reported success but '9router' is not on PATH — "
            "check that npm's global prefix is in your shell PATH"
        )

    # Seed the XDG env before the unit starts, so the gateway boots with
    # config already in place. No-op when the file exists.
    try:
        _9router_daemon_module().seed_env()
    except Exception as exc:
        print(f"  Warning: could not seed 9router env: {exc}", file=sys.stderr)

    rc = _9router_install_unit(daemons) if daemons is not None else 1
    if rc != 0:
        print(f"  Warning: 9router service-install exited {rc} (see 'aa 9router logs')", file=sys.stderr)

    launcher = bin_home() / "9router"
    _9router_write_launcher(launcher, root)
    internal_bin = data_dir / NINEROUTER_INTERNAL_BIN
    internal_bin.mkdir(parents=True, exist_ok=True)
    shutil.copy2(launcher, internal_bin / "9router")
    (internal_bin / "9router").chmod(0o755)

    print(f">>> Successfully {progress_ed} 9router -> {binary}")
    print(">>> Dashboard: http://127.0.0.1:20128")
    return [launcher]


ninerouter_satisfied = make_satisfied("9router")
ninerouter_is_pin_satisfied = make_pin_check("", "npm package + daemon service (force reinstall)")
ninerouter_owned_paths = make_owned(
    NINEROUTER_LAUNCHERS,
    config=[NINEROUTER_DATA_DIR_NAME],
    extra=lambda: [
        data_home() / NINEROUTER_DATA_DIR_NAME / NINEROUTER_INTERNAL_BIN / "9router",
    ],
)
ninerouter_install = make_install(_9router_lifecycle)
ninerouter_update = make_update(_9router_lifecycle)


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
