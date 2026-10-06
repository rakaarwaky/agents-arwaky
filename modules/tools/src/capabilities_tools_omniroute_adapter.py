"""Capability — OmniRoute tool adapter (host-native daemon + launcher).

Exports the `omniroute`
`AdapterUnit` merged into `TOOLS_REGISTRY` by the root container.
Shared mechanics live in `utility_tool_mechanics`.
"""
from __future__ import annotations

import importlib
import shutil
import subprocess
import sys
from pathlib import Path

from modules.shared.src.contract_tools_protocol import IToolsAdapterProtocol
from modules.shared.src.taxonomy_common_constant import PROVENANCE_MARKER
from modules.shared.src.taxonomy_common_vo import (
    ToolSpec,
    atomic_write_text,
    bin_home,
    data_home,
    ensure_bin_home,
    ensure_path,
)
from modules.shared.src.taxonomy_tools_constant import (
    OMNIROUTE_DATA_DIR_NAME,
    OMNIROUTE_INTERNAL_BIN,
    OMNIROUTE_LAUNCHERS,
    OMNIROUTE_NPM_SPEC,
    OMNIROUTE_SRC_REL,
    ROOT_ENV_VAR,
)
from modules.shared.src.taxonomy_tools_vo import (
    AdapterUnit,
    PinCheck,
    ToolPaths,
)
from modules.shared.src.utility_tool_mechanics import (
    make_install,
    make_owned,
    make_pin_check,
    make_satisfied,
    make_update,
)
from modules.shared.src.utility_tools_adapter_body import (
    install_unit,
    is_pin_satisfied_unit,
    owned_paths_unit,
    satisfied_unit,
    update_unit,
)


# ─── Block 1: Class Definition & Constructor ──────────────
class OmnirouteToolsAdapter(IToolsAdapterProtocol):
    """OmniRoute actions behind the tools adapter protocol (AES403 implementor)."""

    _display = 'omniroute'

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
def _omniroute_daemon_module():
    """Import the OmniRoute daemon capability module (for its seed_env helper)."""
    return importlib.import_module("modules.daemon.src.capabilities_omniroute_daemon")


def _omniroute_npm_install() -> None:
    """Install the pinned npm distribution into the user's global node prefix.

    The pinned ``vendor/omniroute`` checkout is the version SSOT; the runtime
    comes from the published npm package rather than a source build, because
    upstream's postinstall compiles native SQLite bindings and the package
    already ships a built tree.
    """
    cmd = ["npm", "install", "-g", OMNIROUTE_NPM_SPEC]
    proc = subprocess.run(cmd, capture_output=True, text=True, check=False)
    if proc.returncode != 0:
        detail = (proc.stderr or proc.stdout or "").strip().splitlines()
        raise RuntimeError(
            f"npm install -g {OMNIROUTE_NPM_SPEC} failed: "
            f"{detail[-1] if detail else proc.returncode}"
        )


def _omniroute_binary() -> str | None:
    """Locate the installed launcher, preferring the user's node prefix."""
    found = shutil.which("omniroute")
    return found or None


def _omniroute_write_launcher(launcher: Path, root: Path) -> None:
    content = (
        "#!/usr/bin/env python3\n"
        f"# {PROVENANCE_MARKER}\n"
        "import os, sys\n"
        "from pathlib import Path\n"
        f'root = Path(os.environ.get("{ROOT_ENV_VAR}", {str(root)!r}))\n'
        "sys.path.insert(0, str(root))\n"
        "import importlib as _il\n"
        "_dv = _il.import_module('modules.daemon.src.' + 'surface' + '_daemon_command')\n"
        "_cmd_omniroute = getattr(_dv, 'cmd_' + 'omniroute')\n"
        "sys.exit(_cmd_omniroute(sys.argv[1:]))\n"
    )
    atomic_write_text(launcher, content)
    launcher.chmod(0o755)


