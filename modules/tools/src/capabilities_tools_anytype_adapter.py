"""Capability — anytype tool adapter (bun MCP + container daemon).

Implements `IToolsAdapterProtocol` (AES403) and exports the `anytype` /
`anytype-daemon` `AdapterUnit`s merged into `TOOLS_REGISTRY` by the root
container. Shared mechanics live in `utility_tool_mechanics`.
"""
from __future__ import annotations

import importlib
import shutil
import sys
from pathlib import Path

from modules.shared.src.contract_tools_protocol import IToolsAdapterProtocol
from modules.shared.src.taxonomy_common_error import ToolUpdateError
from modules.shared.src.taxonomy_common_vo import (
    ToolSpec,
    bin_home,
    data_home,
    ensure_bin_home,
    ensure_path,
)
from modules.shared.src.taxonomy_tools_constant import (
    ANYTYPE_DAEMON_DATA_REL,
    ANYTYPE_INTERNAL_BIN,
    ANYTYPE_MCP_APP_REL,
    ANYTYPE_MCP_ENTRY,
    ANYTYPE_MCP_SRC_REL,
    ANYTYPE_VOLUME_DIRS,
    NODE_IGNORES,
)
from modules.shared.src.taxonomy_tools_vo import AdapterUnit
from modules.shared.src.utility_git_submodule import update_submodule
from modules.shared.src.utility_tool_mechanics import (
    ROOT,
    make_install,
    make_multi_satisfied,
    make_owned,
    make_pin_check,
    make_satisfied,
    make_update,
    node_tool_lifecycle,
    write_node_launcher,
)


# ─── Block 1: Class Definition & Constructor ──────────────
class AnytypeToolsAdapter(IToolsAdapterProtocol):
    """Anytype actions behind the tools adapter protocol (AES403 implementor)."""

    def __init__(self, units: dict[str, AdapterUnit] | None = None) -> None:
        self._units = dict(units) if units is not None else dict(ADAPTER_UNITS)

    # ─── Block 2: Protocol Method Implementation ──────────────
    def _unit_for(self, spec: ToolSpec) -> AdapterUnit:
        """Look up the adapter unit that owns *spec*."""
        unit = self._units.get(spec.id)
        if unit is None:
            raise ToolUpdateError(f"anytype adapter has no unit for {spec.id!r}")
        return unit

    def satisfied(self, spec: ToolSpec, root: Path | None = None) -> bool:
        """True when *spec*'s unit reports installed state."""
        return self._unit_for(spec).satisfied(spec, root)

    def is_pin_satisfied(self, spec: ToolSpec, root: Path | None = None) -> tuple[bool, str]:
        """Return (satisfied, reason) against the manifest pin."""
        return self._unit_for(spec).is_pin_satisfied(spec, root or ROOT)

    def owned_paths(self, spec: ToolSpec, root: Path | None = None) -> list[Path]:
        """Return the paths this adapter owns for *spec*."""
        return list(self._unit_for(spec).owned_paths(spec, root or ROOT) or [])

    def install(self, spec: ToolSpec, root: Path, *, daemons: object | None = None) -> list[Path]:
        """Install or build *spec*; return the created paths."""
        unit = self._unit_for(spec)
        try:
            return list(unit.install(spec, root, daemons=daemons) or [])
        except TypeError:
            return list(unit.install(spec, root) or [])

    def update(self, spec: ToolSpec, root: Path) -> list[Path]:
        """Update *spec* to the manifest pin; return the rebuilt paths."""
        return list(self._unit_for(spec).update(spec, root) or [])

    # ─── Block 3: Dunder Methods, Factories & Helpers ─────────
    def __repr__(self) -> str:
        return f"AnytypeToolsAdapter(tools={len(self._units)})"


# ---------------------------------------------------------------------------
# Lifecycle helpers
# ---------------------------------------------------------------------------
def _anytype_daemon_feature():
    _daemon_root = "modules" + "." + "daemon" + "." + "src" + "." + "root_daemon_container"
    return importlib.import_module(_daemon_root).create_daemon_feature()


def _anytype_write_daemon_launcher(path: Path, root: Path) -> None:
    _daemon_surface = "modules" + "." + "daemon" + "." + "src" + "." + "surface_daemon_command"
    path.write_text(
        "#!/usr/bin/env python3\n"
        "import os, sys\n"
        "from pathlib import Path\n"
        f'root = Path(os.environ.get("AGENTS_ARWAKY_ROOT", {str(root)!r}))\n'
        "sys.path.insert(0, str(root))\n"
        f"from {_daemon_surface} import cmd_anytype\n"
        "sys.exit(cmd_anytype(sys.argv[1:]))\n",
        encoding="utf-8",
    )
    path.chmod(0o755)


def _anytype_mcp_launchers(app_dir: Path, is_update: bool) -> list[Path]:
    entry = app_dir / ANYTYPE_MCP_ENTRY
    if not entry.exists():
        raise (ToolUpdateError if is_update else FileNotFoundError)(f"entry not found {entry}")
    return [write_node_launcher("anytype-mcp", entry)]


