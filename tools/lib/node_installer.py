#!/usr/bin/env python3
"""Shared Node.js-based tool installer pattern (DRY: 5+ installers pakai ini)."""
from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "lib"))

from paths import repo_root  # type: ignore[import-not-found]
from xdg import (  # type: ignore[import-untyped]
    bin_home,
    cache_home,
    data_home,
    ensure_bin_home,
    ensure_path,
    warn_if_bin_not_on_path,
)


def run(cmd, cwd=None):
    subprocess.run(cmd, cwd=cwd, check=True)


# Artefak vendor yang TIDAK boleh ikut tersalin ke build dir:
# - node_modules: deps lama bisa berisi symlink putus (pnpm .old_modules-*);
#   install deps fresh di build dir justru wajib.
# - .git/__pycache__/.venv/dist dsb: sampah/stale yang tidak relevan utk build.
_BUILD_IGNORES = shutil.ignore_patterns(
    "node_modules",
    ".git",
    ".old_modules*",
    "__pycache__",
    ".venv",
    "venv",
    "dist",
    "target",
    "*.egg-info",
    ".next",
    ".turbo",
)


def build(source_dir: Path, build_dir: Path):
    """Build a Node.js project using bun or npm in an isolated cache directory."""
    if build_dir.exists():
        shutil.rmtree(build_dir)
    shutil.copytree(source_dir, build_dir, ignore=_BUILD_IGNORES)
    if shutil.which("bun"):
        run(["bun", "install"], build_dir)
        run(["bun", "run", "build"], build_dir)
    elif shutil.which("npm"):
        run(["npm", "install", "--no-audit", "--no-fund"], build_dir)
        run(["npm", "run", "build"], build_dir)
    else:
        raise RuntimeError("Neither bun nor npm found.")


def install_runtime(build_dir: Path, target_dir: Path):
    """Copy built artifacts to XDG data directory."""
    if target_dir.exists():
        shutil.rmtree(target_dir)
    target_dir.mkdir(parents=True, exist_ok=True)
    if (build_dir / "dist").exists():
        shutil.copytree(build_dir / "dist", target_dir / "dist")
    shutil.copy2(build_dir / "package.json", target_dir / "package.json")
    if (build_dir / "node_modules").exists():
        shutil.copytree(
            build_dir / "node_modules",
            target_dir / "node_modules",
            dirs_exist_ok=True,
        )


def install_launcher(
    tool_name: str,
    aliases: list[str] | None = None,
    entry_point: str = "index.js",
    custom_launcher_content: str | None = None,
    root: Path | None = None,
):
    """Create Node launcher script in XDG bin. Returns launcher path."""
    ensure_bin_home()
    launcher = bin_home() / tool_name
    launcher.unlink(missing_ok=True)
    if custom_launcher_content is not None:
        content = custom_launcher_content
    else:
        baked_root = str(root) if root is not None else str(repo_root())
        content = f"""#!/usr/bin/env python3
import os, sys
from pathlib import Path
root = Path(os.environ.get("AGENTS_ARWAKY_ROOT", {repr(baked_root)}))
data = Path(os.environ.get("XDG_DATA_HOME", str(Path.home() / ".local/share"))) / "{tool_name}"
os.execvpe("node", ["node", str(data / "dist" / "{entry_point}"), *sys.argv[1:]], os.environ.copy())
"""
    launcher.write_text(content, encoding="utf-8")
    launcher.chmod(0o755)
    for alias in (aliases or []):
        # Jangan buat symlink ke diri sendiri (alias == tool_name)
        if alias == tool_name:
            continue
        a = bin_home() / alias
        a.unlink(missing_ok=True)
        a.symlink_to(launcher)
    warn_if_bin_not_on_path()
    ensure_path()
    return launcher


def install_node_tool(
    tool_name: str,
    vendor_subpath: str,
    aliases: list[str] | None = None,
    entry_point: str = "index.js",
    custom_launcher_content: str | None = None,
) -> int:
    """Complete installation pipeline for a Node.js-based tool."""
    vendor_dir = ROOT / vendor_subpath
    target_dir = data_home() / tool_name
    # Build artifacts bersifat transient -> $XDG_CACHE_HOME (bukan data dir).
    build_dir = cache_home() / "agents-arwaky" / f"build-{tool_name}"

    if not vendor_dir.exists() or not (vendor_dir / "package.json").exists():
        print(f"Error: Upstream source not found at {vendor_dir}.", file=sys.stderr)
        return 1

    print(f">>> Building {tool_name} into {target_dir}...")
    try:
        build(vendor_dir, build_dir)
        install_runtime(build_dir, target_dir)
    finally:
        # Selalu bersihkan build cache, termasuk bila build gagal di tengah.
        if build_dir.exists():
            shutil.rmtree(build_dir)
    launcher = install_launcher(
        tool_name, aliases, entry_point, custom_launcher_content=custom_launcher_content
    )
    print(f">>> Successfully installed {tool_name} -> {launcher}")
    return 0
