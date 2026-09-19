"""Launcher write mechanics (utility layer) — write/chmod delegated by the launcher capability.

Used by the uv/python and node adapter families; shared importers outside this
feature (updater) rely on these symbols staying here.
"""
from __future__ import annotations

import stat
from pathlib import Path

from modules.shared.src.taxonomy_paths_constant import PROVENANCE_MARKER
from modules.shared.src.taxonomy_paths_constant import REPO_ROOT as repo_root
from modules.shared.src.taxonomy_xdg_atomic_io import (
    atomic_write_text,
    ensure_bin_home,
    ensure_path,
    warn_if_bin_not_on_path,
)
from modules.shared.src.taxonomy_xdg_paths import bin_home


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


def write_python_module_launcher(name: str, launcher_code: str, aliases: list[str] | None = None) -> Path:
    """Write a python3 launcher baking in arbitrary launcher code. Returns path."""
    ensure_bin_home()
    launcher = bin_home() / name
    content = (
        "#!/usr/bin/env python3\n"
        f"# {PROVENANCE_MARKER}\n"
        "import os, sys\n"
        f"from pathlib import Path\n{launcher_code}"
    )
    atomic_write_text(launcher, content)
    for alias in (aliases or []):
        a = bin_home() / alias
        a.unlink(missing_ok=True)
        a.symlink_to(launcher)
    return launcher


def symlink_alias(alias: str, target: Path) -> Path:
    """Symlink *alias* in XDG bin pointing at *target* (idempotent)."""
    ensure_bin_home()
    a = bin_home() / alias
    a.unlink(missing_ok=True)
    a.symlink_to(target)
    return a


def ensure_executable(path: Path) -> None:
    """Set the user-executable bit on an existing file."""
    st = path.stat()
    if not st.st_mode & stat.S_IXUSR:
        path.chmod(st.st_mode | stat.S_IXUSR)


__all__ = [
    "ensure_executable",
    "symlink_alias",
    "write_generic_launcher",
    "write_node_entry_launcher",
    "write_python_module_launcher",
    "write_uv_launchers",
]
