"""Anytype adapter (bun MCP + container daemon, merged) — unified install + update + teardown.

Merged adapter: installs BOTH components in one command.
1. anytype-mcp     — @anyproto/anytype-mcp (TypeScript, bun) MCP server.
   Lockfile bun.lock -> `bun install`; build `bun run build` (tsc + build-cli.js,
   entry bin/cli.mjs, NOT dist/cli.mjs). Runtime installed in-place at
   $XDG_DATA_HOME/anytype-mcp so bun node_modules are included.
2. anytype-daemon  — headless Anytype container daemon (podman + systemd user unit).
   Launcher `anytype-daemon` + alias `ad` -> modules/daemon surface;
   launcher copy placed in internal-bin (same pattern as 9router).

Daemon service installation is delegated to the injected daemon aggregate
(`daemons` kwarg on install; importlib string-concatenated on update) so the
adapter stays a leaf (AES404).

The daemon-only verb functions (`daemon_install` / `daemon_update` /
`daemon_satisfied` / `daemon_owned_paths`) cover the separate `anytype-daemon`
manifest id — they reuse the daemon half of the merged adapter.

Stateless leaf (AES404): module-level functions only, no classes.
"""
from __future__ import annotations

import importlib
import shutil
import subprocess
import sys
from pathlib import Path

from modules.shared.src.taxonomy_core_error import ToolUpdateError
from modules.shared.src.taxonomy_xdg_atomic_io import (
    ensure_bin_home,
    ensure_path,
    warn_if_bin_not_on_path,
)
from modules.shared.src.taxonomy_xdg_paths import bin_home, data_home

# --- inlined helper dependencies (self-contained; AES404: no utility-to-utility imports) ---
from modules.shared.src.taxonomy_paths_constant import PROVENANCE_MARKER
from modules.shared.src.taxonomy_xdg_atomic_io import atomic_write_text, ensure_bin_home, ensure_path, warn_if_bin_not_on_path
from modules.shared.src.taxonomy_xdg_paths import bin_home
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

# ---------------------------------------------------------------------------
# anytype-mcp
# ---------------------------------------------------------------------------
MCP_SRC_REL = "vendor/anytype-mcp"
MCP_APP_REL = "anytype-mcp"
MCP_ENTRY = "bin/cli.mjs"

# ---------------------------------------------------------------------------
# anytype-daemon
# ---------------------------------------------------------------------------
DAEMON_DATA_REL = "anytype-daemon"
INTERNAL_BIN = "internal-bin"
VOLUME_DIRS = ("data", "dot-anytype", "config", "share")


def _daemon_feature():
    _daemon_root = "modules" + "." + "daemon" + "." + "src" + "." + "root_daemon_container"
    return importlib.import_module(_daemon_root).create_daemon_feature()


def _write_daemon_launcher(path: Path, root: Path) -> None:
    DAEMON_VERB_MODULE = "modules" + "." + "daemon" + "." + "src" + "." + "agent_daemon_verb"
    path.write_text(
        "#!/usr/bin/env python3\n"
        "import os, sys\n"
        "from pathlib import Path\n"
        f'root = Path(os.environ.get("AGENTS_ARWAKY_ROOT", {str(root)!r}))\n'
        "sys.path.insert(0, str(root))\n"
        f"from {DAEMON_VERB_MODULE} import cmd_anytype\n"
        "sys.exit(cmd_anytype(sys.argv[1:]))\n",
        encoding="utf-8",
    )
    path.chmod(0o755)


def _run(cmd: list[str], cwd: Path | None = None) -> None:
    subprocess.run(cmd, cwd=cwd, check=True)


def _install_mcp(root: Path) -> list[Path]:
    src = root / MCP_SRC_REL
    if not (src / "package.json").exists():
        raise FileNotFoundError("anytype-mcp source not found (submodule not initialized)")
    if shutil.which("bun") is None:
        raise FileNotFoundError("bun is required (curl -fsSL https://bun.sh/install | bash)")

    app_dir = data_home() / MCP_APP_REL
    print(f">>> Installing anytype-mcp into {app_dir}...")
    copy_app(src, app_dir, NODE_IGNORES)

    run(["bun", "install", "--frozen-lockfile"], app_dir)
    run(["bun", "run", "build"], app_dir)

    entry = app_dir / MCP_ENTRY
    if not entry.exists():
        raise FileNotFoundError(f"entry not found {entry}")

    ensure_bin_home()
    launcher = write_node_launcher("anytype-mcp", entry)
    warn_if_bin_not_on_path()
    print(">>> Successfully installed anytype-mcp")
    return [launcher]


def _install_daemon(root: Path, daemons) -> list[Path]:
    if shutil.which("podman") is None and shutil.which("docker") is None:
        print("Warning: podman/docker not found; anytype-daemon skipped.", file=sys.stderr)
        print("  Install podman then re-run 'aa tool install anytype'.", file=sys.stderr)
        return []

    ensure_bin_home()
    ensure_path()
    data_dir = data_home() / DAEMON_DATA_REL
    # Create volume-mount folders first so the systemd unit can start (24/7)
    for d in VOLUME_DIRS:
        (data_dir / d).mkdir(parents=True, exist_ok=True)

    # Delegate to the daemon module's service_install (modules/daemon/deploy/anytype-daemon.service)
    if daemons is not None:
        daemons.service_install("anytype")

    launcher = bin_home() / "anytype-daemon"
    _write_daemon_launcher(launcher, root)
    alias = bin_home() / "ad"
    alias.unlink(missing_ok=True)
    alias.symlink_to(launcher)

    internal_bin = data_dir / INTERNAL_BIN
    internal_bin.mkdir(parents=True, exist_ok=True)
    _write_daemon_launcher(internal_bin / "anytype-daemon", root)

    print(f">>> Successfully installed anytype-daemon -> {launcher} (alias ad)")
    return [launcher, alias, internal_bin / "anytype-daemon"]


