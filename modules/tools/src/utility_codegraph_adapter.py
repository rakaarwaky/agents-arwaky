"""Codegraph adapter (npm) — unified install + update + teardown.

@colbymchenry/codegraph is a TypeScript project built with npm. Lockfile
package-lock.json -> `npm ci`; build `npm run build` (tsc + copy-assets +
build:ui) produces dist/bin/codegraph.js. Launchers codegraph-mcp &
codegraph both point at dist/bin/codegraph.js (tool dispatches mode via args).

Stateless leaf (AES404): module-level functions only, no classes.
"""
from __future__ import annotations

from pathlib import Path

from modules.shared.src.taxonomy_core_error import ToolUpdateError
from modules.shared.src.taxonomy_xdg_paths import bin_home, data_home

# --- inlined helper dependencies (self-contained; AES404: no utility-to-utility imports) ---
import shutil
import subprocess
import sys
from modules.shared.src.taxonomy_paths_constant import PROVENANCE_MARKER
from modules.shared.src.taxonomy_xdg_atomic_io import atomic_write_text, ensure_bin_home, ensure_path, warn_if_bin_not_on_path
from modules.shared.src.taxonomy_xdg_atomic_io import ensure_bin_home
from modules.shared.src.taxonomy_xdg_atomic_io import ensure_bin_home, warn_if_bin_not_on_path
from modules.shared.src.taxonomy_xdg_paths import bin_home
from modules.shared.src.taxonomy_xdg_paths import cache_home, config_home
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

NODE_IGNORES = [
    "node_modules", ".git", "__pycache__", "target", "*.egg-info",
    ".venv", "venv", "*.tsbuildinfo",
]

from modules.shared.src.taxonomy_paths_constant import REPO_ROOT

ROOT = REPO_ROOT

def copy_app(src: Path, app_dir: Path, ignore_patterns: list[str]) -> None:
    """Replace *app_dir* with a copy of *src*, dropping the listed patterns."""
    ignore = shutil.ignore_patterns(*ignore_patterns)
    if app_dir.exists():
        shutil.rmtree(app_dir)
    shutil.copytree(src, app_dir, ignore=ignore)

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

def finish_bin() -> None:
    """Ensure bin home + PATH warning after launcher writes."""
    ensure_bin_home()
    warn_if_bin_not_on_path()

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

def require(tool: str, reason: str = "") -> bool:
    """True when *tool* is on PATH; otherwise print the missing-tool diagnostic."""
    if shutil.which(tool):
        return True
    print(f"Error: {tool} not found in PATH. {reason}", file=sys.stderr)
    return False

def run(cmd: list[str], cwd: Path | str | None = None) -> None:
    """Run with check=True; raises subprocess.CalledProcessError on failure."""
    subprocess.run(cmd, cwd=str(cwd) if cwd else None, check=True)

def write_node_launcher(name: str, entry: Path) -> Path:
    """Write a node entry launcher via the shared launcher writer."""
    # inlined: write_node_entry_launcher is defined below in this same file
    launcher = write_node_entry_launcher(name, entry)
    print(f"  -> {launcher}")
    return launcher

def write_node_entry_launcher(name: str, entry: Path, aliases: list[str] | None = None) -> Path:
    """Write a launcher that execs `node <entry>` in XDG bin. Returns launcher path."""
    content = (
        "#!/usr/bin/env python3\n"
        f"# {PROVENANCE_MARKER}\n"
        "import os, sys\n"
        f'entry = r"{entry}"\n'
        'os.execvpe("node", ["node", entry, *sys.argv[1:]], os.environ.copy())\n'
    )
    return write_generic_launcher(name, content, aliases=aliases)

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

SRC_REL = "vendor/codegraph"
ENTRY = "dist/bin/codegraph.js"
LAUNCHERS = ["codegraph-mcp", "codegraph"]


def satisfied(spec, root: Path | None = None) -> bool:
    return (bin_home() / "codegraph-mcp").exists()


# -- install (from old installer adapter, verbatim mechanics) ----------------
def install(spec, root: Path = ROOT, *, daemons=None) -> list[Path]:
    root = root or ROOT
    src = ensure_source(root, SRC_REL)
    if not (src / "package.json").exists():
        raise FileNotFoundError(f"codegraph source not found (submodule not initialized): {src}")
    if not require("npm", "codegraph requires npm (https://nodejs.org)"):
        raise FileNotFoundError("npm is required (https://nodejs.org).")

    app_dir = data_home() / "codegraph"
    print(f">>> Installing codegraph into {app_dir}...")
    copy_app(src, app_dir, NODE_IGNORES)

    run(["npm", "ci", "--no-audit", "--no-fund"], app_dir)
    run(["npm", "run", "build"], app_dir)

    entry = app_dir / ENTRY
    if not entry.exists():
        raise FileNotFoundError(f"entry not found {entry}")

    # codegraph-mcp + codegraph both forward to the same entry binary.
    artifacts = [write_node_launcher(LAUNCHERS[0], entry)]
    artifacts += [symlink_alias(name, bin_home() / LAUNCHERS[0]) for name in LAUNCHERS[1:]]
    finish_bin()
    print(">>> Successfully installed codegraph")
    return artifacts


# -- update (from old updater adapter) ---------------------------------------
def is_pin_satisfied(spec, root: Path) -> tuple[bool, str]:
    source = root / SRC_REL
    if not source.exists():
        return False, "submodule not initialized"
    return False, "npm workspace (rebuild required)"


def update(spec, root: Path) -> list[Path]:

    source = root / SRC_REL
    if not update_submodule(root, SRC_REL):
        raise ToolUpdateError(f"submodule update failed: {SRC_REL}")
    if not (source / "package.json").exists():
        raise ToolUpdateError("codegraph source not found (submodule not initialized)")
    if not require("npm", "codegraph requires npm (https://nodejs.org)"):
        raise ToolUpdateError("codegraph requires npm (https://nodejs.org)")

    app_dir = data_home() / "codegraph"
    print(f">>> Updating codegraph into {app_dir}...")
    copy_app(source, app_dir, NODE_IGNORES)
    run(["npm", "ci", "--no-audit", "--no-fund"], app_dir)
    run(["npm", "run", "build"], app_dir)

    entry = app_dir / ENTRY
    if not entry.exists():
        raise ToolUpdateError(f"entry not found {entry}")

    created = [write_node_launcher(LAUNCHERS[0], entry)]
    created += [symlink_alias(name, bin_home() / LAUNCHERS[0]) for name in LAUNCHERS[1:]]
    finish_bin()
    print(">>> Successfully updated codegraph")
    return created


# -- teardown data --------------------------------------------------------------
def owned_paths(spec, root: Path | None = None) -> list[Path]:
    return generic_owned(spec, LAUNCHERS)
