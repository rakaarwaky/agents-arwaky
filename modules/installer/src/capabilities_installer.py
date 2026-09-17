"""Tool install capability — data-driven dispatch on ToolSpec.runner."""
from __future__ import annotations

import json
import os
import shutil
import subprocess
from pathlib import Path

from modules.shared.src.launcher.capabilities_launcher_writer import write_generic_launcher
from modules.shared.src.logging.utility_logging import info, ok, sub, warn
from modules.shared.src.manifest.capabilities_manifest_reader import load_tools
from modules.shared.src.paths.utility_paths import repo_root
from modules.shared.src.tool.contract_tool_protocol import IToolInstaller
from modules.shared.src.tool.taxonomy_tool_vo import InstallResult, ToolSpec
from modules.shared.src.venv.capabilities_venv_installer import (
    ensure_venv,
    install_package,
    setup_bin_links,
    setup_xdg_directories,
)
from modules.shared.src.xdg.utility_xdg_atomic_io import ensure_bin_home, ensure_path
from modules.shared.src.xdg.utility_xdg_paths import bin_home, cache_home, config_home, data_home


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


class ToolInstaller(IToolInstaller):
    """Data-driven installer: dispatch on spec.runner, ported from tools/install/*.

    # Block 1: Constructor & runner dispatch
    # Block 2: Runner-specific installs (cargo / uv / pip / generic)
    # Block 3: Install-all loop
    """

    # -- Block 1: Constructor & runner dispatch --------------------------------
    def __init__(self, root: Path | None = None) -> None:
        self._root = root or repo_root()

    def install(self, spec: ToolSpec) -> InstallResult:
        ensure_bin_home()
        ensure_path()
        if spec.runner == "cargo":
            return self._install_cargo(spec)
        if spec.runner in {"uv", "python"}:
            return self._install_uv(spec)
        if spec.runner == "pip":
            return self._install_pip(spec)
        return self._install_generic(spec)

    # -- Block 2: Runner-specific installs -------------------------------------
    def _ensure_submodule(self, spec: ToolSpec) -> bool:
        src_rel = spec.path
        if not (self._root / src_rel).exists():
            sub(f"Initializing submodule {src_rel}...")
            subprocess.run(
                ["git", "-C", str(self._root), "submodule", "update", "--init", src_rel],
                check=False,
            )
        return (self._root / src_rel).exists()

    def _install_cargo(self, spec: ToolSpec) -> InstallResult:
        """Port of install_lint.py: cargo build --release into the XDG cache."""
        src_dir = self._root / spec.path
        if not self._ensure_submodule(spec):
            return InstallResult(False, spec.id, f"source not found {spec.path}")
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
            return InstallResult(False, spec.id, f"cargo build failed: {exc}")
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
        return InstallResult(True, spec.id, "cargo build finished")

    def _install_uv(self, spec: ToolSpec) -> InstallResult:
        """Port of install_blender/vision/qwen_web: venv + pip -e + bin links."""
        src_dir = self._root / spec.path
        if not self._ensure_submodule(spec):
            return InstallResult(False, spec.id, f"source not found {spec.path}")
        tool_name = spec.binary or f"{spec.id}-arwaky"
        python_bin = ensure_venv(tool_name, force=False)
        install_package(python_bin, src_dir, tool_name)
        setup_xdg_directories(tool_name)
        setup_bin_links(python_bin, _venv_launcher_names(spec))
        info(f"Installed {spec.id} (venv at {python_bin.parent})")
        return InstallResult(True, spec.id, "venv install finished")

    def _install_pip(self, spec: ToolSpec) -> InstallResult:
        src_dir = self._root / spec.path
        if not self._ensure_submodule(spec):
            return InstallResult(False, spec.id, f"source not found {spec.path}")
        tool_name = spec.binary or f"{spec.id}-arwaky"
        python_bin = ensure_venv(tool_name, force=False)
        subprocess.run([str(python_bin), "-m", "pip", "install", str(src_dir)], check=True)
        setup_xdg_directories(tool_name)
        return InstallResult(True, spec.id, "pip install finished")

    def _install_generic(self, spec: ToolSpec) -> InstallResult:
        """Default (vendor JS tools) port of install_context7/ponytail/codegraph.

        Copies the source into the XDG data dir, installs + builds with the
        package manager present, and writes a node launcher per declared
        binary. Simplification vs the 12 per-tool scripts: single npm/pnpm
        detection instead of per-tool package-manager overrides.
        """
        src_dir = self._root / spec.path
        if not self._ensure_submodule(spec):
            return InstallResult(False, spec.id, f"source not found {spec.path}")
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
        return InstallResult(True, spec.id, "generic install finished")

    # -- Block 3: Install-all loop ---------------------------------------------
    def install_all(self) -> list[InstallResult]:
        """Install every manifest tool; skip missing runners gracefully."""
        results: list[InstallResult] = []
        for tool in load_tools():
            spec = ToolSpec(
                id=tool.id,
                category=tool.category,
                binary=tool.binary,
                is_mcp=tool.is_mcp,
                description=tool.description,
                path=tool.path,
                alias=tool.alias,
                mcp_binary=getattr(tool, "mcp_binary", None),
            )
            results.append(self.install(spec))
        return results
