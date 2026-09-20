"""Shared per-tool adapter mechanics (P1-7 dedup) — stateless utility helpers.

Centralizes the git-submodule update block, XDG owned-set helper,
install-stamp writer, and submodule source-init that were inlined into
every `utility_*_adapter.py` under `modules/tools` (the 9 AES305
duplicate-code violations). The `capabilities_tools_adapter` facade
imports this module instead of re-inlining ~150 lines each.

Layer note (AES201): a `utility` file may not import another `utility`
file, so adapters (leaf utility modules) never import this module
directly; the `capability` layer *is* allowed to import `utility`,
which is why the dedup path that satisfies AES201 routes through
`capabilities_tools_adapter` (which imports this module) plus a
`contract_tools_adapter_protocol` ABC; the capability is wired by the
root container and injected. This module itself stays a leaf (imports
`taxonomy` only, as `utility` files must) and defines stateless
module-level functions only (AES404: no classes in the utility layer).

The git-update functions are a verbatim mirror of
`modules/shared/src/utility_git_update.py`; `has_newer_commits` was also
fixed in one place here: the original inlined copies called
`git log --oneline <a>..<b> --count`, but `--count` is not a `log`
flag (it is a `rev-list` flag), so that check never matched and the
fallback path was always used. The consolidated function uses
`git rev-list --count` so the fast path works.
"""
from __future__ import annotations

import datetime
import json
import subprocess
import sys
from pathlib import Path

from modules.shared.src.taxonomy_paths_constant import REPO_ROOT
from modules.shared.src.taxonomy_xdg_paths import bin_home, cache_home, config_home, data_home

#: Repo root, used as the default for git operations (taxonomy constant
#: so the utility layer stays AES201-legal).
ROOT: Path = REPO_ROOT

# ── Git submodule update block (verbatim mirror of utility_git_update) ─


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

    # Check if remote is ahead (P1-7: `--count` is a rev-list flag, not a log flag).
    r = run_quiet(
        ["git", "rev-list", "--count", f"{local}..{remote_commit}"],
        cwd=submodule_dir,
    )
    if r.returncode == 0 and r.stdout.strip() not in ("", "0"):
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


# ── Install stamp / source-init / owned-set helpers ────────────────────


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
    paths: list[Path] = [bin_home() / name for name in launcher_names]
    paths.append(data_home() / spec.id)
    paths.append(cache_home() / spec.id)
    for name in config or []:
        paths.append(config_home() / name)
    paths.extend(extra or [])
    return paths


__all__ = [
    "ROOT",
    "run_quiet",
    "get_current_commit",
    "get_remote_default_branch",
    "fetch_remote",
    "has_newer_commits",
    "pull_submodule",
    "update_submodule",
    "write_install_stamp",
    "ensure_source",
    "generic_owned",
]