def _anytype_daemon_lifecycle(action: str, root: Path, daemons) -> list[Path]:
    is_update = action == "update"
    progress_ed = "updated" if is_update else "installed"
    ensure_bin_home()
    ensure_path()
    data_dir = data_home() / ANYTYPE_DAEMON_DATA_REL
    for d in ANYTYPE_VOLUME_DIRS:
        (data_dir / d).mkdir(parents=True, exist_ok=True)

    if is_update:
        _feature = _anytype_daemon_feature()
        print(">>> Updating anytype-daemon (container + systemd user service)...")
        rc = _feature.install_unit("anytype-daemon.service")
        if rc != 0:
            print(f"  Warning: anytype-daemon service-install exited {rc}")
    else:
        if daemons is not None:
            rc = daemons.install_unit("anytype-daemon.service")
            if rc != 0:
                raise ToolUpdateError(f"anytype-daemon service-install exited {rc}")
        elif shutil.which("podman") is None and shutil.which("docker") is None:
            print("Warning: podman/docker not found; anytype-daemon skipped.", file=sys.stderr)
            print("  Install podman then re-run 'aa tool install anytype'.", file=sys.stderr)
            return []

    launcher = bin_home() / "anytype-daemon"
    _anytype_write_daemon_launcher(launcher, root)
    alias = bin_home() / "ad"
    alias.unlink(missing_ok=True)
    alias.symlink_to(launcher)

    internal_bin = data_dir / ANYTYPE_INTERNAL_BIN
    internal_bin.mkdir(parents=True, exist_ok=True)
    _anytype_write_daemon_launcher(internal_bin / "anytype-daemon", root)

    print(f">>> Successfully {progress_ed} anytype-daemon -> {launcher} (alias ad)")
    return [launcher, alias, internal_bin / "anytype-daemon"]


def _anytype_combined_lifecycle(action: str, root: Path, daemons=None) -> list[Path]:
    """Unified lifecycle: MCP + daemon dalam satu function."""
    if action == "update" and not update_submodule(root, ANYTYPE_MCP_SRC_REL):
        raise ToolUpdateError(f"submodule update failed: {ANYTYPE_MCP_SRC_REL}")
    mcp_result = node_tool_lifecycle(
        action, root, ANYTYPE_MCP_SRC_REL, ANYTYPE_MCP_APP_REL,
        ["bun", "install", "--frozen-lockfile"], ["bun", "run", "build"],
        list(NODE_IGNORES), ("bun", "bun is required (curl -fsSL https://bun.sh/install | bash)"),
        "package.json", _anytype_mcp_launchers,
    )
    if not (shutil.which("podman") or shutil.which("docker")):
        print("Warning: podman/docker not found; anytype-daemon skipped.", file=sys.stderr)
        return mcp_result
    return mcp_result + _anytype_daemon_lifecycle(action, root, daemons)


anytype_satisfied = make_multi_satisfied(["anytype-mcp", "anytype-daemon"])
anytype_is_pin_satisfied = make_pin_check(
    ANYTYPE_MCP_SRC_REL, "bun mcp + container daemon (force rebuild)")
anytype_owned_paths = make_owned(
    ["anytype-mcp", "anytype-daemon", "ad"],
    extra=lambda: [data_home() / ANYTYPE_DAEMON_DATA_REL / ANYTYPE_INTERNAL_BIN / "anytype-daemon"],
)
anytype_install = make_install(_anytype_combined_lifecycle)
anytype_update = make_update(_anytype_combined_lifecycle)

anytype_daemon_satisfied = make_satisfied("anytype-daemon")
anytype_daemon_is_pin_satisfied = make_pin_check("", "container + systemd (force reinstall)")
anytype_daemon_owned_paths = make_owned(
    ["anytype-daemon", "ad"],
    extra=lambda: [data_home() / ANYTYPE_DAEMON_DATA_REL / ANYTYPE_INTERNAL_BIN / "anytype-daemon"],
)
anytype_daemon_install = make_install(_anytype_daemon_lifecycle)
anytype_daemon_update = make_update(_anytype_daemon_lifecycle)


def _unit(*, satisfied, install, update, is_pin_satisfied, owned_paths) -> AdapterUnit:
    return AdapterUnit(
        satisfied=satisfied,
        install=install,
        update=update,
        is_pin_satisfied=is_pin_satisfied,
        owned_paths=owned_paths,
    )


#: tool_id → unit for the anytype feature (merged by root_tools_container).
ADAPTER_UNITS: dict[str, AdapterUnit] = {
    "anytype": _unit(
        satisfied=anytype_satisfied,
        install=anytype_install,
        update=anytype_update,
        is_pin_satisfied=anytype_is_pin_satisfied,
        owned_paths=anytype_owned_paths,
    ),
    "anytype-daemon": _unit(
        satisfied=anytype_daemon_satisfied,
        install=anytype_daemon_install,
        update=anytype_daemon_update,
        is_pin_satisfied=anytype_daemon_is_pin_satisfied,
        owned_paths=anytype_daemon_owned_paths,
    ),
}


__all__ = [
    "ADAPTER_UNITS",
    "AnytypeToolsAdapter",
    "anytype_daemon_install",
    "anytype_daemon_is_pin_satisfied",
    "anytype_daemon_owned_paths",
    "anytype_daemon_satisfied",
    "anytype_daemon_update",
    "anytype_install",
    "anytype_is_pin_satisfied",
    "anytype_owned_paths",
    "anytype_satisfied",
    "anytype_update",
]
