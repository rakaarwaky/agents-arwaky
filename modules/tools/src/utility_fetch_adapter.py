"""Fetch-mcp adapter (bun) — unified install + update + teardown.

zcaceres/fetch-mcp is a TypeScript project built with bun. Output:
  - dist/index.js -> MCP server (fetch-mcp, mcp-fetch)
  - dist/cli.js   -> CLI mode (html/markdown/readable/txt/json/youtube/...)
The launcher dispatches CLI vs MCP based on the first argument.

Stateless leaf (AES404): module-level functions only, no classes.
"""
from __future__ import annotations

from pathlib import Path

from modules.shared.src.taxonomy_core_error import ToolUpdateError
from modules.shared.src.taxonomy_paths_constant import PROVENANCE_MARKER
from modules.shared.src.taxonomy_xdg_atomic_io import (
    ensure_bin_home,
    warn_if_bin_not_on_path,
)
from modules.shared.src.taxonomy_xdg_paths import bin_home, data_home

# --- inlined helper dependencies (self-contained; AES404: no utility-to-utility imports) ---
import shutil
import subprocess
import sys
from modules.shared.src.taxonomy_xdg_paths import bin_home

from modules.shared.src.taxonomy_paths_constant import REPO_ROOT
# --- inlined git-update helpers (self-contained, no utility-to-utility imports) ---
import subprocess

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

SRC_REL = "vendor/fetch-mcp"
APP_DIR = data_home() / "fetch-mcp"

# First argument meaning "CLI mode" -> run dist/cli.js, otherwise MCP.
CLI_ARGS = {"html", "markdown", "readable", "txt", "json", "youtube", "--help", "-h", "--version", "-v"}

IGNORES = [
    "node_modules", ".git", "__pycache__", "target", "*.egg-info",
    ".venv", "venv", "*.tsbuildinfo",
]


def _write_launchers() -> list[Path]:
    """Write the CLI/MCP dispatch launchers (shared by install and update)."""
    index_js = APP_DIR / "dist/index.js"
    cli_js = APP_DIR / "dist/cli.js"
    ensure_bin_home()
    content = (
        "#!/usr/bin/env python3\n"
        f"# {PROVENANCE_MARKER}\n"
        "import os, sys\n"
        f'index_js = r"{index_js}"\n'
        f'cli_js = r"{cli_js}"\n'
        "cli = " + repr(sorted(CLI_ARGS)) + "\n"
        "script = cli_js if (len(sys.argv) > 1 and sys.argv[1] in cli) else index_js\n"
        'env = os.environ.copy()\n'
        'os.execvpe("node", ["node", script, *sys.argv[1:]], env)\n'
    )
    artifacts = []
    for name in ("fetch-mcp", "mcp-fetch"):
        launcher = bin_home() / name
        launcher.write_text(content, encoding="utf-8")
        launcher.chmod(0o755)
        artifacts.append(launcher)
        print(f"  -> {launcher}")
    warn_if_bin_not_on_path()
    return artifacts


def satisfied(spec, root: Path | None = None) -> bool:
    return (bin_home() / "fetch-mcp").exists()


# -- install (from old installer adapter, verbatim mechanics) ----------------
def install(spec, root: Path = ROOT, *, daemons=None) -> list[Path]:
    root = root or ROOT
    src = ensure_source(root, SRC_REL)
    if not (src / "package.json").exists():
        raise FileNotFoundError(f"fetch-mcp source not found (submodule not initialized): {src}")
    if not require("bun", "fetch-mcp requires bun (curl -fsSL https://bun.sh/install | bash)"):
        raise FileNotFoundError("bun is required (curl -fsSL https://bun.sh/install | bash).")

    print(f">>> Installing fetch-mcp into {APP_DIR}...")
    copy_app(src, APP_DIR, IGNORES)

    run(["bun", "install", "--frozen-lockfile"], APP_DIR)
    run(["bun", "run", "build"], APP_DIR)

    if not (APP_DIR / "dist/index.js").exists() or not (APP_DIR / "dist/cli.js").exists():
        raise FileNotFoundError(f"build output incomplete ({APP_DIR / 'dist/index.js'}, {APP_DIR / 'dist/cli.js'})")

    artifacts = _write_launchers()
    print(">>> Successfully installed fetch-mcp")
    return artifacts


# -- update (from old updater adapter) ---------------------------------------
def is_pin_satisfied(spec, root: Path) -> tuple[bool, str]:
    source = root / SRC_REL
    if not source.exists():
        return False, "submodule not initialized"
    return False, "bun workspace (rebuild required)"


def update(spec, root: Path) -> list[Path]:

    source = root / SRC_REL
    if not update_submodule(root, SRC_REL):
        raise ToolUpdateError(f"submodule update failed: {SRC_REL}")
    if not (source / "package.json").exists():
        raise ToolUpdateError("fetch-mcp source not found (submodule not initialized)")
    if not require("bun", "fetch-mcp requires bun (curl -fsSL https://bun.sh/install | bash)"):
        raise ToolUpdateError("fetch-mcp requires bun (curl -fsSL https://bun.sh/install | bash)")

    print(f">>> Updating fetch-mcp into {APP_DIR}...")
    copy_app(source, APP_DIR, IGNORES)
    run(["bun", "install", "--frozen-lockfile"], APP_DIR)
    run(["bun", "run", "build"], APP_DIR)

    if not (APP_DIR / "dist/index.js").exists() or not (APP_DIR / "dist/cli.js").exists():
        raise ToolUpdateError(f"build output incomplete ({APP_DIR / 'dist/index.js'}, {APP_DIR / 'dist/cli.js'})")

    created = _write_launchers()
    print(">>> Successfully updated fetch-mcp")
    return created


# -- teardown data --------------------------------------------------------------
def owned_paths(spec, root: Path | None = None) -> list[Path]:
    return generic_owned(spec, ["fetch-mcp", "mcp-fetch"])
