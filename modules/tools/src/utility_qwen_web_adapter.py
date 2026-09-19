"""Qwen-web-arwaky adapter (uv venv + Playwright) — unified install + update + teardown.

Creates a venv in ~/.local/share/qwen-web/venv/, pip-installs the
internal/qwen-web-arwaky package, installs Playwright Chromium, sets up
XDG data/state/cache dirs, and symlinks the launchers into ~/.local/bin/.
"""
from __future__ import annotations

import subprocess
from pathlib import Path

from modules.shared.src.taxonomy_core_error import ToolUpdateError
from modules.shared.src.taxonomy_xdg_paths import (
    bin_home,
    tool_cache_dir,
    tool_config_dir,
    tool_data_dir,
    tool_state_dir,
)
import contextlib
import shutil
import sys
from modules.shared.src.taxonomy_paths_constant import REPO_ROOT
from modules.shared.src.taxonomy_xdg_atomic_io import warn_if_bin_not_on_path
from modules.shared.src.taxonomy_xdg_paths import tool_data_dir

# --- inlined helper deps (self-contained, no utility-to-utility imports) ---
ROOT = REPO_ROOT

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

def ensure_venv(tool_name: str, force: bool = False) -> Path:
    """Create venv in XDG data directory. If force=True, recreate even if exists."""
    venv_dir = get_venv_dir(tool_name)
    python_bin = get_venv_python(venv_dir)

    if python_bin.exists():
        if not force:
            print(f"  [skip] Venv already exists at {venv_dir}")
            return python_bin
        print(f"  [update] Recreating venv at {venv_dir}...")
        import shutil
        shutil.rmtree(venv_dir)
    else:
        print(f"  [install] Creating venv at {venv_dir}...")

    subprocess.run([sys.executable, "-m", "venv", "--without-pip", str(venv_dir)], check=True)
    print("  [install] Bootstrapping pip...")
    subprocess.run([str(get_venv_python(venv_dir)), "-m", "ensurepip", "--upgrade"], check=True)
    python_bin = get_venv_python(venv_dir)
    print(f"  [ok] Venv created: {python_bin}")
    return python_bin

def install_package(python_bin: Path, src_dir: Path, tool_name: str) -> None:
    print(f"  [install] Installing {tool_name} package...")
    subprocess.run(
        [str(python_bin), "-m", "pip", "install", "-e", str(src_dir)],
        check=True,
    )

def setup_bin_links(python_bin: Path, launchers: list[tuple[str, str]]) -> None:
    """Create symlinks in ~/.local/bin/. launchers = [(name, entrypoint), ...]"""
    import contextlib
    ensure_bin_home()
    local_bin = bin_home()
    venv_bin_dir = python_bin.parent
    print(f"  [install] Creating launchers in {local_bin}...")
    for name, _entry in launchers:
        src = venv_bin_dir / name
        dst = local_bin / name
        if src.exists():
            if dst.is_symlink() or dst.exists():
                with contextlib.suppress(OSError):
                    dst.unlink()
            with contextlib.suppress(OSError):
                dst.symlink_to(src)
                print(f"  [ok] {dst} -> {src}")
    warn_if_bin_not_on_path()

def setup_xdg_directories(tool_name: str) -> None:
    print(f"  [install] Creating XDG directories for {tool_name}...")
    tool_data_dir(tool_name)
    tool_config_dir(tool_name)
    tool_state_dir(tool_name)
    tool_cache_dir(tool_name)
    print(f"  [ok] Data: {tool_data_dir(tool_name)}")
    print(f"  [ok] Config: {tool_config_dir(tool_name)}")
    print(f"  [ok] State: {tool_state_dir(tool_name)}")
    print(f"  [ok] Cache: {tool_cache_dir(tool_name)}")

def get_venv_dir(tool_name: str) -> Path:
    """XDG-compliant venv directory: ~/.local/share/<tool>/venv/"""
    return tool_data_dir(tool_name) / "venv"

def get_venv_python(venv_dir: Path) -> Path:
    return venv_dir / "bin" / "python"


