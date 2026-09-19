"""Blender-arwaky adapter (uv venv) — unified install + update + teardown.

Creates venv in ~/.local/share/blender-arwaky/venv/ and symlinks to
~/.local/bin/. Update rebuilds the venv in place and re-stamps the install.

Stateless leaf (AES404): module-level functions only, no classes.
"""
from __future__ import annotations

from pathlib import Path

from modules.shared.src.taxonomy_core_error import ToolUpdateError
from modules.shared.src.taxonomy_xdg_paths import bin_home, tool_data_dir

# --- inlined helper dependencies (self-contained; AES404: no utility-to-utility imports) ---
import contextlib
import shutil
import subprocess
import sys
from modules.shared.src.taxonomy_xdg_atomic_io import warn_if_bin_not_on_path
from modules.shared.src.taxonomy_xdg_paths import bin_home
from modules.shared.src.taxonomy_xdg_paths import tool_cache_dir, tool_config_dir, tool_data_dir, tool_state_dir
from modules.shared.src.taxonomy_xdg_paths import tool_data_dir

from modules.shared.src.taxonomy_paths_constant import REPO_ROOT
# --- inlined git-update helpers (self-contained, no utility-to-utility imports) ---
import datetime
import json

def run_quiet(cmd: list[str], cwd: Path | None = None) -> subprocess.CompletedProcess:
    """Run a command silently, return result."""
    return subprocess.run(
        cmd, cwd=cwd, check=False,
        capture_output=True, text=True,
    )

def get_current_commit(submodule_dir: Path) -> str | None:
    """Get current HEAD commit hash of a submodule."""
    r = run_quiet(["git", "rev-parse", "HEAD"], cwd=submodule_dir)
    if r.returncode == 0:
        return r.stdout.strip()
    return None

def get_remote_default_branch(submodule_dir: Path) -> str | None:
    """Detect the default branch of the remote (main, master, etc.)."""
    r = run_quiet(["git", "remote", "show"], cwd=submodule_dir)
    if r.returncode != 0 or not r.stdout.strip():
        return None
    remote = r.stdout.strip().split("\n")[0]
    r2 = run_quiet(["git", "symbolic-ref", f"refs/remotes/{remote}/HEAD"], cwd=submodule_dir)
    if r2.returncode == 0:
        ref = r2.stdout.strip()
        # refs/remotes/origin/main -> main
        parts = ref.split("/")
        if len(parts) >= 4:
            return parts[-1]
    # Fallback: try common names
    for branch in ("main", "master", "dev"):
        r3 = run_quiet(["git", "rev-parse", "--verify", f"refs/remotes/{remote}/{branch}"], cwd=submodule_dir)
        if r3.returncode == 0:
            return branch
    return None

def fetch_remote(submodule_dir: Path) -> bool:
    """Fetch latest from remote. Returns True if successful."""
    r = run_quiet(["git", "fetch", "--quiet"], cwd=submodule_dir)
    return r.returncode == 0

def has_newer_commits(submodule_dir: Path) -> tuple[bool, str | None, str | None]:
    """Check if remote has newer commits than local.

    Returns:
        (has_updates, local_commit, remote_commit)
    """
    local = get_current_commit(submodule_dir)
    if not local:
        return False, None, None

    branch = get_remote_default_branch(submodule_dir)
    if not branch:
        return False, local, None

    remote = run_quiet(["git", "rev-parse", f"origin/{branch}"], cwd=submodule_dir)
    if remote.returncode != 0:
        return False, local, None

    remote_commit = remote.stdout.strip()
    if remote_commit == local:
        return False, local, remote_commit

    # Check if remote is ahead
    r = run_quiet(
        ["git", "log", "--oneline", f"{local}..{remote_commit}", "--count"],
        cwd=submodule_dir,
    )
    if r.returncode == 0 and r.stdout.strip():
        return True, local, remote_commit

    # Fallback: use merge-base
    mb = run_quiet(["git", "merge-base", local, remote_commit], cwd=submodule_dir)
    if mb.returncode == 0 and mb.stdout.strip() == local:
        return True, local, remote_commit

    return False, local, remote_commit

def pull_submodule(submodule_dir: Path) -> bool:
    """Pull latest commits for the submodule. Returns True if successful."""
    branch = get_remote_default_branch(submodule_dir)
    if not branch:
        branch = "main"

    r = run_quiet(["git", "checkout", f"origin/{branch}"], cwd=submodule_dir)
    return r.returncode == 0