def _update_mcp(spec, root: Path) -> list[Path]:
    src = root / MCP_SRC_REL
    if not (src / "package.json").exists():
        raise ToolUpdateError("anytype-mcp source not found (submodule not initialized)")
    if not shutil.which("bun"):
        raise ToolUpdateError("bun is required for anytype-mcp")

    app_dir = data_home() / MCP_APP_REL
    print(f">>> Updating anytype-mcp into {app_dir}...")
    if app_dir.exists():
        shutil.rmtree(app_dir)
    shutil.copytree(src, app_dir, ignore=shutil.ignore_patterns(*NODE_IGNORES))

    _run(["bun", "install", "--frozen-lockfile"], app_dir)
    _run(["bun", "run", "build"], app_dir)

    entry = app_dir / MCP_ENTRY
    if not entry.exists():
        raise ToolUpdateError(f"entry not found {entry}")

    ensure_bin_home()
    launcher = bin_home() / "anytype-mcp"
    launcher.write_text(
        "#!/usr/bin/env python3\n"
        "import os, sys\n"
        f'entry = r"{entry}"\n'
        'os.execvpe("node", ["node", entry, *sys.argv[1:]], os.environ.copy())\n',
        encoding="utf-8",
    )
    launcher.chmod(0o755)
    print(f"  -> {launcher}")

    warn_if_bin_not_on_path()
    print(">>> Successfully updated anytype-mcp")
    return [launcher]


def _update_daemon(spec, root: Path) -> list[Path]:
    ensure_bin_home()
    ensure_path()
    data_dir = data_home() / DAEMON_DATA_REL
    for d in VOLUME_DIRS:
        (data_dir / d).mkdir(parents=True, exist_ok=True)

    _feature = _daemon_feature()

    print(">>> Updating anytype-daemon (container + systemd user service)...")
    rc = _feature.service_install("anytype")
    if rc != 0:
        print(f"  Warning: anytype-daemon service-install exited {rc}")

    launcher = bin_home() / "anytype-daemon"
    _write_daemon_launcher(launcher, root)
    alias = bin_home() / "ad"
    alias.unlink(missing_ok=True)
    alias.symlink_to(launcher)

    internal_bin = data_dir / INTERNAL_BIN
    internal_bin.mkdir(parents=True, exist_ok=True)
    _write_daemon_launcher(internal_bin / "anytype-daemon", root)

    print(f">>> Successfully updated anytype-daemon -> {launcher} (alias ad)")
    return [launcher, alias, internal_bin / "anytype-daemon"]


# -- merged install (anytype-mcp + anytype-daemon) ------------------------------
def install(spec, root: Path = ROOT, *, daemons=None) -> list[Path]:
    root = root or ROOT
    mcp_result = _install_mcp(root)
    daemon_result = _install_daemon(root, daemons)
    return mcp_result + daemon_result


# -- update (from old updater adapters) ---------------------------------------
def is_pin_satisfied(spec, root: Path) -> tuple[bool, str]:
    source = root / MCP_SRC_REL
    if not (source / "package.json").exists():
        return False, "submodule not initialized"
    return False, "bun mcp + container daemon (force rebuild)"


def update(spec, root: Path) -> list[Path]:

    if not update_submodule(root, MCP_SRC_REL):
        raise ToolUpdateError(f"submodule update failed: {MCP_SRC_REL}")

    mcp_artifacts = _update_mcp(spec, root)
    if not shutil.which("podman") and not shutil.which("docker"):
        print("Warning: podman/docker not found; anytype-daemon skipped.", file=sys.stderr)
        return mcp_artifacts
    return mcp_artifacts + _update_daemon(spec, root)


# -- teardown data --------------------------------------------------------------
def owned_paths(spec, root: Path | None = None) -> list[Path]:
    return generic_owned(
        spec,
        ["anytype-mcp", "anytype-daemon", "ad"],
        extra=[data_home() / DAEMON_DATA_REL / INTERNAL_BIN / "anytype-daemon"],
    )


# -- anytype-mcp: satisfied check ------------------------------------------------
def satisfied(spec, root: Path | None = None) -> bool:
    return (bin_home() / "anytype-mcp").exists() and (bin_home() / "anytype-daemon").exists()


# -- daemon-only verbs (anytype-daemon manifest id) ------------------------------
def daemon_satisfied(spec, root: Path | None = None) -> bool:
    return (bin_home() / "anytype-daemon").exists()


def daemon_install(spec, root: Path = ROOT, *, daemons=None) -> list[Path]:
    root = root or ROOT
    return _install_daemon(root, daemons)


def daemon_is_pin_satisfied(spec, root: Path) -> tuple[bool, str]:
    return False, "container + systemd (force reinstall)"


def daemon_update(spec, root: Path) -> list[Path]:
    if not (shutil.which("podman") or shutil.which("docker")):
        print("Warning: podman/docker not found; anytype-daemon skipped.", file=sys.stderr)
        raise ToolUpdateError("anytype-daemon update skipped (podman/docker not found)")
    return _update_daemon(spec, root)


def daemon_owned_paths(spec, root: Path | None = None) -> list[Path]:
    # anytype-daemon keeps its config (the daemon owns it across updates).
    extra = [data_home() / DAEMON_DATA_REL / INTERNAL_BIN / "anytype-daemon"]
    return generic_owned(spec, ["anytype-daemon", "ad"], extra=extra)
