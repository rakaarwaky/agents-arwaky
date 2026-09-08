"""XDG Base Directory helpers (Python) — replaces tools/lib/xdg.sh.

Follows freedesktop.org XDG Base Directory Specification:
    $XDG_DATA_HOME    -> ~/.local/share   (persistent data, per-tool)
    $XDG_CONFIG_HOME  -> ~/.config        (configuration, per-tool)
    $XDG_STATE_HOME   -> ~/.local/state   (state: PID files, history, logs)
    $XDG_CACHE_HOME   -> ~/.cache         (transient: build artifacts, caches)
    $XDG_RUNTIME_DIR  -> /run/user/<uid>  (sockets/private runtime, if available)
    $XDG_BIN_HOME     -> ~/.local/bin     (de-facto convention user binaries)

All helpers are pure (no side effects) except explicit
*_dir()/ensure_*(). Fallback defaults follow the official spec.
"""
from __future__ import annotations

import os
import shutil
import sys
from pathlib import Path


# ---------------------------------------------------------------------------
# Base directories (pure)
# ---------------------------------------------------------------------------
def data_home() -> Path:
    return Path(os.environ.get("XDG_DATA_HOME", str(Path.home() / ".local/share")))


def config_home() -> Path:
    return Path(os.environ.get("XDG_CONFIG_HOME", str(Path.home() / ".config")))


def state_home() -> Path:
    """$XDG_STATE_HOME, default ~/.local/state (resmi sejak spec 0.8)."""
    return Path(os.environ.get("XDG_STATE_HOME", str(Path.home() / ".local/state")))


def cache_home() -> Path:
    return Path(os.environ.get("XDG_CACHE_HOME", str(Path.home() / ".cache")))


def runtime_dir() -> Path | None:
    """Return $XDG_RUNTIME_DIR if defined and writable, else None."""
    raw = os.environ.get("XDG_RUNTIME_DIR")
    if raw:
        p = Path(raw)
        if p.is_dir() and os.access(p, os.W_OK):
            return p
    return None


def bin_home() -> Path:
    """User binary dir: $XDG_BIN_HOME, default ~/.local/bin (de-facto standard)."""
    return Path(os.environ.get("XDG_BIN_HOME", str(Path.home() / ".local/bin")))


# ---------------------------------------------------------------------------
# Side-effect helpers
# ---------------------------------------------------------------------------
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
        f"         Add it to your profile, e.g.:\n"
        f"           echo 'export PATH=\"$HOME/.local/bin:$PATH\"' >> ~/.bashrc\n",
        file=sys.stderr,
    )
    return False


# ---------------------------------------------------------------------------
# Per-tool path helpers (pure) + mkdir variants
# ---------------------------------------------------------------------------
def tool_data_path(tool: str) -> Path:
    return data_home() / tool


def tool_config_path(tool: str) -> Path:
    return config_home() / tool


def tool_state_path(tool: str) -> Path:
    return state_home() / tool


def tool_cache_path(tool: str) -> Path:
    return cache_home() / tool


def tool_data_dir(tool: str) -> Path:
    p = tool_data_path(tool)
    p.mkdir(parents=True, exist_ok=True)
    return p


def tool_config_dir(tool: str) -> Path:
    p = tool_config_path(tool)
    p.mkdir(parents=True, exist_ok=True)
    return p


def tool_state_dir(tool: str) -> Path:
    p = tool_state_path(tool)
    p.mkdir(parents=True, exist_ok=True)
    return p


def tool_cache_dir(tool: str) -> Path:
    p = tool_cache_path(tool)
    p.mkdir(parents=True, exist_ok=True)
    return p


# ---------------------------------------------------------------------------
# agents-arwaky private config (secrets/env)
# ---------------------------------------------------------------------------
def agents_arwaky_config_dir() -> Path:
    """Private config dir: $XDG_CONFIG_HOME/agents-arwaky.

    Stores secret/env (.env) per tool with mode 0700.
    """
    p = config_home() / "agents-arwaky"
    p.mkdir(parents=True, exist_ok=True, mode=0o700)
    return p


def agent_secret_candidates(tool: str, repo_config: Path | None = None) -> list[Path]:
    """Candidate env files utk sebuah tool: kanonik -> repo config."""
    candidates = [
        agents_arwaky_config_dir() / f"{tool}.env",
    ]
    if repo_config is not None:
        candidates.append(repo_config)
    return candidates


# ---------------------------------------------------------------------------
# Uninstall helper (single source of truth for all uninstallers)
# ---------------------------------------------------------------------------
def remove_tool_artifacts(
    tool: str,
    launchers: list[str],
    *,
    clean_config: bool = True,
) -> None:
    """Remove all XDG artifacts that installers may have created for a tool.

    Removes: launchers + aliases in bin, data, cache (including build dir),
    and (optionally) config dir. Does not touch $XDG_STATE_HOME.
    Also cleans up .venv in source directories (for uv-based tools).
    """
    for name in launchers:
        (bin_home() / name).unlink(missing_ok=True)
    shutil.rmtree(tool_data_path(tool), ignore_errors=True)
    shutil.rmtree(tool_cache_path(tool), ignore_errors=True)
    if clean_config:
        shutil.rmtree(tool_config_path(tool), ignore_errors=True)
    # Clean up .venv in source directories (uv-based tools)
    for src_dir in _find_source_dirs(tool):
        venv_path = src_dir / ".venv"
        if venv_path.is_symlink():
            venv_path.unlink(missing_ok=True)
        elif venv_path.is_dir():
            shutil.rmtree(venv_path, ignore_errors=True)


def _find_source_dirs(tool: str) -> list[Path]:
    """Find source directories for a tool (internal/ or vendor/)."""
    candidates = []
    internal_dir = Path(__file__).resolve().parents[1].parent / "internal" / f"{tool}-arwaky"
    if internal_dir.is_dir():
        candidates.append(internal_dir)
    vendor_dir = Path(__file__).resolve().parents[1].parent / "vendor" / tool
    if vendor_dir.is_dir():
        candidates.append(vendor_dir)
    return candidates


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
