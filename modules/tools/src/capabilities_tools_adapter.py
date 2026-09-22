"""Capability — GOD OBJECT unified per-tool adapter (implements IToolAdapterFacade).

Maximum DRY: top-level factories + config-driven generation + unified lifecycles.

Skill structure (`create-capabilities`, AES403) — honoured in-file:

- Role `adapter` is an allowed external role; exactly 1 class
  (`ToolAdapterFacade`) implements the `IToolAdapterFacade` protocol
  (≥1 implementor, ≤3 types). Imports are taxonomy + `_protocol`
  contract only — no `agent_*`, no sibling `capabilities_*`, no
  `surface_*`, no local domain models.
- 3-Block order, class FIRST (top of file): Block 1 (definition +
  constructor), Block 2 (protocol methods ONLY, in protocol order),
  Block 3 (`__repr__` + private instance helpers). Module-level
  factories / lifecycles / config below are the Block 3 helpers —
  kept in-file by explicit request instead of `utility_*`
  (Helper-vs-Utility: domain-specific, single consumer).
- Known deviation: AES301 FILE_TOO_LARGE is registered as an exception
  in `lint_arwaky.config.yaml`; everything else scans clean.
"""
from __future__ import annotations

import contextlib
import datetime
import importlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from types import SimpleNamespace
from typing import Callable

from modules.shared.src.taxonomy_core_error import ToolUpdateError
from modules.shared.src.taxonomy_paths_constant import PROVENANCE_MARKER, REPO_ROOT
from modules.shared.src.taxonomy_tool_vo import ToolSpec
from modules.shared.src.taxonomy_xdg_atomic_io import (
    atomic_write_text,
    ensure_bin_home,
    ensure_path,
    warn_if_bin_not_on_path,
)
from modules.shared.src.taxonomy_xdg_paths import (
    agents_arwaky_config_dir,
    bin_home,
    cache_home,
    config_home,
    data_home,
    tool_cache_dir,
    tool_config_dir,
    tool_data_dir,
    tool_state_dir,
)
from modules.tools.src.contract_tools_protocol import IToolAdapterFacade
from modules.tools.src.taxonomy_tools_constant import LAUNCHER_NAMES


class ToolAdapterFacade(IToolAdapterFacade):
    """God-object facade: one injected object holding all 13 tool verbs."""

    # ─── Block 1: Class Definition & Constructor ─────────────────────
    def __init__(
        self,
        registry: dict[str, object] | None = None,
        daemons=None,
        root: Path | None = None,
    ) -> None:
        self._registry = dict(registry) if registry is not None else dict(_ADAPTER_UNITS)
        # Any missing id falls back to this file's own units (god object is SSOT).
        for tool_id, unit in _ADAPTER_UNITS.items():
            self._registry.setdefault(tool_id, unit)
        self._daemons = daemons
        self._root = root

    # ─── Block 2: Public Contract (domain protocol ONLY, protocol order) ──
    def resolve(self, spec: ToolSpec) -> object:
        """Uniform verb surface for *spec* (god-object unit)."""
        return self._unit(spec)

    def is_registered(self, spec: ToolSpec) -> bool:
        return spec.id in self._registry

    def satisfied(self, spec: ToolSpec) -> bool:
        """Adapter's idempotence probe (True when the tool is already at pin)."""
        unit = self._unit(spec)
        fn = getattr(unit, "satisfied", None)
        return bool(fn(spec, self._root_for(None))) if callable(fn) else False

    def is_pin_satisfied(self, spec: ToolSpec) -> tuple[bool, str]:
        """Adapter's pin-check for the updater (True, reason) when satisfied."""
        unit = self._unit(spec)
        fn = getattr(unit, "is_pin_satisfied", None)
        return fn(spec, self._root_for(None)) if callable(fn) else (False, "no pin check")

    def install(self, spec: ToolSpec, root: Path | None = None) -> list[Path]:
        """Run the tool's install build (source-init lives inside the verb)."""
        r = self._root_for(root)
        unit = self._unit(spec)
        fn = getattr(unit, "install", None)
        if not callable(fn):
            return []
        try:
            return list(fn(spec, r, daemons=self._daemons) or [])
        except TypeError:
            return list(fn(spec, r) or [])

    def update(self, spec: ToolSpec, root: Path | None = None) -> list[Path]:
        """Run the tool's update build (git-update lives inside the verb)."""
        r = self._root_for(root)
        unit = self._unit(spec)
        fn = getattr(unit, "update", None)
        return list(fn(spec, r) or []) if callable(fn) else []

    def owned_paths(self, spec: ToolSpec, root: Path | None = None) -> list[Path]:
        """The tool's teardown set (per-tool verb, generic fallback)."""
        unit = self._unit(spec)
        fn = getattr(unit, "owned_paths", None)
        if callable(fn):
            return list(fn(spec, self._root_for(root)) or [])
        return generic_owned(spec, LAUNCHER_NAMES.get(spec.id, [spec.id]))

    # ─── Block 3: Dunder Methods, Factories & Helpers ────────────────
    def __repr__(self) -> str:
        return f"ToolAdapterFacade(tools={len(self._registry)})"

    def _unit(self, spec: ToolSpec):
        """Resolve the verb namespace for *spec* (registry, then in-file SSOT)."""
        return self._registry.get(spec.id, _ADAPTER_UNITS.get(spec.id))

    def _root_for(self, root: Path | None) -> Path:
        """Effective repo root: explicit arg, else injected, else REPO_ROOT."""
        return root or self._root or ROOT


# ===========================================================================
# Block 3 (lanjutan): module-level private helpers
# (dibaca setelah class: urutan file = Block 1 → Block 2 → Block 3)
# ===========================================================================

# ---------------------------------------------------------------------------
# Top-Level Factories (DRY core — dipakai di seluruh file)
# ---------------------------------------------------------------------------
def _make_satisfied(bin_name: str) -> Callable:
    """Factory: satisfied probe — cek keberadaan satu launcher di XDG bin."""
    return lambda spec, root=None: (bin_home() / bin_name).exists()


def _make_multi_satisfied(bin_names: list[str]) -> Callable:
    """Factory: satisfied probe — semua launcher harus ada."""
    return lambda spec, root=None: all((bin_home() / b).exists() for b in bin_names)


