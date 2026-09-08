"""XDG Base Directory helpers (Python) — pengganti tools/lib/xdg.sh.

Mengikuti freedesktop.org XDG Base Directory Specification:
    $XDG_DATA_HOME    -> ~/.local/share   (persistent data, per-tool)
    $XDG_CONFIG_HOME  -> ~/.config        (configuration, per-tool)
    $XDG_STATE_HOME   -> ~/.local/state   (state: PID files, history, logs)
    $XDG_CACHE_HOME   -> ~/.cache         (transient: build artifacts, caches)
    $XDG_RUNTIME_DIR  -> /run/user/<uid>  (sockets/private runtime, jika tersedia)
    $XDG_BIN_HOME     -> ~/.local/bin     (de-facto convention user binaries)

Semua helper bersifat pure (tanpa side effect) kecuali yang eksplisit
*_dir()/ensure_*(). Fallback default mengikuti spec resmi.
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
    """Return $XDG_RUNTIME_DIR jika terdefinisi dan writable, else None."""
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
    """True jika $XDG_BIN_HOME sudah ada di PATH proses ini."""
    return str(bin_home()) in os.environ.get("PATH", "").split(os.pathsep)


def ensure_path() -> None:
    """Prepend $XDG_BIN_HOME ke PATH proses berjalan (bukan shell persist)."""
    b = str(bin_home())
    ensure_bin_home()
    paths = os.environ.get("PATH", "").split(os.pathsep)
    if b not in paths:
        os.environ["PATH"] = b + os.pathsep + os.environ.get("PATH", "")


def warn_if_bin_not_on_path() -> bool:
    """Warn sekali jika $XDG_BIN_HOME tidak ada di PATH (berguna utk installer).

    Return True jika sudah on PATH (aman), False jika perlu ditambahkan user.
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
# agents-arwaky private config (secrets/env) — canonical + legacy
# ---------------------------------------------------------------------------
def agents_arwaky_config_dir() -> Path:
    """Canonical private config dir: $XDG_CONFIG_HOME/agents-arwaky.

    Menyimpan secret/env (.env) per tool dengan mode 0700.
    """
    p = config_home() / "agents-arwaky"
    p.mkdir(parents=True, exist_ok=True, mode=0o700)
    return p


def legacy_agents_arwaky_secret_dir() -> Path:
    """Lokasi lama ($XDG_DATA_HOME/agents-arwaky/config) utk backward-compat."""
    return data_home() / "agents-arwaky" / "config"


def agent_secret_candidates(tool: str, repo_config: Path | None = None) -> list[Path]:
    """Candidate env files utk sebuah tool: kanonik -> legacy -> repo config."""
    candidates = [
        agents_arwaky_config_dir() / f"{tool}.env",
        legacy_agents_arwaky_secret_dir() / f"{tool}.env",
    ]
    if repo_config is not None:
        candidates.append(repo_config)
    return candidates


# ---------------------------------------------------------------------------
# Uninstall helper (single source of truth utk semua uninstaller)
# ---------------------------------------------------------------------------
def remove_tool_artifacts(
    tool: str,
    launchers: list[str],
    *,
    clean_config: bool = True,
) -> None:
    """Hapus semua artifact XDG yang mungkin dibuat installer untuk tool.

    Menghapus: launcher + alias di bin, data, cache (termasuk build dir),
    dan (opsional) config dir. Tidak menyentuh $XDG_STATE_HOME.
    """
    for name in launchers:
        (bin_home() / name).unlink(missing_ok=True)
    shutil.rmtree(tool_data_path(tool), ignore_errors=True)
    shutil.rmtree(tool_cache_path(tool), ignore_errors=True)
    shutil.rmtree(cache_home() / "agents-arwaky" / f"build-{tool}", ignore_errors=True)
    if clean_config:
        shutil.rmtree(tool_config_path(tool), ignore_errors=True)
