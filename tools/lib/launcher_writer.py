#!/usr/bin/env python3
"""Shared launcher writer (DRY: used by 5+ uv/python installers)."""
from __future__ import annotations

from pathlib import Path

from paths import repo_root  # type: ignore[import-not-found]
from xdg import (  # type: ignore[import-untyped]
    atomic_write_text,
    bin_home,
    ensure_bin_home,
    ensure_path,
    warn_if_bin_not_on_path,
)


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
    baked_root = str(root) if root is not None else str(repo_root())
    extra = "".join(repr(a) + ", " for a in (uv_args or []))
    created = []
    for name, entry in launchers:
        target = bin_home() / name
        content = (
            "#!/usr/bin/env python3\n"
            "import os, sys\n"
            "from pathlib import Path\n"
            f'root = Path(os.environ.get("AGENTS_ARWAKY_ROOT", {repr(baked_root)}))\n'
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