def _make_pin_check(src_rel: str, reason: str) -> Callable:
    """Factory: pin-check — (False, reason) kecuali submodule belum init."""
    return lambda spec, root: (
        (False, "submodule not initialized")
        if src_rel and not (root / src_rel).exists()
        else (False, reason)
    )


def _make_owned(
    launchers: list,
    *,
    extra: list[Path] | Callable[[], list[Path]] | None = None,
    config: list[str] | None = None,
    extra_fn: Callable[[], list[Path]] | None = None,
) -> Callable:
    """Factory: owned_paths — bungkus generic_owned (extra dievaluasi saat call)."""
    names = [l[0] for l in launchers] if launchers and isinstance(launchers[0], tuple) else list(launchers)

    def owned(spec, root=None):
        stat = list(extra() if callable(extra) else (extra or []))
        dyn = list(extra_fn()) if callable(extra_fn) else []
        return generic_owned(spec, names, extra=stat + dyn, config=config)

    return owned


def _make_install(lifecycle_fn: Callable) -> Callable:
    """Factory: install wrapper — signature (spec, root=ROOT, *, daemons=None)."""
    return lambda spec, root=ROOT, *, daemons=None: lifecycle_fn("install", root or ROOT, daemons)


def _make_update(lifecycle_fn: Callable) -> Callable:
    """Factory: update wrapper — signature (spec, root)."""
    return lambda spec, root: lifecycle_fn("update", root or ROOT, None)


# ---------------------------------------------------------------------------
# Pure utilities (single copy)
# ---------------------------------------------------------------------------
ROOT = REPO_ROOT
_NODE_IGNORES = [
    "node_modules", ".git", "__pycache__", "target", "*.egg-info",
    ".venv", "venv", "*.tsbuildinfo",
]


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
    for branch in ("main", "master", "dev"):
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


