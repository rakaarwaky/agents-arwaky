#!/usr/bin/env python3
"""Shared launcher writer (DRY: 5+ uv/python installers pakai ini)."""
from __future__ import annotations

from pathlib import Path

from paths import repo_root  # type: ignore[import-not-found]
from xdg import bin_home, ensure_bin_home, ensure_path, warn_if_bin_not_on_path  # type: ignore[import-untyped]


def write_uv_launchers(
    package_name: str,
    src_rel: str,
    launchers: list,
    root: Path | None = None,
) -> list:
    """Write uv-run launchers for a Python tool. Returns list of created paths."""
    ensure_bin_home()
    # Bake actual install-time ROOT sebagai fallback (bukan hardcode ~/agents-arwaky),
    # tetap hormati AGENTS_ARWAKY_ROOT bila diset runtime.
    baked_root = str(root) if root is not None else str(repo_root())
    created = []
    for launcher in launchers:
        target = bin_home() / launcher
        content = (
            "#!/usr/bin/env python3\n"
            "import os, sys\n"
            "from pathlib import Path\n"
            f'root = Path(os.environ.get("AGENTS_ARWAKY_ROOT", {repr(baked_root)}))\n'
            f'os.execvpe("uv", ["uv", "run", "--directory", str(root / "{src_rel}"), '
            f'"{launcher}", *sys.argv[1:]], os.environ.copy())\n'
        )
        target.write_text(content, encoding="utf-8")
        target.chmod(0o755)
        created.append(target)
    warn_if_bin_not_on_path()
    ensure_path()
    return created


def write_generic_launcher(tool_name: str, content: str, aliases: list[str] | None = None) -> Path:
    """Write a generic launcher with aliases. Returns launcher path."""
    ensure_bin_home()
    launcher = bin_home() / tool_name
    launcher.write_text(content, encoding="utf-8")
    launcher.chmod(0o755)
    for alias in (aliases or []):
        a = bin_home() / alias
        a.unlink(missing_ok=True)
        a.symlink_to(launcher)
    warn_if_bin_not_on_path()
    ensure_path()
    return launcher
