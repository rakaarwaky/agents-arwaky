"""Tool install mechanics — shared free functions for every tools adapter.

Factories, launcher writers, XDG path helpers, the node-family lifecycle,
the venv/uv lifecycles, the generic unit builder, and the shared protocol
dispatcher. Consumed by the nine provider modules
`capabilities_tools_{blender,vision,qwen_web,mnemosyne,workspace,
codegraph,context7,fetch,ponytail}_adapter` plus
`capabilities_tools_{adapter,anytype_adapter,lint_adapter,
ninerouter_adapter}` (≥2 consumers). Taxonomy + `utility_git_submodule`
only (AES201 exception registered for the utility→utility edge — same
pattern as `utility_config_engine`).
"""
from __future__ import annotations

import contextlib
import json
import shutil
import subprocess
import sys
from collections.abc import Callable
from pathlib import Path

from modules.shared.src.taxonomy_common_constant import PROVENANCE_MARKER, REPO_ROOT
from modules.shared.src.taxonomy_common_error import ToolUpdateError
from modules.shared.src.taxonomy_common_vo import (
    ToolSpec,
    atomic_write_text,
    bin_home,
    cache_home,
    config_home,
    data_home,
    ensure_bin_home,
    ensure_path,
    tool_cache_dir,
    tool_config_dir,
    tool_data_dir,
    tool_state_dir,
    utc_now_iso,
    warn_if_bin_not_on_path,
)
from modules.shared.src.taxonomy_tools_constant import (
    INSTALL_STAMP_FILENAME,
    NODE_IGNORES,
    ROOT_ENV_VAR,
)
from modules.shared.src.taxonomy_tools_vo import AdapterUnit, ToolLifecycleConfig
from modules.shared.src.utility_git_submodule import (
    ensure_source,
    get_current_commit,
    update_submodule,
)

#: Effective repository root for default lifecycle arguments.
ROOT = REPO_ROOT


# ---------------------------------------------------------------------------
# Top-level factories (DRY core — dipakai di seluruh adapter)
# ---------------------------------------------------------------------------
def make_satisfied(bin_name: str) -> Callable:
    """Factory: satisfied probe — cek keberadaan satu launcher di XDG bin."""
    return lambda spec, root=None: (bin_home() / bin_name).exists()


def make_multi_satisfied(bin_names: list[str]) -> Callable:
    """Factory: satisfied probe — semua launcher harus ada."""
    return lambda spec, root=None: all((bin_home() / b).exists() for b in bin_names)


def make_pin_check(src_rel: str, reason: str) -> Callable:
    """Factory: pin-check — (False, reason) kecuali submodule belum init."""
    return lambda spec, root: (
        (False, "submodule not initialized")
        if src_rel and not (root / src_rel).exists()
        else (False, reason)
    )


def make_owned(
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


def make_install(lifecycle_fn: Callable) -> Callable:
    """Factory: install wrapper — signature (spec, root=ROOT, *, daemons=None)."""
    return lambda spec, root=ROOT, *, daemons=None: lifecycle_fn("install", root or ROOT, daemons)


def make_update(lifecycle_fn: Callable) -> Callable:
    """Factory: update wrapper — signature (spec, root)."""
    return lambda spec, root: lifecycle_fn("update", root or ROOT, None)


# ---------------------------------------------------------------------------
# Pure path / process helpers
# ---------------------------------------------------------------------------
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


# ---------------------------------------------------------------------------
# Launcher writers
# ---------------------------------------------------------------------------
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
            f'root = Path(os.environ.get("{ROOT_ENV_VAR}", {baked_root!r}))\n'
            f'os.execvpe("uv", ["uv", "run", {extra}"--directory", str(root / "{src_rel}"), '
            f'"{entry}", *sys.argv[1:]], os.environ.copy())\n'
        )
        atomic_write_text(target, content)
        created.append(target)
    warn_if_bin_not_on_path()
    ensure_path()
    return created


# ---------------------------------------------------------------------------
# venv lifecycle (uv_venv family: blender / vision / qwen-web)
# ---------------------------------------------------------------------------
def _write_install_stamp(app_dir: Path, tool: str, submodule_dir: Path) -> None:
    """Record what was deployed so rollback/audit is possible."""
    stamp = {
        "tool": tool,
        "commit": get_current_commit(submodule_dir) or "unknown",
        "installed_at": utc_now_iso(),
    }
    try:
        app_dir.mkdir(parents=True, exist_ok=True)
        (app_dir / INSTALL_STAMP_FILENAME).write_text(
            json.dumps(stamp, indent=2) + "\n", encoding="utf-8"
        )
    except OSError as exc:
        print(f"  Warning: could not write install stamp: {exc}", file=sys.stderr)


