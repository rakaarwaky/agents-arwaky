"""Context7 adapter (pnpm workspace) — unified install + update + teardown.

@upstash/context7 is a pnpm workspace (MCP server + CLI). pnpm blocks
postinstall deps by default, so the copied pnpm-workspace.yaml is patched with
`dangerouslyAllowAllBuilds: true`. Runtime is installed in-place to
$XDG_DATA_HOME/context7; launchers point at packages/{mcp,cli}/dist/index.js.

Stateless leaf (AES404): module-level functions only, no classes.
"""
from __future__ import annotations

import sys
from pathlib import Path

from modules.shared.src.taxonomy_core_error import ToolUpdateError
from modules.shared.src.taxonomy_xdg_paths import data_home
from modules.tools.src.utility_tool_mechanics import ROOT, copy_app, ensure_source, finish_bin, generic_owned, require, run, write_node_launcher

SRC_REL = "vendor/context7"
APP_DIR = data_home() / "context7"
# Vendor artifacts that must not be included: stale node_modules (may contain
# broken symlinks), git, old build output, etc.
IGNORES = [
    "node_modules", ".git", ".old_modules*", "__pycache__", "mcpb",
    "dist", "target", "*.egg-info", ".venv", "venv", ".next", ".turbo",
]

LAUNCHERS = {
    "context7-mcp": "packages/mcp/dist/index.js",
    "ctx7": "packages/cli/dist/index.js",
}


def _write_launchers() -> list[Path]:
    """Write node launchers for every context7 entry point (shared install/update)."""
    from modules.shared.src.taxonomy_xdg_paths import bin_home

    created: list[Path] = []
    for name, entry in LAUNCHERS.items():
        target = APP_DIR / entry
        if not target.exists():
            print(f"  Warning: entry not found {target}", file=sys.stderr)
            continue
        created.append(write_node_launcher(name, target))
    return created


def satisfied(spec, root: Path | None = None) -> bool:
    from modules.shared.src.taxonomy_xdg_paths import bin_home
    return (bin_home() / "context7-mcp").exists()


# -- install (from old installer adapter, verbatim mechanics) ----------------
def install(spec, root: Path = ROOT, *, daemons=None) -> list[Path]:
    root = root or ROOT
    src = ensure_source(root, SRC_REL)
    if not (src / "pnpm-workspace.yaml").exists():
        raise FileNotFoundError(f"context7 source not found (submodule not initialized): {src}")
    if not require("pnpm", "context7 is a pnpm workspace"):
        raise FileNotFoundError("pnpm is required (context7 is a pnpm workspace).")

    print(f">>> Installing context7 (pnpm workspace) into {APP_DIR}...")
    copy_app(src, APP_DIR, IGNORES)

    # pnpm blocks postinstall deps by default -> allow in this copy only
    ws = APP_DIR / "pnpm-workspace.yaml"
    if "dangerouslyAllowAllBuilds" not in ws.read_text(encoding="utf-8", errors="replace"):
        with ws.open("a", encoding="utf-8") as f:
            f.write("\ndangerouslyAllowAllBuilds: true\n")

    run(["pnpm", "install", "--frozen-lockfile"], APP_DIR)
    run(["pnpm", "run", "build"], APP_DIR)

    artifacts = _write_launchers()

    finish_bin()
    print(">>> Successfully installed context7")
    return artifacts


# -- update (from old updater adapter) ---------------------------------------
def is_pin_satisfied(spec, root: Path) -> tuple[bool, str]:
    source = root / SRC_REL
    if not source.exists():
        return False, "submodule not initialized"
    return False, "pnpm workspace (rebuild required)"


def update(spec, root: Path) -> list[Path]:
    from modules.shared.src.utility_git_update import update_submodule

    source = root / SRC_REL
    if not update_submodule(root, SRC_REL):
        raise ToolUpdateError(f"submodule update failed: {SRC_REL}")
    if not (source / "pnpm-workspace.yaml").exists():
        raise ToolUpdateError("context7 source not found (submodule not initialized)")
    if not require("pnpm", "context7 is a pnpm workspace"):
        raise ToolUpdateError("pnpm is required (context7 is a pnpm workspace)")

    print(f">>> Updating context7 (pnpm workspace) into {APP_DIR}...")
    copy_app(source, APP_DIR, IGNORES)
    workspace = APP_DIR / "pnpm-workspace.yaml"
    if "dangerouslyAllowAllBuilds" not in workspace.read_text(encoding="utf-8", errors="replace"):
        with workspace.open("a", encoding="utf-8") as fh:
            fh.write("\ndangerouslyAllowAllBuilds: true\n")

    run(["pnpm", "install", "--frozen-lockfile"], APP_DIR)
    run(["pnpm", "run", "build"], APP_DIR)

    created = _write_launchers()

    finish_bin()
    print(">>> Successfully updated context7")
    return created


# -- teardown data --------------------------------------------------------------
def owned_paths(spec, root: Path | None = None) -> list[Path]:
    return generic_owned(spec, list(LAUNCHERS))