TOOL_NAME = "qwen-web"
SRC_REL = f"internal/{TOOL_NAME}-arwaky"
LAUNCHERS = [
    ("qwen-web-arwaky", "qwen-web-arwaky"),
    ("qwa", "qwen-web-arwaky"),
    ("qwen-web-cli", "qwen-web-arwaky"),
    ("qwen-web-mcp", "qwen-web-mcp"),
    ("qwc", "qwen-web-arwaky"),
]


def _install_playwright(python_bin: Path) -> None:
    print("  [install] Installing Playwright Chromium...")
    subprocess.run([str(python_bin), "-m", "playwright", "install", "chromium"], check=True)


def _setup_qwen_web_dirs() -> None:
    data_dir = tool_data_dir(TOOL_NAME)
    state_dir = tool_state_dir(TOOL_NAME)
    cache_dir = tool_cache_dir(TOOL_NAME)
    for role in ("role-architect", "role-business-analyst", "role-tech-lead"):
        (data_dir / "input" / role / "done").mkdir(parents=True, exist_ok=True)
        (data_dir / "input" / role / "failed").mkdir(parents=True, exist_ok=True)
    (data_dir / "output").mkdir(parents=True, exist_ok=True)
    (data_dir / "qwen_session").mkdir(parents=True, exist_ok=True)
    (state_dir / "log").mkdir(parents=True, exist_ok=True)
    (cache_dir / ".processing").mkdir(parents=True, exist_ok=True)
    print(f"  [ok] Data: {data_dir}")
    print(f"  [ok] State: {state_dir}")
    print(f"  [ok] Cache: {cache_dir}")


class QwenWebAdapter:
    """Install/update internal/qwen-web-arwaky via a uv-managed venv + Playwright."""

    def satisfied(self, spec, root: Path | None = None) -> bool:
        return (bin_home() / "qwen-web-arwaky").exists()

    # -- install (from old installer adapter, verbatim mechanics) ----------------
    def install(self, spec, root: Path = ROOT, *, daemons=None) -> list[Path]:
        root = root or ROOT
        src_dir = root / SRC_REL

        print(">>> Installing qwen-web-arwaky (XDG compliant)...")
        if not ensure_source(root, SRC_REL):
            raise FileNotFoundError(f"source not found {src_dir}")

        python_bin = ensure_venv(TOOL_NAME, force=False)
        install_package(python_bin, src_dir, TOOL_NAME)
        _install_playwright(python_bin)
        _setup_qwen_web_dirs()
        setup_bin_links(python_bin, LAUNCHERS)

        print("\n>>> Successfully installed qwen-web-arwaky")
        print(f"    Venv: {python_bin.parent}")
        print(f"    Data: {tool_data_dir(TOOL_NAME)}")
        print("    Run 'qwc init' to setup workspace symlinks")
        return [python_bin]

    # -- update (from old updater adapter) ---------------------------------------
    def is_pin_satisfied(self, spec, root: Path) -> tuple[bool, str]:
        source = root / SRC_REL
        if not source.exists():
            return False, "submodule not initialized"
        return False, "venv/pip + Playwright (rebuild required)"

    def update(self, spec, root: Path) -> list[Path]:

        print(">>> Updating qwen-web-arwaky (XDG compliant)...")

        if not update_submodule(root, SRC_REL):
            raise ToolUpdateError(f"submodule update failed: {SRC_REL}")

        source = root / SRC_REL
        if not source.exists():
            raise ToolUpdateError(f"source not found {source}")

        python_bin = ensure_venv(TOOL_NAME, force=True)
        install_package(python_bin, source, TOOL_NAME)
        _install_playwright(python_bin)
        _setup_qwen_web_dirs()
        setup_bin_links(python_bin, LAUNCHERS)
        write_install_stamp(python_bin.parent.parent, TOOL_NAME, source)

        created = [bin_home() / name for name, _entry in LAUNCHERS]
        print("\n>>> Successfully updated qwen-web-arwaky")
        print(f"    Venv: {python_bin.parent}")
        print(f"    Data: {tool_data_dir(TOOL_NAME)}")
        return created

    # -- teardown data --------------------------------------------------------------
    def owned_paths(self, spec, root: Path | None = None) -> list[Path]:
        return generic_owned(
            spec,
            [name for name, _e in LAUNCHERS],
            extra=[tool_config_dir(TOOL_NAME), tool_state_dir(TOOL_NAME), tool_cache_dir(TOOL_NAME)],
        )