def _omniroute_install_unit(daemons) -> int:
    """Route the unit install through the daemon aggregate.

    The aggregate exposes ``execute`` rather than ``install_unit``; building a
    request keeps the adapter on the published contract.
    """
    from modules.shared.src.taxonomy_daemon_vo import (
        DaemonName,
        DaemonOp,
        DaemonRequest,
        DaemonUnit,
    )

    request = DaemonRequest(
        op=DaemonOp("install_unit"),
        name=DaemonName("omniroute"),
        unit=DaemonUnit("omniroute.service"),
    )
    return int(daemons.execute(request))


def _omniroute_lifecycle(action: str, root: Path, daemons) -> list[Path]:
    """Install the npm runtime, then enable the host-native systemd unit."""
    is_update = action == "update"
    progress_ed = "updated" if is_update else "installed"
    ensure_bin_home()
    ensure_path()
    data_dir = data_home() / OMNIROUTE_DATA_DIR_NAME
    data_dir.mkdir(parents=True, exist_ok=True)

    print(f">>> {'Updating' if is_update else 'Installing'} OmniRoute from npm ({OMNIROUTE_NPM_SPEC})...")
    _omniroute_npm_install()
    binary = _omniroute_binary()
    if binary is None:
        raise FileNotFoundError(
            "npm reported success but 'omniroute' is not on PATH — "
            "check that npm's global prefix is in your shell PATH"
        )

    # Seed the XDG env before the unit starts, so the gateway boots with a
    # STORAGE_ENCRYPTION_KEY already in place. No-op when the file exists.
    try:
        _omniroute_daemon_module().seed_env()
    except Exception as exc:
        print(f"  Warning: could not seed omniroute env: {exc}", file=sys.stderr)

    rc = _omniroute_install_unit(daemons) if daemons is not None else 1
    if rc != 0:
        print(f"  Warning: omniroute service-install exited {rc} (see 'aa omniroute logs')", file=sys.stderr)

    launcher = bin_home() / "omniroute"
    _omniroute_write_launcher(launcher, root)
    internal_bin = data_dir / OMNIROUTE_INTERNAL_BIN
    internal_bin.mkdir(parents=True, exist_ok=True)
    shutil.copy2(launcher, internal_bin / "omniroute")
    (internal_bin / "omniroute").chmod(0o755)

    print(f">>> Successfully {progress_ed} OmniRoute -> {binary}")
    print(f">>> Submodule (version SSOT): {root / OMNIROUTE_SRC_REL}")
    print(">>> Dashboard: http://127.0.0.1:20139")
    return [launcher]


omniroute_satisfied = make_satisfied("omniroute")
omniroute_is_pin_satisfied = make_pin_check("", "npm package + daemon service (force reinstall)")
omniroute_owned_paths = make_owned(
    OMNIROUTE_LAUNCHERS,
    config=[OMNIROUTE_DATA_DIR_NAME],
    extra=lambda: [
        data_home() / OMNIROUTE_DATA_DIR_NAME / OMNIROUTE_INTERNAL_BIN / "omniroute",
        # Never delete ~/.omniroute/.env or storage.sqlite: the encryption key
        # there decrypts every stored provider credential, and both files are
        # owned by the gateway, not by this installer.
    ],
)
omniroute_install = make_install(_omniroute_lifecycle)
omniroute_update = make_update(_omniroute_lifecycle)


def _unit(*, satisfied, install, update, is_pin_satisfied, owned_paths) -> AdapterUnit:
    return AdapterUnit(
        satisfied=satisfied,
        install=install,
        update=update,
        is_pin_satisfied=is_pin_satisfied,
        owned_paths=owned_paths,
    )


#: tool_id → unit for omniroute (merged by root_tools_container).
ADAPTER_UNITS: dict[str, AdapterUnit] = {
    "omniroute": _unit(
        satisfied=omniroute_satisfied,
        install=omniroute_install,
        update=omniroute_update,
        is_pin_satisfied=omniroute_is_pin_satisfied,
        owned_paths=omniroute_owned_paths,
    ),
}

__all__ = [
    "ADAPTER_UNITS",
    "OmnirouteToolsAdapter",
    "omniroute_install",
    "omniroute_is_pin_satisfied",
    "omniroute_owned_paths",
    "omniroute_satisfied",
    "omniroute_update",
]
