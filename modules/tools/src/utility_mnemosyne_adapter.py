"""Mnemosyne adapter (uv, [mcp] extra) — unified install + update + teardown.

vendor/mnemosyne is a Python package run via `uv run` (no venv copy).
The MCP stdio server lives in the [mcp] optional-dependency group, so the
launchers are written with `uv_args=["--extra", "mcp"]` — without it uv dies
with "MCP not installed" (mnemosyne.mcp_server ImportError).

Stateless leaf (AES404): module-level functions only, no classes.
"""
from __future__ import annotations

import subprocess
from pathlib import Path

from modules.shared.src.taxonomy_core_error import ToolUpdateError
from modules.shared.src.taxonomy_paths_constant import PROVENANCE_MARKER
from modules.shared.src.taxonomy_paths_constant import REPO_ROOT as repo_root
from modules.shared.src.taxonomy_xdg_atomic_io import (
    atomic_write_text,
    ensure_bin_home,
    ensure_path,
    warn_if_bin_not_on_path,
)
from modules.shared.src.taxonomy_xdg_paths import bin_home


def ensure_source(root: Path, src_rel: str) -> Path:
    """Ensure `root/src_rel` exists, attempting a git submodule init first."""
    src = root / src_rel
    if not src.exists():
        print(f">>> Initializing submodule {src_rel}...")
        subprocess.run(
            ["git", "-C", str(root), "submodule", "update", "--init", src_rel],
            check=False,
        )
    return src

def generic_owned(
    spec,
    launcher_names: list[str],
    *,
    extra: list[Path] | None = None,
    config: list[str] | None = None,
) -> list[Path]:
    """Generic XDG owned set for one tool: bin launchers + data + cache.

    Adapters extend it with tool-specific extras (internal-bin copies,
    env files, daemon units) via *extra* and with installer-owned
    config subtrees (``config_home() / name``) via *config*.
    """
    from modules.shared.src.taxonomy_xdg_paths import cache_home, config_home, data_home

    paths: list[Path] = [bin_home() / name for name in launcher_names]
    paths.append(data_home() / spec.id)
    paths.append(cache_home() / spec.id)
    for name in config or []:
        paths.append(config_home() / name)
    paths.extend(extra or [])
    return paths

def write_uv_launchers(
    src_rel: str,
    launchers: list[tuple[str, str]],
    root: Path | None = None,
    uv_args: list[str] | None = None,
) -> list[Path]:
    """Write uv-run launchers for a Python tool.

    Args:
        src_rel: Relative path from repo root to tool source (e.g. "internal/vision-arwaky").
        launchers: List of (launcher_name, entry_command) tuples.
            Each launcher runs: uv run <uv_args> --directory <src_rel> <entry_command>
        root: Override repo root (default: resolved from this file's location).
        uv_args: Extra uv flags inserted before --directory, e.g. ["--extra", "mcp"]
            to materialize optional dependency groups in the runtime venv.

    Returns:
        List of created launcher paths.
    """
    ensure_bin_home()
    baked_root = str(root) if root is not None else str(repo_root)
    extra = "".join(repr(a) + ", " for a in (uv_args or []))
    created = []
    for name, entry in launchers:
        target = bin_home() / name
        content = (
            "#!/usr/bin/env python3\n"
            f"# {PROVENANCE_MARKER}\n"
            "import os, sys\n"
            "from pathlib import Path\n"
            f'root = Path(os.environ.get("AGENTS_ARWAKY_ROOT", {baked_root!r}))\n'
            f'os.execvpe("uv", ["uv", "run", {extra}"--directory", str(root / "{src_rel}"), '
            f'"{entry}", *sys.argv[1:]], os.environ.copy())\n'
        )
        atomic_write_text(target, content)
        created.append(target)
    warn_if_bin_not_on_path()
    ensure_path()
    return created

ROOT = repo_root

SRC_REL = "vendor/mnemosyne"
LAUNCHERS = [
    ("mnemosyne", "mnemosyne"),
    ("mnemosyne-mcp", "mnemosyne"),
]
# The MCP stdio server lives in the [mcp] optional-dependency group; uv run
# without it dies with "MCP not installed" (mnemosyne.mcp_server ImportError).
UV_ARGS = ["--extra", "mcp"]

def _write_launchers(root: Path) -> list[Path]:
    created = write_uv_launchers(SRC_REL, LAUNCHERS, root=root, uv_args=UV_ARGS)
    for p in created:
        print(f"  -> {p}")
    return created

def satisfied(spec, root: Path | None = None) -> bool:
    return (bin_home() / "mnemosyne").exists()

# -- install (from old installer adapter, verbatim mechanics) ----------------
def install(spec, root: Path = ROOT, *, daemons=None) -> list[Path]:
    root = root or ROOT
    src_dir = root / SRC_REL
    if not ensure_source(root, SRC_REL):
        raise FileNotFoundError(f"source not found {src_dir}")

    created = _write_launchers(root)
    print(">>> Successfully installed mnemosyne")
    return created

# -- update (from old updater adapter) ---------------------------------------
def is_pin_satisfied(spec, root: Path) -> tuple[bool, str]:
    source = root / SRC_REL
    if not source.exists():
        return False, "submodule not initialized"
    return False, "uv project (rebuild required)"

def update(spec, root: Path) -> list[Path]:

    source = root / SRC_REL
    if not update_submodule(root, SRC_REL):
        raise ToolUpdateError(f"submodule update failed: {SRC_REL}")
    if not source.exists():
        raise ToolUpdateError(f"source not found {source}")

    created = _write_launchers(root)
    print(">>> Successfully updated mnemosyne")
    return created

# -- teardown data --------------------------------------------------------------
def owned_paths(spec, root: Path | None = None) -> list[Path]:
    return generic_owned(spec, ["mnemosyne", "mnemosyne-mcp"])
