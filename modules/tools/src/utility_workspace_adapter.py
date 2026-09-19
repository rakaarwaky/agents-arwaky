"""Workspace (google-workspace-mcp) adapter (uv) — unified install + update + teardown.

vendor/google-workspace-mcp is a Python package run via `uv run` (no venv copy).
Launchers `workspace-mcp` and `google-workspace-mcp` both point at the same entry.

Stateless leaf (AES404): module-level functions only, no classes.
"""
from __future__ import annotations

from pathlib import Path

from modules.shared.src.taxonomy_core_error import ToolUpdateError

# --- inlined helper deps (self-contained, no utility-to-utility imports) ---
import subprocess
from modules.shared.src.taxonomy_paths_constant import PROVENANCE_MARKER
from modules.shared.src.taxonomy_paths_constant import PROVENANCE_MARKER, REPO_ROOT as repo_root
from modules.shared.src.taxonomy_xdg_atomic_io import atomic_write_text, ensure_bin_home, ensure_path, warn_if_bin_not_on_path
from modules.shared.src.taxonomy_xdg_atomic_io import ensure_bin_home
# --- inlined git-update helpers (self-contained, no utility-to-utility imports) ---

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

def symlink_alias(alias: str, target: Path) -> Path:
    """Symlink *alias* in XDG bin pointing at *target* (idempotent)."""
    ensure_bin_home()
    a = bin_home() / alias
    a.unlink(missing_ok=True)
    a.symlink_to(target)
    return a

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

from modules.shared.src.taxonomy_paths_constant import REPO_ROOT

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

def write_generic_launcher(tool_name: str, content: str, aliases: list[str] | None = None) -> Path:
    """Write a generic launcher with aliases. Returns launcher path."""
    ensure_bin_home()
    launcher = bin_home() / tool_name
    atomic_write_text(launcher, content)
    for alias in (aliases or []):
        a = bin_home() / alias
        a.unlink(missing_ok=True)
        a.symlink_to(launcher)
    warn_if_bin_not_on_path()
    ensure_path()
    return launcher

SRC_REL = "vendor/google-workspace-mcp"
LAUNCHERS = [
    ("workspace-mcp", "workspace-mcp"),
    ("google-workspace-mcp", "workspace-mcp"),
]


def _write_launchers(root: Path) -> list[Path]:
    created = write_uv_launchers(SRC_REL, LAUNCHERS[:1], root=root)
    for p in created:
        print(f"  -> {p}")
    # google-workspace-mcp is a PATH alias for workspace-mcp.
    alias = symlink_alias(LAUNCHERS[1][0], created[0])
    print(f"  -> {alias}")
    created.append(alias)
    return created


def satisfied(spec, root: Path | None = None) -> bool:
    from modules.shared.src.taxonomy_xdg_paths import bin_home
    return (bin_home() / "workspace-mcp").exists()


# -- install (from old installer adapter, verbatim mechanics) ----------------
def install(spec, root: Path = ROOT, *, daemons=None) -> list[Path]:
    root = root or ROOT
    src_dir = root / SRC_REL

    if not ensure_source(root, SRC_REL):
        raise FileNotFoundError(f"source not found {src_dir}")

    created = _write_launchers(root)
    print(">>> Successfully installed google-workspace-mcp")
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
    print(">>> Successfully updated google-workspace-mcp")
    return created


# -- teardown data --------------------------------------------------------------
def owned_paths(spec, root: Path | None = None) -> list[Path]:
    return generic_owned(spec, ["workspace-mcp", "google-workspace-mcp"])