def update_submodule(repo_root: Path, submodule_path: str) -> bool:
    """Full update workflow: fetch, check, pull a submodule.

    Args:
        repo_root: Root of the main repository
        submodule_path: Path relative to repo root (e.g. "internal/vision-arwaky")

    Returns:
        True if updated (or already latest), False on error.
    """
    submodule_dir = repo_root / submodule_path
    if not submodule_dir.exists() or not (submodule_dir / ".git").exists():
        # Not initialized yet, init first
        r = run_quiet(
            ["git", "-C", str(repo_root), "submodule", "update", "--init", submodule_path],
        )
        return r.returncode == 0

    # Fetch latest
    if not fetch_remote(submodule_dir):
        print(f"  Warning: fetch failed for {submodule_path}", file=sys.stderr)
        return False

    has_updates, local, remote = has_newer_commits(submodule_dir)
    if not has_updates:
        short_local = (local[:8] + "...") if local and len(local) > 8 else local
        print(f"  [skip] {submodule_path} is up to date ({short_local})")
        return True

    short_local = (local[:8] + "...") if local and len(local) > 8 else local
    short_remote = (remote[:8] + "...") if remote and len(remote) > 8 else remote
    print(f"  [update] {submodule_path}: {short_local} -> {short_remote}")

    if pull_submodule(submodule_dir):
        print(f"  [ok] {submodule_path} updated successfully")
        return True
    else:
        print(f"  Warning: pull failed for {submodule_path}", file=sys.stderr)
        return False

def write_install_stamp(app_dir: Path, tool: str, submodule_dir: Path) -> None:
    """Record what was deployed so rollback/audit is possible.

    Writes .arwaky-install.json to the app directory with:
    - tool name
    - commit SHA
    - timestamp
    """
    commit = get_current_commit(submodule_dir)
    stamp = {
        "tool": tool,
        "commit": commit or "unknown",
        "installed_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
    }
    try:
        app_dir.mkdir(parents=True, exist_ok=True)
        (app_dir / ".arwaky-install.json").write_text(
            json.dumps(stamp, indent=2) + "\n", encoding="utf-8"
        )
    except OSError as exc:
        print(f"  Warning: could not write install stamp: {exc}", file=sys.stderr)

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

TOOL_NAME = "blender-arwaky"
SRC_REL = f"internal/{TOOL_NAME}"
LAUNCHERS = [("blender-arwaky", "blender-arwaky"), ("ba", "blender-arwaky"), ("blender-mcp", "blender-mcp")]


def satisfied(spec, root: Path | None = None) -> bool:
    return (bin_home() / "blender-arwaky").exists()


# -- install (from old installer adapter, verbatim mechanics) ----------------
def install(spec, root: Path = ROOT, *, daemons=None) -> list[Path]:
    root = root or ROOT
    src_dir = root / SRC_REL

    if not ensure_source(root, SRC_REL):
        raise FileNotFoundError(f"source not found {src_dir}")

    python_bin = ensure_venv(TOOL_NAME, force=False)
    install_package(python_bin, src_dir, TOOL_NAME)
    setup_xdg_directories(TOOL_NAME)
    setup_bin_links(python_bin, LAUNCHERS)

    print("\n>>> Successfully installed blender-arwaky")
    print(f"    Venv: {python_bin.parent}")
    print(f"    Data: {tool_data_dir(TOOL_NAME)}")
    print("    Run 'blender-arwaky init' to setup workspace symlinks")
    return [python_bin]


# -- update (from old updater adapter) ---------------------------------------
def is_pin_satisfied(spec, root: Path) -> tuple[bool, str]:
    source = root / SRC_REL
    if not source.exists():
        return False, "submodule not initialized"
    return False, "venv/pip (rebuild required)"


def update(spec, root: Path) -> list[Path]:

    print(f">>> Updating {TOOL_NAME} (XDG compliant)...")

    if not update_submodule(root, SRC_REL):
        raise ToolUpdateError(f"submodule update failed: {SRC_REL}")

    source = root / SRC_REL
    if not source.exists():
        raise ToolUpdateError(f"source not found {source}")

    python_bin = ensure_venv(TOOL_NAME, force=True)
    install_package(python_bin, source, TOOL_NAME)
    setup_xdg_directories(TOOL_NAME)
    setup_bin_links(python_bin, LAUNCHERS)
    write_install_stamp(python_bin.parent.parent, TOOL_NAME, source)

    created = [bin_home() / name for name, _entry in LAUNCHERS]
    print(f"\n>>> Successfully updated {TOOL_NAME}")
    print(f"    Venv: {python_bin.parent}")
    print(f"    Data: {tool_data_dir(TOOL_NAME)}")
    return created


# -- teardown data --------------------------------------------------------------
def owned_paths(spec, root: Path | None = None) -> list[Path]:
    return generic_owned(spec, [name for name, _e in LAUNCHERS])
