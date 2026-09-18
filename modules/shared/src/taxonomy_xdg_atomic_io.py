"""Side-effect XDG I/O helpers, split out from tools/lib/xdg.py.\n\nDepends on ``modules.shared.src.taxonomy_xdg_paths`` for the pure helpers.\n"""
from __future__ import annotations

import os
import shutil
import sys
from pathlib import Path

from modules.shared.src.taxonomy_xdg_paths import (
    bin_home,
    tool_cache_dir,
    tool_config_dir,
    tool_data_dir,
)


def ensure_bin_home() -> None:
    bin_home().mkdir(parents=True, exist_ok=True)


def bin_on_path() -> bool:
    """True if $XDG_BIN_HOME is already on this process's PATH."""
    return str(bin_home()) in os.environ.get("PATH", "").split(os.pathsep)


def ensure_path() -> None:
    """Prepend $XDG_BIN_HOME to current process PATH (not persistent shell)."""
    b = str(bin_home())
    ensure_bin_home()
    paths = os.environ.get("PATH", "").split(os.pathsep)
    if b not in paths:
        os.environ["PATH"] = b + os.pathsep + os.environ.get("PATH", "")


def warn_if_bin_not_on_path() -> bool:
    """Warn once if $XDG_BIN_HOME is not on PATH (useful for installers).

    Return True if already on PATH (safe), False if user needs to add it.
    """
    if bin_on_path():
        return True
    print(
        f"  [WARN] {bin_home()} is not on your PATH.\n"
        f"         Launchers installed there won't be found by your shell.\n"
        f"         Add it to your profile, e.g.:\\n"
        f"           echo 'export PATH=\\\"$HOME/.local/bin:$PATH\\\"' >> ~/.bashrc\\n",
        file=sys.stderr,
    )
    return False


def remove_tool_artifacts(
    tool: str,
    launchers: list[str],
    *,
    clean_config: bool = True,
) -> None:
    """Remove all XDG artifacts that installers may have created for a tool.

    Removes: launchers + aliases in bin, data, cache (including build dir),
    and (optionally) config dir. Does not touch $XDG_STATE_HOME.
    Also cleans up .venv and target/ in source directories.
    """
    for name in launchers:
        (bin_home() / name).unlink(missing_ok=True)
    shutil.rmtree(tool_data_dir(tool), ignore_errors=True)
    shutil.rmtree(tool_cache_dir(tool), ignore_errors=True)
    if clean_config:
        shutil.rmtree(tool_config_dir(tool), ignore_errors=True)
    # Clean up build artifacts in source directories — only safe dirs
    source_candidates = [
        Path.home() / "projects" / tool,
        Path.home() / "src" / tool,
    ]
    for src_dir in source_candidates:
        if not src_dir.exists():
            continue
        # Clean .venv (uv-based Python tools)
        venv_path = src_dir / ".venv"
        if venv_path.is_symlink():
            venv_path.unlink(missing_ok=True)
        elif venv_path.is_dir():
            shutil.rmtree(venv_path, ignore_errors=True)
        # Clean target/ (Rust cargo tools)
        target_path = src_dir / "target"
        if target_path.is_dir():
            shutil.rmtree(target_path, ignore_errors=True)


def atomic_write_text(path: Path, content: str, mode: int = 0o755) -> None:
    """Atomically write file (temp + os.replace).

    Avoids ETXTBSY ('Text file busy') when overwriting an executable
    that is currently running: rename is safe because the old process
    still holds the old inode.
    """
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(content, encoding="utf-8")
    tmp.chmod(mode)
    os.replace(tmp, path)