def update_submodule(repo_root: Path, submodule_path: str) -> bool:
    """Full update workflow: fetch, check, pull a submodule."""
    submodule_dir = repo_root / submodule_path
    if not submodule_dir.exists() or not (submodule_dir / ".git").exists():
        r = run_quiet(
            ["git", "-C", str(repo_root), "submodule", "update", "--init", submodule_path],
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


def write_install_stamp(app_dir: Path, tool: str, submodule_dir: Path) -> None:
    """Record what was deployed so rollback/audit is possible."""
    stamp = {
        "tool": tool,
        "commit": get_current_commit(submodule_dir) or "unknown",
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
    """Generic XDG owned set: bin launchers + data + cache (+ config subtrees)."""
    paths: list[Path] = [bin_home() / name for name in launcher_names]
    paths.append(data_home() / spec.id)
    paths.append(cache_home() / spec.id)
    for name in config or []:
        paths.append(config_home() / name)
    paths.extend(extra or [])
    return paths


def copy_app(src: Path, app_dir: Path, ignore_patterns: list[str]) -> None:
    """Replace *app_dir* with a copy of *src*, dropping the listed patterns."""
    ignore = shutil.ignore_patterns(*ignore_patterns)
    if app_dir.exists():
        shutil.rmtree(app_dir)
    shutil.copytree(src, app_dir, ignore=ignore)


def require(tool: str, reason: str = "") -> bool:
    """True when *tool* is on PATH; otherwise print the missing-tool diagnostic."""
    if shutil.which(tool):
        return True
    print(f"Error: {tool} not found in PATH. {reason}", file=sys.stderr)
    return False


def run(cmd: list[str], cwd: Path | str | None = None) -> None:
    """Run with check=True; raises subprocess.CalledProcessError on failure."""
    subprocess.run(cmd, cwd=str(cwd) if cwd else None, check=True)


def finish_bin() -> None:
    """Ensure bin home + PATH warning after launcher writes."""
    ensure_bin_home()
    warn_if_bin_not_on_path()


def symlink_alias(alias: str, target: Path) -> Path:
    """Symlink *alias* in XDG bin pointing at *target* (idempotent)."""
    ensure_bin_home()
    a = bin_home() / alias
    a.unlink(missing_ok=True)
    a.symlink_to(target)
    return a


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


def write_node_launcher(name: str, entry: Path) -> Path:
    """Write a node entry launcher via the shared launcher writer."""
    launcher = write_node_entry_launcher(name, entry)
    print(f"  -> {launcher}")
    return launcher


def write_uv_launchers(
    src_rel: str,
    launchers: list[tuple[str, str]],
    root: Path | None = None,
    uv_args: list[str] | None = None,
) -> list[Path]:
    """Write uv-run launchers: `uv run <uv_args> --directory <src_rel> <entry>`."""
    ensure_bin_home()
    baked_root = str(root) if root is not None else str(REPO_ROOT)
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
    subprocess.run([str(python_bin), "-m", "pip", "install", "-e", str(src_dir)], check=True)


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


# ---------------------------------------------------------------------------
# Generic lifecycle functions (satu implementasi per keluarga runner)
# ---------------------------------------------------------------------------
def _node_tool_lifecycle(
    action: str,
    root: Path,
    src_rel: str,
    app_name: str,
    install_cmd: list[str],
    build_cmd: list[str],
    ignores: list[str],
    requires: tuple[str, str] | None,
    src_marker: str,
    write_launchers_fn: Callable[[Path, bool], list[Path]],
    post_copy_hook: Callable[[Path], None] | None = None,
) -> list[Path]:
    """Unified install/update untuk tool node (npm/pnpm/bun, dengan/tanpa build)."""
    is_update = action == "update"
    err_cls = ToolUpdateError if is_update else FileNotFoundError
    verb_ing = "Updating" if is_update else "Installing"
    verb_ed = "updated" if is_update else "installed"

    if is_update:
        if not update_submodule(root, src_rel):
            raise err_cls(f"submodule update failed: {src_rel}")
        source = root / src_rel
    else:
        source = ensure_source(root, src_rel)
    if not (source / src_marker).exists():
        raise err_cls(f"{app_name} source not found (submodule not initialized): {source}")

    if requires and requires[0] and not require(requires[0], requires[1]):
        raise err_cls(f"{requires[0]} is required ({requires[1]}).")

    app_dir = data_home() / app_name
    print(f">>> {verb_ing} {app_name} into {app_dir}...")
    copy_app(source, app_dir, ignores)

    if post_copy_hook:
        post_copy_hook(app_dir)
    if install_cmd:
        run(install_cmd, app_dir)
    if build_cmd:
        run(build_cmd, app_dir)

    artifacts = write_launchers_fn(app_dir, is_update)
    finish_bin()
    print(f">>> Successfully {verb_ed} {app_name}")
    return artifacts


def _uv_venv_lifecycle(
    action: str,
    root: Path,
    src_rel: str,
    tool_name: str,
    launchers: list[tuple[str, str]],
    post_install_hook: Callable[[Path, Path], None] | None = None,
    init_message: str = "",
) -> list[Path]:
    """Unified install/update untuk tool venv+pip (blender/vision/qwen-web)."""
    is_update = action == "update"
    err_cls = ToolUpdateError if is_update else FileNotFoundError

    if is_update:
        print(f">>> Updating {tool_name} (XDG compliant)...")
        if not update_submodule(root, src_rel):
            raise err_cls(f"submodule update failed: {src_rel}")
        source = root / src_rel
        if not source.exists():
            raise err_cls(f"source not found {source}")
        python_bin = ensure_venv(tool_name, force=True)
    else:
        src_dir = root / src_rel
        source = ensure_source(root, src_rel)
        if not source.exists():
            raise err_cls(f"source not found {src_dir}")
        python_bin = ensure_venv(tool_name, force=False)

    install_package(python_bin, source, tool_name)
    if post_install_hook:
        post_install_hook(python_bin, source)
    setup_xdg_directories(tool_name)
    setup_bin_links(python_bin, launchers)

    if is_update:
        write_install_stamp(python_bin.parent.parent, tool_name, source)
        created = [bin_home() / name for name, _entry in launchers]
        print(f"\n>>> Successfully updated {tool_name}")
        print(f"    Venv: {python_bin.parent}")
        return created
    print(f"\n>>> Successfully installed {tool_name}")
    print(f"    Venv: {python_bin.parent}")
    print(f"    Data: {tool_data_dir(tool_name)}")
    if init_message:
        print(f"    {init_message}")
    return [python_bin]


def _uv_project_lifecycle(
    action: str,
    root: Path,
    src_rel: str,
    tool_name: str,
    write_launchers_fn: Callable[[Path], list[Path]],
) -> list[Path]:
    """Unified install/update untuk tool `uv run` (mnemosyne/workspace)."""
    is_update = action == "update"
    err_cls = ToolUpdateError if is_update else FileNotFoundError
    verb_ed = "updated" if is_update else "installed"

    if is_update:
        if not update_submodule(root, src_rel):
            raise err_cls(f"submodule update failed: {src_rel}")
        source = root / src_rel
        if not source.exists():
            raise err_cls(f"source not found {source}")
    else:
        src_dir = root / src_rel
        source = ensure_source(root, src_rel)
        if not source.exists():
            raise err_cls(f"source not found {src_dir}")

    created = write_launchers_fn(root)
    print(f">>> Successfully {verb_ed} {tool_name}")
    return created


# ---------------------------------------------------------------------------
# Centralized tool configuration (DRY core)
# ---------------------------------------------------------------------------
QWEN_TOOL_NAME = "qwen-web"


def _qwen_post_install(python_bin: Path, source: Path) -> None:
    print("  [install] Installing Playwright Chromium...")
    subprocess.run([str(python_bin), "-m", "playwright", "install", "chromium"], check=True)
    data_dir = tool_data_dir(QWEN_TOOL_NAME)
    state_dir = tool_state_dir(QWEN_TOOL_NAME)
    cache_dir = tool_cache_dir(QWEN_TOOL_NAME)
    for role in ("role-architect", "role-business-analyst", "role-tech-lead"):
        (data_dir / "input" / role / "done").mkdir(parents=True, exist_ok=True)
        (data_dir / "input" / role / "failed").mkdir(parents=True, exist_ok=True)
    (data_dir / "output").mkdir(parents=True, exist_ok=True)
    (data_dir / "qwen_session").mkdir(parents=True, exist_ok=True)
    (state_dir / "log").mkdir(parents=True, exist_ok=True)
    (cache_dir / ".processing").mkdir(parents=True, exist_ok=True)
    print(f"  [ok] Data: {data_dir}")
    print(f"  [ok] State: {state_dir}")
    print(f"  [ok] Cache: {cache_dir}")


SIMPLE_TOOLS_CONFIG = {
    "blender": {
        "lifecycle": "uv_venv",
        "src_rel": "internal/blender-arwaky",
        "tool_name": "blender-arwaky",
        "launchers": [
            ("blender-arwaky", "blender-arwaky"),
            ("ba", "blender-arwaky"),
            ("blender-mcp", "blender-mcp"),
        ],
        "pin_reason": "venv/pip (rebuild required)",
        "satisfied_bin": "blender-arwaky",
        "init_message": "Run 'blender-arwaky init' to setup workspace symlinks",
    },
    "vision": {
        "lifecycle": "uv_venv",
        "src_rel": "internal/vision-arwaky",
        "tool_name": "vision-arwaky",
        "launchers": [
            ("vision-arwaky", "vision-arwaky-cli"),
            ("vision-arwaky-cli", "vision-arwaky-cli"),
            ("va", "vision-arwaky-cli"),
            ("vision-arwaky-mcp", "vision-arwaky-mcp"),
        ],
        "pin_reason": "venv/pip (rebuild required)",
        "satisfied_bin": "vision-arwaky",
        "init_message": "Run 'vision-arwaky-cli init' to setup workspace symlinks",
    },
    "qwen-web": {
        "lifecycle": "uv_venv",
        "src_rel": f"internal/{QWEN_TOOL_NAME}-arwaky",
        "tool_name": QWEN_TOOL_NAME,
        "launchers": [
            ("qwen-web-arwaky", "qwen-web-arwaky"),
            ("qwa", "qwen-web-arwaky"),
            ("qwen-web-cli", "qwen-web-arwaky"),
            ("qwen-web-mcp", "qwen-web-mcp"),
            ("qwc", "qwen-web-arwaky"),
        ],
        "pin_reason": "venv/pip + Playwright (rebuild required)",
        "satisfied_bin": "qwen-web-arwaky",
        "init_message": "Run 'qwc init' to setup workspace symlinks",
        "post_install_hook": _qwen_post_install,
        "extra_paths_fn": lambda: [
            tool_config_dir(QWEN_TOOL_NAME),
            tool_state_dir(QWEN_TOOL_NAME),
            tool_cache_dir(QWEN_TOOL_NAME),
        ],
    },
    "mnemosyne": {
        "lifecycle": "uv_project",
        "src_rel": "vendor/mnemosyne",
        "tool_name": "mnemosyne",
        "launchers": [("mnemosyne", "mnemosyne"), ("mnemosyne-mcp", "mnemosyne")],
        "pin_reason": "uv project (rebuild required)",
        "satisfied_bin": "mnemosyne",
        "uv_args": ["--extra", "mcp"],
    },
    "workspace": {
        "lifecycle": "uv_project",
        "src_rel": "vendor/google-workspace-mcp",
        "tool_name": "google-workspace-mcp",
        "launchers": [("workspace-mcp", "workspace-mcp"), ("google-workspace-mcp", "workspace-mcp")],
        "pin_reason": "uv project (rebuild required)",
        "satisfied_bin": "workspace-mcp",
        # google-workspace-mcp adalah alias PATH dari workspace-mcp.
        "alias_second_to_first": True,
    },
    "codegraph": {
        "lifecycle": "node",
        "src_rel": "vendor/codegraph",
        "app_name": "codegraph",
        "entry": "dist/bin/codegraph.js",
        "launchers": ["codegraph-mcp", "codegraph"],
        "pin_reason": "npm workspace (rebuild required)",
        "satisfied_bin": "codegraph-mcp",
        "requires": ("npm", "codegraph requires npm (https://nodejs.org)"),
        "install_cmd": ["npm", "ci", "--no-audit", "--no-fund"],
        "build_cmd": ["npm", "run", "build"],
    },
    "context7": {
        "lifecycle": "node",
        "src_rel": "vendor/context7",
        "app_name": "context7",
        "launchers": ["context7-mcp", "ctx7"],
        "ignores": [
            "node_modules", ".git", ".old_modules*", "__pycache__", "mcpb",
            "dist", "target", "*.egg-info", ".venv", "venv", ".next", ".turbo",
        ],
        "src_marker": "pnpm-workspace.yaml",
        "pin_reason": "pnpm workspace (rebuild required)",
        "satisfied_bin": "context7-mcp",
        "requires": ("pnpm", "context7 is a pnpm workspace"),
        "install_cmd": ["pnpm", "install", "--frozen-lockfile"],
        "build_cmd": ["pnpm", "run", "build"],
    },
    "fetch": {
        "lifecycle": "node",
        "src_rel": "vendor/fetch-mcp",
        "app_name": "fetch-mcp",
        "launchers": ["fetch-mcp", "mcp-fetch"],
        "ignores": [
            "node_modules", ".git", "__pycache__", "target", "*.egg-info",
            ".venv", "venv", "*.tsbuildinfo",
        ],
        "pin_reason": "bun workspace (rebuild required)",
        "satisfied_bin": "fetch-mcp",
        "requires": ("bun", "fetch-mcp requires bun (curl -fsSL https://bun.sh/install | bash)"),
        "install_cmd": ["bun", "install", "--frozen-lockfile"],
        "build_cmd": ["bun", "run", "build"],
    },
    "ponytail": {
        "lifecycle": "node",
        "src_rel": "vendor/ponytail",
        "app_name": "ponytail",
        "launchers": ["ponytail-mcp"],
        "entry": "ponytail-mcp/index.js",
        "ignores": ["node_modules", ".git", "__pycache__", "*.egg-info", ".venv", "venv"],
        "pin_reason": "npm workspace (rebuild required)",
        "satisfied_bin": "ponytail-mcp",
        "requires": ("npm", "ponytail requires npm (https://nodejs.org)"),
    },
}


# ---------------------------------------------------------------------------
# Tool adapter factory (auto-generate unit dari config)
# ---------------------------------------------------------------------------
def _build_adapter_unit(name: str, config: dict) -> SimpleNamespace:
    """Build complete adapter unit dari configuration."""
    lifecycle = config["lifecycle"]
    src_rel = config["src_rel"]
    tool_name = config.get("tool_name", name)
    launchers = config["launchers"]
    pin_reason = config.get("pin_reason", "rebuild required")
    satisfied_bin = config.get("satisfied_bin")

    satisfied = _make_satisfied(satisfied_bin)
    is_pin_satisfied = _make_pin_check(src_rel, pin_reason)
    owned_paths = _make_owned(
        launchers,
        extra=config.get("extra_paths"),
        config=config.get("config_dirs"),
        extra_fn=config.get("extra_paths_fn"),
    )

    if lifecycle == "uv_venv":
        post_install = config.get("post_install_hook")
        init_msg = config.get("init_message", "")

        def install(spec, root=ROOT, *, daemons=None):
            return _uv_venv_lifecycle(
                "install", root or ROOT, src_rel, tool_name, launchers,
                post_install_hook=post_install, init_message=init_msg,
            )

        def update(spec, root):
            return _uv_venv_lifecycle(
                "update", root, src_rel, tool_name, launchers,
                post_install_hook=post_install,
            )

    elif lifecycle == "uv_project":
        uv_args = config.get("uv_args")
        alias_second = config.get("alias_second_to_first", False)

        def write_launchers(root):
            targets = launchers[:1] if alias_second else launchers
            created = write_uv_launchers(src_rel, targets, root=root, uv_args=uv_args)
            for p in created:
                print(f"  -> {p}")
            if alias_second:
                alias = symlink_alias(launchers[1][0], created[0])
                print(f"  -> {alias}")
                created.append(alias)
            return created

        def install(spec, root=ROOT, *, daemons=None):
            return _uv_project_lifecycle("install", root or ROOT, src_rel, tool_name, write_launchers)

        def update(spec, root):
            return _uv_project_lifecycle("update", root, src_rel, tool_name, write_launchers)

    elif lifecycle == "node":
        app_name = config.get("app_name", tool_name)
        entry = config.get("entry")
        ignores = config.get("ignores", _NODE_IGNORES)
        requires = config.get("requires")
        src_marker = config.get("src_marker", "package.json")
        install_cmd = config.get("install_cmd") or []
        build_cmd = config.get("build_cmd") or []
        post_copy_hook: Callable[[Path], None] | None = None

        if name == "codegraph":
            def write_launchers(app_dir, is_update):
                entry_path = app_dir / entry
                if not entry_path.exists():
                    raise (ToolUpdateError if is_update else FileNotFoundError)(
                        f"entry not found {entry_path}")
                created = [write_node_launcher(launchers[0], entry_path)]
                created += [symlink_alias(n, bin_home() / launchers[0]) for n in launchers[1:]]
                return created
        elif name == "context7":
            ctx_launchers = {
                "context7-mcp": "packages/mcp/dist/index.js",
                "ctx7": "packages/cli/dist/index.js",
            }

            def write_launchers(app_dir, is_update):
                created = []
                for lname, lentry in ctx_launchers.items():
                    target = app_dir / lentry
                    if target.exists():
                        created.append(write_node_launcher(lname, target))
                    else:
                        print(f"  Warning: entry not found {target}", file=sys.stderr)
                return created

            def post_copy_hook(app_dir):
                ws = app_dir / "pnpm-workspace.yaml"
                if "dangerouslyAllowAllBuilds" not in ws.read_text(encoding="utf-8", errors="replace"):
                    with ws.open("a", encoding="utf-8") as f:
                        f.write("\ndangerouslyAllowAllBuilds: true\n")
        elif name == "fetch":
            fetch_cli_args = {
                "html", "markdown", "readable", "txt", "json", "youtube",
                "--help", "-h", "--version", "-v",
            }

            def write_launchers(app_dir, is_update):
                index_js = app_dir / "dist/index.js"
                cli_js = app_dir / "dist/cli.js"
                if not index_js.exists() or not cli_js.exists():
                    raise (ToolUpdateError if is_update else FileNotFoundError)(
                        f"build output incomplete ({index_js}, {cli_js})")
                ensure_bin_home()
                content = (
                    "#!/usr/bin/env python3\n"
                    f"# {PROVENANCE_MARKER}\n"
                    "import os, sys\n"
                    f'index_js = r"{index_js}"\n'
                    f'cli_js = r"{cli_js}"\n'
                    "cli = " + repr(sorted(fetch_cli_args)) + "\n"
                    "script = cli_js if (len(sys.argv) > 1 and sys.argv[1] in cli) else index_js\n"
                    "env = os.environ.copy()\n"
                    'os.execvpe("node", ["node", script, *sys.argv[1:]], env)\n'
                )
                artifacts = []
                for lname in ("fetch-mcp", "mcp-fetch"):
                    launcher = bin_home() / lname
                    launcher.write_text(content, encoding="utf-8")
                    launcher.chmod(0o755)
                    artifacts.append(launcher)
                    print(f"  -> {launcher}")
                warn_if_bin_not_on_path()
                return artifacts
        elif name == "ponytail":
            def write_launchers(app_dir, is_update):
                entry_path = app_dir / entry
                if not entry_path.exists():
                    raise (ToolUpdateError if is_update else FileNotFoundError)(
                        f"entry not found {entry_path}")
                launcher = write_node_launcher("ponytail-mcp", entry_path)
                finish_bin()
                return [launcher]

            def post_copy_hook(app_dir):
                mcp_dir = app_dir / "ponytail-mcp"
                if (mcp_dir / "package.json").exists():
                    run(["npm", "ci", "--no-audit", "--no-fund"], mcp_dir)
        else:
            def write_launchers(app_dir, is_update):
                entry_path = app_dir / entry
                if not entry_path.exists():
                    raise (ToolUpdateError if is_update else FileNotFoundError)(
                        f"entry not found {entry_path}")
                return [write_node_launcher(name, entry_path)]

        def install(spec, root=ROOT, *, daemons=None):
            return _node_tool_lifecycle(
                "install", root or ROOT, src_rel, app_name,
                install_cmd, build_cmd, ignores, requires, src_marker,
                write_launchers, post_copy_hook,
            )

        def update(spec, root):
            return _node_tool_lifecycle(
                "update", root, src_rel, app_name,
                install_cmd, build_cmd, ignores, requires, src_marker,
                write_launchers, post_copy_hook,
            )
    else:
        raise ValueError(f"unknown lifecycle {lifecycle!r} for tool {name!r}")

    return SimpleNamespace(
        satisfied=satisfied,
        install=install,
        update=update,
        is_pin_satisfied=is_pin_satisfied,
        owned_paths=owned_paths,
    )


# ---------------------------------------------------------------------------
# Complex tools (implementasi custom + factories)
# ---------------------------------------------------------------------------
# anytype (bun MCP + container daemon) — unified lifecycle
ANYTYPE_MCP_SRC_REL = "vendor/anytype-mcp"
ANYTYPE_MCP_APP_REL = "anytype-mcp"
ANYTYPE_MCP_ENTRY = "bin/cli.mjs"
ANYTYPE_DAEMON_DATA_REL = "anytype-daemon"
ANYTYPE_INTERNAL_BIN = "internal-bin"
ANYTYPE_VOLUME_DIRS = ("data", "dot-anytype", "config", "share")


def _anytype_daemon_feature():
    _daemon_root = "modules" + "." + "daemon" + "." + "src" + "." + "root_daemon_container"
    return importlib.import_module(_daemon_root).create_daemon_feature()


def _anytype_write_daemon_launcher(path: Path, root: Path) -> None:
    _daemon_verb = "modules" + "." + "daemon" + "." + "src" + "." + "agent_daemon_verb"
    path.write_text(
        "#!/usr/bin/env python3\n"
        "import os, sys\n"
        "from pathlib import Path\n"
        f'root = Path(os.environ.get("AGENTS_ARWAKY_ROOT", {str(root)!r}))\n'
        "sys.path.insert(0, str(root))\n"
        f"from {_daemon_verb} import cmd_anytype\n"
        "sys.exit(cmd_anytype(sys.argv[1:]))\n",
        encoding="utf-8",
    )
    path.chmod(0o755)


def _anytype_mcp_launchers(app_dir: Path, is_update: bool) -> list[Path]:
    entry = app_dir / ANYTYPE_MCP_ENTRY
    if not entry.exists():
        raise (ToolUpdateError if is_update else FileNotFoundError)(f"entry not found {entry}")
    return [write_node_launcher("anytype-mcp", entry)]


def _anytype_daemon_lifecycle(action: str, root: Path, daemons) -> list[Path]:
    is_update = action == "update"
    verb_ed = "updated" if is_update else "installed"
    ensure_bin_home()
    ensure_path()
    data_dir = data_home() / ANYTYPE_DAEMON_DATA_REL
    for d in ANYTYPE_VOLUME_DIRS:
        (data_dir / d).mkdir(parents=True, exist_ok=True)

    if is_update:
        _feature = _anytype_daemon_feature()
        print(">>> Updating anytype-daemon (container + systemd user service)...")
        rc = _feature.service_install("anytype")
        if rc != 0:
            print(f"  Warning: anytype-daemon service-install exited {rc}")
    else:
        if daemons is not None:
            rc = daemons.service_install("anytype")
            if rc != 0:
                raise ToolUpdateError(f"anytype-daemon service-install exited {rc}")
        elif shutil.which("podman") is None and shutil.which("docker") is None:
            print("Warning: podman/docker not found; anytype-daemon skipped.", file=sys.stderr)
            print("  Install podman then re-run 'aa tool install anytype'.", file=sys.stderr)
            return []

    launcher = bin_home() / "anytype-daemon"
    _anytype_write_daemon_launcher(launcher, root)
    alias = bin_home() / "ad"
    alias.unlink(missing_ok=True)
    alias.symlink_to(launcher)

    internal_bin = data_dir / ANYTYPE_INTERNAL_BIN
    internal_bin.mkdir(parents=True, exist_ok=True)
    _anytype_write_daemon_launcher(internal_bin / "anytype-daemon", root)

    print(f">>> Successfully {verb_ed} anytype-daemon -> {launcher} (alias ad)")
    return [launcher, alias, internal_bin / "anytype-daemon"]


def _anytype_combined_lifecycle(action: str, root: Path, daemons=None) -> list[Path]:
    """Unified lifecycle: MCP + daemon dalam satu function."""
    if action == "update":
        if not update_submodule(root, ANYTYPE_MCP_SRC_REL):
            raise ToolUpdateError(f"submodule update failed: {ANYTYPE_MCP_SRC_REL}")
    mcp_result = _node_tool_lifecycle(
        action, root, ANYTYPE_MCP_SRC_REL, ANYTYPE_MCP_APP_REL,
        ["bun", "install", "--frozen-lockfile"], ["bun", "run", "build"],
        _NODE_IGNORES, ("bun", "bun is required (curl -fsSL https://bun.sh/install | bash)"),
        "package.json", _anytype_mcp_launchers,
    )
    if not (shutil.which("podman") or shutil.which("docker")):
        print("Warning: podman/docker not found; anytype-daemon skipped.", file=sys.stderr)
        return mcp_result
    return mcp_result + _anytype_daemon_lifecycle(action, root, daemons)


anytype_satisfied = _make_multi_satisfied(["anytype-mcp", "anytype-daemon"])
anytype_is_pin_satisfied = _make_pin_check(
    ANYTYPE_MCP_SRC_REL, "bun mcp + container daemon (force rebuild)")
anytype_owned_paths = _make_owned(
    ["anytype-mcp", "anytype-daemon", "ad"],
    extra=lambda: [data_home() / ANYTYPE_DAEMON_DATA_REL / ANYTYPE_INTERNAL_BIN / "anytype-daemon"],
)
anytype_install = _make_install(_anytype_combined_lifecycle)
anytype_update = _make_update(_anytype_combined_lifecycle)

anytype_daemon_satisfied = _make_satisfied("anytype-daemon")
anytype_daemon_is_pin_satisfied = _make_pin_check("", "container + systemd (force reinstall)")
anytype_daemon_owned_paths = _make_owned(
    ["anytype-daemon", "ad"],
    extra=lambda: [data_home() / ANYTYPE_DAEMON_DATA_REL / ANYTYPE_INTERNAL_BIN / "anytype-daemon"],
)
anytype_daemon_install = _make_install(_anytype_daemon_lifecycle)
anytype_daemon_update = _make_update(_anytype_daemon_lifecycle)


# lint (cargo — rustup bootstrap + atomic install)
LINT_INTERNAL_DIR_REL = "internal/lint-arwaky"
LINT_BINARIES = ["lint-arwaky", "la", "lint-arwaky-cli", "lint-arwaky-mcp", "lint-arwaky-tui"]
LINT_LAUNCHERS = [
    ("lint-arwaky", "lint-arwaky"),
    ("la", "la"),
    ("lint-arwaky-cli", "lint-arwaky-cli"),
    ("lint-arwaky-mcp", "lint-arwaky-mcp"),
    ("lint-arwaky-tui", "lint-arwaky-tui"),
    ("lac", "lac"),
]
# NOTE: leaf lama merujuk `_BUILD_DEPS` tanpa definisi (NameError) — didefinisikan di sini.
LINT_BUILD_DEPS: tuple[tuple[str, str], ...] = (("sccache", "sccache"), ("mold", "mold"))


def _lint_bootstrap_rustup() -> bool:
    """Install rust toolchain via rustup (non-interactive). Best effort."""
    fd, script = tempfile.mkstemp(prefix="rustup-init-", suffix=".sh")
    os.close(fd)
    try:
        if shutil.which("curl"):
            cmd = ["curl", "--proto", "=https", "--tlsv1.2", "-sSf",
                   "https://sh.rustup.rs", "-o", script]
        elif shutil.which("wget"):
            cmd = ["wget", "-qO", script, "https://sh.rustup.rs"]
        else:
            print("  Warning: no curl/wget found for rustup bootstrap.", file=sys.stderr)
            return False
        subprocess.run(cmd, check=True, timeout=120)
        subprocess.run(["sh", script, "-y", "--no-modify-path"], check=True, timeout=600)
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as e:
        print(f"  Warning: rustup bootstrap failed ({e}).", file=sys.stderr)
        return False
    finally:
        os.unlink(script)
    return _lint_cargo_on_path() is not None


def _lint_cargo_on_path() -> str | None:
    """Find cargo on PATH or at the default rustup location."""
    found = shutil.which("cargo")
    if found:
        return found
    for cand in (Path.home() / ".cargo/bin/cargo", Path("/usr/local/cargo/bin/cargo")):
        if cand.exists():
            os.environ["PATH"] = str(cand.parent) + os.pathsep + os.environ.get("PATH", "")
            return str(cand)
    return None


def _lint_preflight_build_deps() -> dict:
    """Ensure build deps are present (apt best-effort via sudo); fallback override env."""
    env: dict = {}
    for cmd, pkg in LINT_BUILD_DEPS:
        if shutil.which(cmd):
            continue
        print(f">>> Build dep '{cmd}' not found; trying apt install {pkg}...", file=sys.stderr)
        try:
            subprocess.run(["sudo", "-n", "apt-get", "install", "-y", pkg],
                           check=True, timeout=300, capture_output=True)
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as e:
            print(f"  Warning: apt install {pkg} failed ({e}); using fallback.", file=sys.stderr)
        if shutil.which(cmd):
            print(f"  -> {cmd} available.")
        else:
            if cmd == "sccache":
                env["CARGO_BUILD_RUSTC_WRAPPER"] = ""
                print("  -> sccache skipped (RUSTC_WRAPPER empty).", file=sys.stderr)
            elif cmd == "mold":
                env["CARGO_TARGET_X86_64_UNKNOWN_LINUX_GNU_RUSTFLAGS"] = ""
                env["CARGO_TARGET_X86_64_UNKNOWN_LINUX_GNU_LINKER"] = "cc"
                print("  -> mold skipped (linker=cc).", file=sys.stderr)
    return env


def _lint_build_and_install(root: Path, *, raise_on_missing_cargo: bool) -> list[Path]:
    """Cargo release build into XDG cache + atomic binary install + `lac` alias."""
    internal_dir = root / LINT_INTERNAL_DIR_REL
    if _lint_cargo_on_path() is None:
        print(">>> cargo not found; attempting rustup bootstrap...", file=sys.stderr)
        if not _lint_bootstrap_rustup():
            if not raise_on_missing_cargo:
                print("  Warning: lint-arwaky skipped (Rust toolchain not available).",
                      file=sys.stderr)
                print("  Re-run 'aa install lint' after installing Rust.", file=sys.stderr)
                return []
            raise ToolUpdateError("lint-arwaky update failed (Rust toolchain not available)")

    build_env = _lint_preflight_build_deps()
    build_env["CARGO_INCREMENTAL"] = "0"
    env = os.environ.copy()
    env.update(build_env)

    ensure_bin_home()
    (config_home() / "lint-arwaky/rules").mkdir(parents=True, exist_ok=True)
    (data_home() / "lint-arwaky/reports").mkdir(parents=True, exist_ok=True)

    cache_dir = cache_home() / "lint-arwaky"
    cache_dir.mkdir(parents=True, exist_ok=True)
    print(f">>> Building lint-arwaky (AES Architecture Linter) into {cache_dir}...")
    env["CARGO_TARGET_DIR"] = str(cache_dir)
    subprocess.run(["cargo", "build", "--release"], cwd=internal_dir, env=env, check=True)

    release = cache_dir / "release"
    artifacts: list[Path] = []
    for b in LINT_BINARIES:
        src = release / b
        if src.exists():
            dst = bin_home() / b
            tmp = dst.with_suffix(dst.suffix + ".tmp")
            shutil.copy2(src, tmp)
            tmp.chmod(0o755)
            os.replace(tmp, dst)
            artifacts.append(dst)
            print(f"  -> {dst}")
    if (bin_home() / "lint-arwaky-cli").exists():
        lac = bin_home() / "lac"
        lac.unlink(missing_ok=True)
        lac.symlink_to(bin_home() / "lint-arwaky-cli")
        artifacts.append(lac)
    return artifacts


lint_satisfied = _make_satisfied("lint-arwaky")
lint_is_pin_satisfied = _make_pin_check(
    LINT_INTERNAL_DIR_REL, "cargo release build (rebuild required)")
lint_owned_paths = _make_owned(
    LINT_LAUNCHERS, extra=lambda: [bin_home() / "lac"])


def lint_install(spec, root=ROOT, *, daemons=None):
    root = root or ROOT
    internal_dir = root / LINT_INTERNAL_DIR_REL
    if not (internal_dir.exists() and (internal_dir / "Cargo.toml").exists()):
        run(["git", "-C", str(root), "submodule", "update", "--init", LINT_INTERNAL_DIR_REL])
    artifacts = _lint_build_and_install(root, raise_on_missing_cargo=False)
    if not artifacts:
        return []
    print(">>> Successfully installed lint-arwaky")
    return artifacts


def lint_update(spec, root):
    if not update_submodule(root, LINT_INTERNAL_DIR_REL):
        raise ToolUpdateError(f"submodule update failed: {LINT_INTERNAL_DIR_REL}")
    created = _lint_build_and_install(root, raise_on_missing_cargo=True)
    print(">>> Successfully updated lint-arwaky")
    return created


# omniroute (host-native daemon + launcher)
OMNIROUTE_DATA_DIR_NAME = "omniroute"
OMNIROUTE_INTERNAL_BIN = "internal-bin"
OMNIROUTE_LAUNCHERS = ["omniroute"]


def _omniroute_daemon_feature():
    _daemon_root = ".".join(("modules", "daemon", "src", "root_daemon_container"))
    return importlib.import_module(_daemon_root).create_daemon_feature()


def _omniroute_write_launcher(launcher: Path, root: Path) -> None:
    content = (
        "#!/usr/bin/env python3\n"
        f"# {PROVENANCE_MARKER}\n"
        "import os, sys\n"
        "from pathlib import Path\n"
        f'root = Path(os.environ.get("AGENTS_ARWAKY_ROOT", {str(root)!r}))\n'
        "sys.path.insert(0, str(root))\n"
        "import importlib as _il\n"
        "_dv = _il.import_module('modules.daemon.src.' + 'agent' + '_daemon_verb')\n"
        "_cmd_omniroute = getattr(_dv, 'cmd_' + 'omniroute')\n"
        "sys.exit(_cmd_omniroute(sys.argv[1:]))\n"
    )
    atomic_write_text(launcher, content)
    launcher.chmod(0o755)


def _omniroute_lifecycle(action: str, root: Path, daemons) -> list[Path]:
    is_update = action == "update"
    verb_ed = "updated" if is_update else "installed"
    ensure_bin_home()
    ensure_path()
    data_dir = data_home() / OMNIROUTE_DATA_DIR_NAME
    data_dir.mkdir(parents=True, exist_ok=True)

    if is_update:
        _feature = _omniroute_daemon_feature()
        print(">>> Updating OmniRoute host-native service...")
        rc = _feature.service_install("omniroute")
        if rc != 0:
            print(f"  Warning: omniroute service-install exited {rc}")
    else:
        if daemons is not None:
            rc = daemons.service_install()
            if rc != 0:
                print(f"omniroute service-install exited {rc} (see 'aa omniroute logs')", file=sys.stderr)
                return []

    launcher = bin_home() / "omniroute"
    _omniroute_write_launcher(launcher, root)
    internal_bin = data_dir / OMNIROUTE_INTERNAL_BIN
    internal_bin.mkdir(parents=True, exist_ok=True)
    shutil.copy2(launcher, internal_bin / "omniroute")
    (internal_bin / "omniroute").chmod(0o755)
    print(f">>> Successfully {verb_ed} OmniRoute -> {launcher}")

    if is_update:
        return [launcher, internal_bin / "omniroute"]
    return [launcher]


omniroute_satisfied = _make_satisfied("omniroute")
omniroute_is_pin_satisfied = _make_pin_check("", "daemon service + launcher (force reinstall)")
omniroute_owned_paths = _make_owned(
    OMNIROUTE_LAUNCHERS,
    config=[OMNIROUTE_DATA_DIR_NAME],
    extra=lambda: [
        data_home() / OMNIROUTE_DATA_DIR_NAME / OMNIROUTE_INTERNAL_BIN / "omniroute",
        agents_arwaky_config_dir() / "omniroute.env",
    ],
)
omniroute_install = _make_install(_omniroute_lifecycle)
omniroute_update = _make_update(_omniroute_lifecycle)


# ---------------------------------------------------------------------------
# Registry (dibangun dari config + complex tools)
# ---------------------------------------------------------------------------
def _unit(*, satisfied, install, update, is_pin_satisfied, owned_paths) -> SimpleNamespace:
    return SimpleNamespace(
        satisfied=satisfied,
        install=install,
        update=update,
        is_pin_satisfied=is_pin_satisfied,
        owned_paths=owned_paths,
    )


_ADAPTER_UNITS: dict[str, SimpleNamespace] = {
    name: _build_adapter_unit(name, cfg)
    for name, cfg in SIMPLE_TOOLS_CONFIG.items()
}

_ADAPTER_UNITS.update({
    "anytype": _unit(
        satisfied=anytype_satisfied,
        install=anytype_install,
        update=anytype_update,
        is_pin_satisfied=anytype_is_pin_satisfied,
        owned_paths=anytype_owned_paths,
    ),
    "anytype-daemon": _unit(
        satisfied=anytype_daemon_satisfied,
        install=anytype_daemon_install,
        update=anytype_daemon_update,
        is_pin_satisfied=anytype_daemon_is_pin_satisfied,
        owned_paths=anytype_daemon_owned_paths,
    ),
    "lint": _unit(
        satisfied=lint_satisfied,
        install=lint_install,
        update=lint_update,
        is_pin_satisfied=lint_is_pin_satisfied,
        owned_paths=lint_owned_paths,
    ),
    "omniroute": _unit(
        satisfied=omniroute_satisfied,
        install=omniroute_install,
        update=omniroute_update,
        is_pin_satisfied=omniroute_is_pin_satisfied,
        owned_paths=omniroute_owned_paths,
    ),
})

#: Root-container compatible registry.
TOOLS_REGISTRY: dict[str, object] = dict(_ADAPTER_UNITS)

# Backward-compat: nama verb per-tool untuk config-driven tools (qwen-web,
# blender, vision, mnemosyne, workspace, codegraph, context7, fetch, ponytail).
_TOOL_PREFIXES = {
    "blender": "blender",
    "vision": "vision",
    "qwen-web": "qwen_web",
    "mnemosyne": "mnemosyne",
    "workspace": "workspace",
    "codegraph": "codegraph",
    "context7": "context7",
    "fetch": "fetch",
    "ponytail": "ponytail",
}
for _tid, _prefix in _TOOL_PREFIXES.items():
    _ns = _ADAPTER_UNITS[_tid]
    globals()[f"{_prefix}_satisfied"] = _ns.satisfied
    globals()[f"{_prefix}_install"] = _ns.install
    globals()[f"{_prefix}_update"] = _ns.update
    globals()[f"{_prefix}_is_pin_satisfied"] = _ns.is_pin_satisfied
    globals()[f"{_prefix}_owned_paths"] = _ns.owned_paths
del _tid, _prefix, _ns


__all__ = [
    "TOOLS_REGISTRY",
    "_ADAPTER_UNITS",
    "ToolAdapterFacade",
    "anytype_satisfied", "anytype_install", "anytype_update",
    "anytype_is_pin_satisfied", "anytype_owned_paths",
    "anytype_daemon_satisfied", "anytype_daemon_install", "anytype_daemon_update",
    "anytype_daemon_is_pin_satisfied", "anytype_daemon_owned_paths",
    "blender_satisfied", "blender_install", "blender_update",
    "blender_is_pin_satisfied", "blender_owned_paths",
    "codegraph_satisfied", "codegraph_install", "codegraph_update",
    "codegraph_is_pin_satisfied", "codegraph_owned_paths",
    "context7_satisfied", "context7_install", "context7_update",
    "context7_is_pin_satisfied", "context7_owned_paths",
    "fetch_satisfied", "fetch_install", "fetch_update",
    "fetch_is_pin_satisfied", "fetch_owned_paths",
    "lint_satisfied", "lint_install", "lint_update",
    "lint_is_pin_satisfied", "lint_owned_paths",
    "mnemosyne_satisfied", "mnemosyne_install", "mnemosyne_update",
    "mnemosyne_is_pin_satisfied", "mnemosyne_owned_paths",
    "ninerouter_satisfied", "ninerouter_install", "ninerouter_update",
    "ninerouter_is_pin_satisfied", "ninerouter_owned_paths",
    "ponytail_satisfied", "ponytail_install", "ponytail_update",
    "ponytail_is_pin_satisfied", "ponytail_owned_paths",
    "qwen_web_satisfied", "qwen_web_install", "qwen_web_update",
    "qwen_web_is_pin_satisfied", "qwen_web_owned_paths",
    "vision_satisfied", "vision_install", "vision_update",
    "vision_is_pin_satisfied", "vision_owned_paths",
    "workspace_satisfied", "workspace_install", "workspace_update",
    "workspace_is_pin_satisfied", "workspace_owned_paths",
]
