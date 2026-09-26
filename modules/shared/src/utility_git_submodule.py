"""Git submodule helpers — domain-agnostic init/fetch/pull (utility).

Stateless subprocess helpers shared by the tools adapter, root CLI entry,
and tools surface command (≥2 consumers). Taxonomy-only imports.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from modules.shared.src.taxonomy_tools_constant import FALLBACK_REMOTE_BRANCHES


def run_quiet(cmd: list[str], cwd: Path | None = None) -> subprocess.CompletedProcess:
    """Run a command silently, return result."""
    return subprocess.run(cmd, cwd=cwd, check=False, capture_output=True, text=True)


def get_current_commit(submodule_dir: Path) -> str | None:
    """Get current HEAD commit hash of a submodule."""
    r = run_quiet(["git", "rev-parse", "HEAD"], cwd=submodule_dir)
    return r.stdout.strip() if r.returncode == 0 else None


def get_remote_default_branch(submodule_dir: Path) -> str | None:
    """Detect the default branch of the remote (main, master, etc.)."""
    r = run_quiet(["git", "remote", "show"], cwd=submodule_dir)
    if r.returncode != 0 or not r.stdout.strip():
        return None
    remote = r.stdout.strip().split("\n")[0]
    r2 = run_quiet(["git", "symbolic-ref", f"refs/remotes/{remote}/HEAD"], cwd=submodule_dir)
    if r2.returncode == 0:
        ref = r2.stdout.strip()
        parts = ref.split("/")
        if len(parts) >= 4:
            return parts[-1]
    for branch in FALLBACK_REMOTE_BRANCHES:
        r3 = run_quiet(
            ["git", "rev-parse", "--verify", f"refs/remotes/{remote}/{branch}"],
            cwd=submodule_dir,
        )
        if r3.returncode == 0:
            return branch
    return None


def fetch_remote(submodule_dir: Path) -> bool:
    """Fetch latest from remote. Returns True if successful."""
    return run_quiet(["git", "fetch", "--quiet"], cwd=submodule_dir).returncode == 0


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
    # NOTE: `--count` is a rev-list flag, not a log flag.
    r = run_quiet(["git", "rev-list", "--count", f"{local}..{remote_commit}"], cwd=submodule_dir)
    if r.returncode == 0 and r.stdout.strip() not in ("", "0"):
        return True, local, remote_commit
    mb = run_quiet(["git", "merge-base", local, remote_commit], cwd=submodule_dir)
    if mb.returncode == 0 and mb.stdout.strip() == local:
        return True, local, remote_commit
    return False, local, remote_commit


def pull_submodule(submodule_dir: Path) -> bool:
    """Pull latest commits for the submodule. Returns True if successful."""
    branch = get_remote_default_branch(submodule_dir) or "main"
    return run_quiet(["git", "checkout", f"origin/{branch}"], cwd=submodule_dir).returncode == 0


def init_submodules(root: Path, paths: tuple[str, ...], *, recursive: bool = False) -> int:
    """`git submodule update --init` for *paths* under *root*. Returns exit code."""
    cmd = ["git", "-C", str(root), "submodule", "update", "--init"]
    if recursive:
        cmd.append("--recursive")
    cmd.extend(paths)
    return subprocess.run(cmd, check=False).returncode


def update_submodule(root: Path, submodule_path: str) -> bool:
    """Full update workflow: fetch, check, pull a submodule."""
    submodule_dir = root / submodule_path
    if not submodule_dir.exists() or not (submodule_dir / ".git").exists():
        r = run_quiet(
            ["git", "-C", str(root), "submodule", "update", "--init", submodule_path],
        )
        return r.returncode == 0
    if not fetch_remote(submodule_dir):
        print(f"  Warning: fetch failed for {submodule_path}", file=sys.stderr)
        return False
    has_updates, local, remote = has_newer_commits(submodule_dir)
    short_local = (local[:8] + "...") if local and len(local) > 8 else local
    if not has_updates:
        print(f"  [skip] {submodule_path} is up to date ({short_local})")
        return True
    short_remote = (remote[:8] + "...") if remote and len(remote) > 8 else remote
    print(f"  [update] {submodule_path}: {short_local} -> {short_remote}")
    if pull_submodule(submodule_dir):
        print(f"  [ok] {submodule_path} updated successfully")
        return True
    print(f"  Warning: pull failed for {submodule_path}", file=sys.stderr)
    return False


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


__all__ = [
    "ensure_source",
    "fetch_remote",
    "get_current_commit",
    "get_remote_default_branch",
    "has_newer_commits",
    "init_submodules",
    "pull_submodule",
    "run_quiet",
    "update_submodule",
]