def _ensure_venv(tool_name: str, force: bool = False) -> Path:
    """Create venv in XDG data directory. If force=True, recreate even if exists."""
    venv_dir = _get_venv_dir(tool_name)
    python_bin = _get_venv_python(venv_dir)
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
    subprocess.run([str(_get_venv_python(venv_dir)), "-m", "ensurepip", "--upgrade"], check=True)
    python_bin = _get_venv_python(venv_dir)
    print(f"  [ok] Venv created: {python_bin}")
    return python_bin


def _install_package(python_bin: Path, src_dir: Path, tool_name: str) -> None:
    print(f"  [install] Installing {tool_name} package...")
    subprocess.run([str(python_bin), "-m", "pip", "install", "-e", str(src_dir)], check=True)


def _setup_bin_links(python_bin: Path, launchers: list[tuple[str, str]]) -> None:
    """Create symlinks in ~/.local/bin/. launchers = [(name, entrypoint), ...]"""
    ensure_bin_home()
    local_bin = bin_home()
    venv_bin_dir = python_bin.parent
    print(f"  [install] Creating launchers in {local_bin}...")
    for name, _entry in launchers:
        src = venv_bin_dir / name
        dst = local_bin / name
        if src.exists():
            dst.unlink(missing_ok=True)
            with contextlib.suppress(OSError):
                dst.symlink_to(src)
                print(f"  [ok] {dst} -> {src}")
    warn_if_bin_not_on_path()


def _setup_xdg_directories(tool_name: str) -> None:
    print(f"  [install] Creating XDG directories for {tool_name}...")
    tool_data_dir(tool_name)
    tool_config_dir(tool_name)
    tool_state_dir(tool_name)
    tool_cache_dir(tool_name)
    print(f"  [ok] Data: {tool_data_dir(tool_name)}")
    print(f"  [ok] Config: {tool_config_dir(tool_name)}")
    print(f"  [ok] State: {tool_state_dir(tool_name)}")
    print(f"  [ok] Cache: {tool_cache_dir(tool_name)}")


def _get_venv_dir(tool_name: str) -> Path:
    """XDG-compliant venv directory: ~/.local/share/<tool>/venv/"""
    return tool_data_dir(tool_name) / "venv"


def _get_venv_python(venv_dir: Path) -> Path:
    return venv_dir / "bin" / "python"


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
        python_bin = _ensure_venv(tool_name, force=True)
    else:
        src_dir = root / src_rel
        source = ensure_source(root, src_rel)
        if not source.exists():
            raise err_cls(f"source not found {src_dir}")
        python_bin = _ensure_venv(tool_name, force=False)

    _install_package(python_bin, source, tool_name)
    if post_install_hook:
        post_install_hook(python_bin, source)
    _setup_xdg_directories(tool_name)
    _setup_bin_links(python_bin, launchers)

    if is_update:
        _write_install_stamp(python_bin.parent.parent, tool_name, source)
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
    progress_ed = "updated" if is_update else "installed"

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
    print(f">>> Successfully {progress_ed} {tool_name}")
    return created


