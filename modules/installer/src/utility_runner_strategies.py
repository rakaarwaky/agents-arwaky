"""Shared runner strategies used by every per-tool installer capability."""
from __future__ import annotations

import json
import os
import shutil
import subprocess
from pathlib import Path

from modules.shared.src.launcher.capabilities_launcher_writer import write_generic_launcher
from modules.shared.src.logging.utility_logging import info, ok, sub, warn
from modules.shared.src.venv.capabilities_venv_installer import (
    ensure_venv,
    install_package,
    setup_bin_links,
    setup_xdg_directories,
)
from modules.shared.src.xdg.utility_xdg_paths import bin_home, cache_home, config_home, data_home
from modules.shared.src.tool.taxonomy_tool_vo import InstallResult, ToolSpec

from modules.installer.src.utility_installer_base import InstallerBase


def _venv_launcher_names(spec: ToolSpec) -> list[tuple[str, str]]:
    """Launcher list a venv tool exposes: binary, mcp binary and alias."""
    launchers: list[tuple[str, str]] = []
    seen: set[str] = set()

    def add(name: str, entry: str) -> None:
        if name and name not in seen:
            launchers.append((name, entry))
            seen.add(name)

    add(spec.binary, spec.binary)
    if spec.mcp_binary:
        add(spec.mcp_binary, spec.mcp_binary)
    if spec.alias:
        add(spec.alias, spec.binary)
    return launchers


def install_cargo(base: InstallerBase, spec: ToolSpec) -> InstallResult:
    """Rust cargo build --release into the XDG cache (lint-arwaky pattern)."""
    src_dir = base._root / spec.path
    if not base._ensure_submodule(spec):
        return base.fail(spec, f"source not found {spec.path}")
    if shutil.which("cargo") is None:
        warn("cargo not found; Rust toolchain unavailable, skipping build.")
        return InstallResult(True, spec.id, "skipped (cargo missing)")
    cache_dir = cache_home() / spec.id
    cache_dir.mkdir(parents=True, exist_ok=True)
    (config_home() / spec.id / "rules").mkdir(parents=True, exist_ok=True)
    (data_home() / spec.id / "reports").mkdir(parents=True, exist_ok=True)
    env = os.environ.copy()
    env["CARGO_TARGET_DIR"] = str(cache_dir)
    env["CARGO_INCREMENTAL"] = "0"
    info(f"Building {spec.id} (cargo) into {cache_dir}...")
    try:
        subprocess.run(["cargo", "build", "--release"], cwd=src_dir, env=env, check=True)
    except subprocess.CalledProcessError as exc:
        return base.fail(spec, f"cargo build failed: {exc}")
    release = cache_dir / "release"
    created: list[str] = []
    for binary in (spec.binary, f"{spec.id}-arwaky", f"{spec.id}-cli", f"{spec.id}-mcp", f"{spec.id}-tui"):
        source = release / binary
        if source.exists():
            target = bin_home() / binary
            shutil.copy2(source, target)
            target.chmod(0o755)
            created.append(str(target))
    if created:
        ok(f"cargo binaries installed: {', '.join(Path(c).name for c in created)}")
    return base.ok(spec, "cargo build finished")


def install_uv(base: InstallerBase, spec: ToolSpec) -> InstallResult:
    """Python venv + pip -e + bin links (blender/vision/qwen-web pattern)."""
    src_dir = base._root / spec.path
    if not base._ensure_submodule(spec):
        return base.fail(spec, f"source not found {spec.path}")
    tool_name = spec.binary or f"{spec.id}-arwaky"
    python_bin = ensure_venv(tool_name, force=False)
    install_package(python_bin, src_dir, tool_name)
    setup_xdg_directories(tool_name)
    setup_bin_links(python_bin, _venv_launcher_names(spec))
    info(f"Installed {spec.id} (venv at {python_bin.parent})")
    return base.ok(spec, "venv install finished")


def install_generic(base: InstallerBase, spec: ToolSpec) -> InstallResult:
    """Copy source into XDG data dir, build with pnpm/npm, write node launcher.

    Used by context7, fetch, ponytail, codegraph, anytype, 9router,
    google-workspace-mcp, mnemosyne, anytype-daemon, skill.
    """
    src_dir = base._root / spec.path
    if not base._ensure_submodule(spec):
        return base.fail(spec, f"source not found {spec.path}")
    app_dir = data_home() / spec.id
    ignores = shutil.ignore_patterns("node_modules", ".git", "__pycache__", "*.egg-info", ".venv", "venv")
    if app_dir.exists():
        shutil.rmtree(app_dir)
    shutil.copytree(src_dir, app_dir, ignore=ignores)
    package_json = app_dir / "package.json"
    if package_json.exists():
        pm = shutil.which("pnpm") and ["pnpm", "install"] or shutil.which("npm") and ["npm", "ci", "--no-audit", "--no-fund"]
        if pm:
            subprocess.run(list(pm), cwd=app_dir, check=False)
        scripts = json.loads(package_json.read_text(encoding="utf-8", errors="replace")).get("scripts", {})
        build = scripts.get("build")
        if build:
            pm_run = shutil.which("pnpm") and ["pnpm", "run"] or ["npm", "run"]
            subprocess.run(list(pm_run), build, cwd=app_dir, check=False)
    entry = app_dir / "index.js"
    if spec.mcp_binary and entry.exists():
        launcher = write_generic_launcher(
            spec.mcp_binary,
            "#!/usr/bin/env python3\n"
            "import os, sys\n"
            f'entry = r"{entry}"\n'
            'os.execvpe("node", ["node", entry, *sys.argv[1:]], os.environ.copy())\n',
            aliases=[spec.binary] if spec.binary != spec.mcp_binary else None,
        )
        ok(f"-> {launcher}")
    return base.ok(spec, "generic install finished")
