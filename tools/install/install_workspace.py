#!/usr/bin/env python3
"""Installer workspace — google-workspace-mcp (Python, uv)."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "lib"))

from xdg import bin_home, ensure_bin_home, warn_if_bin_not_on_path  # type: ignore[import-not-found]

SRC_REL = "vendor/google-workspace-mcp"
SRC_DIR = ROOT / SRC_REL
# (nama launcher, entry command yang dijalankan via `uv run`)
LAUNCHERS = [('workspace-mcp', 'workspace-mcp'), ('google-workspace-mcp', 'workspace-mcp')]


def run(cmd, cwd=None):
    subprocess.run(cmd, cwd=cwd, check=True)


def _uv_launcher(entry: str) -> str:
    root = repr(str(ROOT))
    return (
        "#!/usr/bin/env python3\n"
        "import os, sys\n"
        "from pathlib import Path\n"
        f'root = Path(os.environ.get("AGENTS_ARWAKY_ROOT", {root}))\n'
        f'os.execvpe("uv", ["uv", "run", "--directory", str(root / "vendor/google-workspace-mcp"), '
        f'"{entry}", *sys.argv[1:]], os.environ.copy())\n'
    )


def main() -> int:
    if not SRC_DIR.exists():
        print(f">>> Initializing submodule {SRC_REL}...", file=sys.stderr)
        run(["git", "-C", str(ROOT), "submodule", "update", "--init", SRC_REL])
    if not SRC_DIR.exists():
        print(f"Error: source tidak ditemukan {SRC_DIR}.", file=sys.stderr)
        return 1

    ensure_bin_home()
    for name, entry in LAUNCHERS:
        launcher = bin_home() / name
        launcher.write_text(_uv_launcher(entry), encoding="utf-8")
        launcher.chmod(0o755)
        print(f"  -> {launcher}")

    warn_if_bin_not_on_path()
    print(">>> Successfully installed " + LAUNCHERS[0][0].split("-")[0])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