# ---------------------------------------------------------------------------
# Node-family lifecycle (shared by config-driven node tools + anytype MCP)
# ---------------------------------------------------------------------------
def node_tool_lifecycle(
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
    progress_ing = "Updating" if is_update else "Installing"
    progress_ed = "updated" if is_update else "installed"

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
    print(f">>> {progress_ing} {app_name} into {app_dir}...")
    copy_app(source, app_dir, ignores)

    if post_copy_hook:
        post_copy_hook(app_dir)
    if install_cmd:
        run(install_cmd, app_dir)
    if build_cmd:
        run(build_cmd, app_dir)

    artifacts = write_launchers_fn(app_dir, is_update)
    finish_bin()
    print(f">>> Successfully {progress_ed} {app_name}")
    return artifacts


# ---------------------------------------------------------------------------
# Generic unit builder (config-driven recipes → AdapterUnit)
# ---------------------------------------------------------------------------
def build_adapter_unit(name: str, config: ToolLifecycleConfig) -> AdapterUnit:
    """Build the complete adapter unit for one config-driven tool recipe.

    Lifecycle branches: `uv_venv` (blender/vision/qwen-web), `uv_project`
    (mnemosyne/workspace), `node` (codegraph/context7/fetch/ponytail).
    Node launchers default to a primary `launchers[0]` entry launcher plus
    symlinks for `launchers[1:]`; per-tool overrides arrive as
    `config.node_write_launchers_fn` / `config.node_post_copy_hook`.
    """
    lifecycle = config.lifecycle
    src_rel = config.src_rel
    tool_name = config.tool_name or name
    launchers = list(config.launchers)

    satisfied = make_satisfied(config.satisfied_bin)
    is_pin_satisfied = make_pin_check(src_rel, config.pin_reason)
    owned_paths = make_owned(
        launchers,
        extra=list(config.extra_paths) if config.extra_paths else None,
        config=list(config.config_dirs) if config.config_dirs else None,
        extra_fn=config.extra_paths_fn,
    )

    if lifecycle == "uv_venv":
        post_install = config.post_install_hook
        init_msg = config.init_message

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
        uv_args = list(config.uv_args) if config.uv_args else None
        alias_second = config.alias_second_to_first

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
        app_name = config.app_name or tool_name
        entry = config.entry
        ignores = list(config.ignores) if config.ignores else list(NODE_IGNORES)
        requires = config.requires
        src_marker = config.src_marker
        install_cmd = list(config.install_cmd)
        build_cmd = list(config.build_cmd)
        post_copy_hook = config.node_post_copy_hook
        write_launchers = config.node_write_launchers_fn

        if write_launchers is None:
            if entry is None:
                raise ValueError(
                    f"node recipe {name!r} needs entry= or node_write_launchers_fn"
                )

            def write_launchers(app_dir, is_update):
                entry_path = app_dir / entry
                if not entry_path.exists():
                    raise (ToolUpdateError if is_update else FileNotFoundError)(
                        f"entry not found {entry_path}")
                created = [write_node_launcher(launchers[0], entry_path)]
                created += [
                    symlink_alias(n, bin_home() / launchers[0])
                    for n in launchers[1:]
                ]
                return created

        def install(spec, root=ROOT, *, daemons=None):
            return node_tool_lifecycle(
                "install", root or ROOT, src_rel, app_name,
                install_cmd, build_cmd, ignores, requires, src_marker,
                write_launchers, post_copy_hook,
            )

        def update(spec, root):
            return node_tool_lifecycle(
                "update", root, src_rel, app_name,
                install_cmd, build_cmd, ignores, requires, src_marker,
                write_launchers, post_copy_hook,
            )
    else:
        raise ValueError(f"unknown lifecycle {lifecycle!r} for tool {name!r}")

    return AdapterUnit(
        satisfied=satisfied,
        install=install,
        update=update,
        is_pin_satisfied=is_pin_satisfied,
        owned_paths=owned_paths,
    )


# ---------------------------------------------------------------------------
# Shared protocol dispatcher (per-provider IToolsProtocol.execute bodies)
# ---------------------------------------------------------------------------
def dispatch_unit_op(
    units: dict[str, AdapterUnit],
    op: str,
    spec: ToolSpec | None = None,
    query: object | None = None,
    args: list[str] | None = None,
    *,
    label: str,
) -> object:
    """Dispatch one `IToolsProtocol.execute` call against *units*.

    Shared body of every provider adapter's `execute`: resolve the unit
    for *spec*, then route `satisfied` / `is_pin_satisfied` /
    `owned_paths` / `install` / `update` (install retries without the
    injected `daemons` kwarg when the unit rejects it).
    """
    if spec is None:
        raise ToolUpdateError(f"{label} got op={op!r} without a spec")
    unit = units.get(spec.id)
    if unit is None:
        raise ToolUpdateError(f"{label} has no unit for {spec.id!r}")
    root = Path(args[0]) if args else None
    if op == "satisfied":
        return unit.satisfied(spec, root)
    if op == "is_pin_satisfied":
        return unit.is_pin_satisfied(spec, root or ROOT)
    if op == "owned_paths":
        return unit.owned_paths(spec, root or ROOT)
    if op == "install":
        try:
            return list(unit.install(spec, root or ROOT, daemons=query) or [])
        except TypeError:
            return list(unit.install(spec, root or ROOT) or [])
    if op == "update":
        return list(unit.update(spec, root or ROOT) or [])
    raise ToolUpdateError(f"unsupported {label} op {op!r}")


__all__ = [
    "ROOT",
    "build_adapter_unit",
    "copy_app",
    "dispatch_unit_op",
    "finish_bin",
    "generic_owned",
    "make_install",
    "make_multi_satisfied",
    "make_owned",
    "make_pin_check",
    "make_satisfied",
    "make_update",
    "node_tool_lifecycle",
    "require",
    "run",
    "symlink_alias",
    "write_generic_launcher",
    "write_node_entry_launcher",
    "write_node_launcher",
    "write_uv_launchers",
]
