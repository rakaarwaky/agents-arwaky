#!/usr/bin/env python3
"""Shared launcher writer (DRY: 5+ uv/python installers pakai ini)."""
from __future__ import annotations

from pathlib import Path

from xdg import bin_home, ensure_bin_home  # noqa: E402


def write_uv_launchers(package_name: str, src_rel: str, launchers: list) -> list:
    """Write uv-run launchers for a Python tool. Returns list of created paths."""
    ensure_bin_home()
    created = []
    for launcher in launchers:
        target = bin_home() / launcher
        content = (
            "#!/usr/bin/env python3\n"
            "import os, sys\n"
            "from pathlib import Path\n"
            'root = Path(os.environ.get("AGENTS_ARWAKY_ROOT", str(Path.home() / "agents-arwaky")))\n'
            f'os.execvpe("uv", ["uv", "run", "--directory", str(root / "{src_rel}"), '
            f'"{launcher}", *sys.argv[1:]], os.environ.copy())\n'
        )
        target.write_text(content, encoding="utf-8")
        target.chmod(0o755)
        created.append(target)
    return created


def write_generic_launcher(tool_name: str, content: str, aliases: list = None) -> Path:
    """Write a generic launcher with aliases. Returns launcher path."""
    ensure_bin_home()
    launcher = bin_home() / tool_name
    launcher.write_text(content, encoding="utf-8")
    launcher.chmod(0o755)
    for alias in (aliases or []):
        a = bin_home() / alias
        a.unlink(missing_ok=True)
        a.symlink_to(launcher)
    return launcher
