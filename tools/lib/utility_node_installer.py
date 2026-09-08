#!/usr/bin/env python3
"""Shared Node.js-based tool installer pattern (DRY: 5+ installers pakai ini)."""
from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "lib"))

from xdg import bin_home, data_home, ensure_bin_home


def run(cmd, cwd=None):
    subprocess.run(cmd, cwd=cwd, check=True)


def build(vendor_dir: Path):
    """Build a Node.js project using bun or npm."""
    if shutil.which("bun"):
        run(["bun", "install"], vendor_dir)
        run(["bun", "run", "build"], vendor_dir)
    elif shutil.which("npm"):
        run(["npm", "install", "--no-audit", "--no-fund"], vendor_dir)
        run(["npm", "run", "build"], vendor_dir)
    else:
        raise RuntimeError("Neither bun nor npm found.")


def install_runtime(vendor_dir: Path, target_dir: Path):
    """Copy built artifacts to XDG data directory."""
    if target_dir.exists():
        shutil.rmtree(target_dir)
    target_dir.mkdir(parents=True, exist_ok=True)
    if (vendor_dir / "dist").exists():
        shutil.copytree(vendor_dir / "dist", target_dir / "dist")
    shutil.copy2(vendor_dir / "package.json", target_dir / "package.json")
    if (vendor_dir / "node_modules").exists():
        shutil.copytree(
            vendor_dir / "node_modules",
            target_dir / "node_modules",
            dirs_exist_ok=True,
        )


def install_launcher(
    tool_name: str,
    aliases: list[str] | None = None,
    entry_point: str = "index.js",
    custom_launcher_content: str | None = None,
):
    """Create Node launcher script in XDG bin. Returns launcher path."""
    ensure_bin_home()
    launcher = bin_home() / tool_name
    if custom_launcher_content is not None:
        content = custom_launcher_content
    else:
        content = f"""#!/usr/bin/env python3
import os, sys
from pathlib import Path
data = Path(os.environ.get("XDG_DATA_HOME", str(Path.home() / ".local/share"))) / "{tool_name}"
os.execvpe("node", ["node", str(data / "dist" / "{entry_point}"), *sys.argv[1:]], os.environ.copy())
"""
    launcher.write_text(content, encoding="utf-8")
    launcher.chmod(0o755)
    for alias in (aliases or []):
        a = bin_home() / alias
        a.unlink(missing_ok=True)
        a.symlink_to(launcher)
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

    if not vendor_dir.exists() or not (vendor_dir / "package.json").exists():
        print(f"Error: Upstream source not found at {vendor_dir}.", file=sys.stderr)
        return 1

    print(f">>> Building {tool_name} into {target_dir}...")
    build(vendor_dir)
    install_runtime(vendor_dir, target_dir)
    launcher = install_launcher(
        tool_name, aliases, entry_point, custom_launcher_content=custom_launcher_content
    )
    print(f">>> Successfully installed {tool_name} -> {launcher}")
    return 0
