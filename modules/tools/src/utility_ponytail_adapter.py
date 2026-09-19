"""Ponytail adapter (npm, no build) — unified install + update + teardown.

@dietrichgebert/ponytail has NO build script and no lockfile — just copy
source to $XDG_DATA_HOME/ponytail and install ponytail-mcp dependencies
(@modelcontextprotocol/sdk, zod) via npm. Entry MCP = ponytail-mcp/index.js.

Stateless leaf (AES404): module-level functions only, no classes.
"""
from __future__ import annotations

from pathlib import Path

from modules.shared.src.taxonomy_core_error import ToolUpdateError
from modules.shared.src.taxonomy_xdg_paths import data_home
from modules.tools.src.utility_tool_mechanics import ROOT, copy_app, ensure_source, finish_bin, generic_owned, require, run, write_node_launcher

SRC_REL = "vendor/ponytail"
APP_DIR_REL = "ponytail"
ENTRY = "ponytail-mcp/index.js"

# Old node_modules in vendor are not copied (may be stale); deps are reinstalled
# with npm --prefix inside APP_DIR/ponytail-mcp.
IGNORES = ["node_modules", ".git", "__pycache__", "*.egg-info", ".venv", "venv"]


def _build(src: Path) -> None:
    """Copy source and install ponytail-mcp deps (shared install/update step)."""
    app_dir = data_home() / APP_DIR_REL
    copy_app(src, app_dir, IGNORES)
    mcp_dir = app_dir / "ponytail-mcp"
    if (mcp_dir / "package.json").exists():
        run(["npm", "ci", "--no-audit", "--no-fund"], mcp_dir)
    entry = app_dir / ENTRY
    if not entry.exists():
        raise FileNotFoundError(f"entry not found {entry}")


def _write_launcher() -> Path:
    from modules.shared.src.taxonomy_xdg_paths import bin_home
    app_dir = data_home() / APP_DIR_REL
    launcher = write_node_launcher("ponytail-mcp", app_dir / ENTRY)
    finish_bin()
    return launcher


def satisfied(spec, root: Path | None = None) -> bool:
    from modules.shared.src.taxonomy_xdg_paths import bin_home
    return (bin_home() / "ponytail-mcp").exists()


# -- install (from old installer adapter, verbatim mechanics) ----------------
def install(spec, root: Path = ROOT, *, daemons=None) -> list[Path]:
    root = root or ROOT
    src = ensure_source(root, SRC_REL)
    if not (src / "package.json").exists():
        raise FileNotFoundError(f"ponytail source not found (submodule not initialized): {src}")
    if not require("npm", "ponytail requires npm (https://nodejs.org)"):
        raise FileNotFoundError("npm is required (https://nodejs.org).")

    print(f">>> Installing ponytail (no build) into {data_home() / APP_DIR_REL}...")
    _build(src)
    launcher = _write_launcher()
    print(">>> Successfully installed ponytail")
    return [launcher]


# -- update (from old updater adapter) ---------------------------------------
def is_pin_satisfied(spec, root: Path) -> tuple[bool, str]:
    source = root / SRC_REL
    if not source.exists():
        return False, "submodule not initialized"
    return False, "npm workspace (rebuild required)"


def update(spec, root: Path) -> list[Path]:
    from modules.shared.src.utility_git_update import update_submodule

    source = root / SRC_REL
    if not update_submodule(root, SRC_REL):
        raise ToolUpdateError(f"submodule update failed: {SRC_REL}")
    if not (source / "package.json").exists():
        raise ToolUpdateError("ponytail source not found (submodule not initialized)")
    if not require("npm", "ponytail requires npm (https://nodejs.org)"):
        raise ToolUpdateError("ponytail requires npm (https://nodejs.org)")

    print(f">>> Updating ponytail into {data_home() / APP_DIR_REL}...")
    _build(source)
    launcher = _write_launcher()
    print(">>> Successfully updated ponytail")
    return [launcher]


# -- teardown data --------------------------------------------------------------
def owned_paths(spec, root: Path | None = None) -> list[Path]:
    return generic_owned(spec, ["ponytail-mcp"])
