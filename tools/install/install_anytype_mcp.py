#!/usr/bin/env python3
"""Installer anytype-mcp — @anyproto/anytype-mcp (TypeScript, bun).

Spesifik: lockfile bun.lock -> `bun install`; build `tsc -build` (outDir ./build)
+ scripts/build-cli.js (outfile bin/cli.mjs). Entry CLI = bin/cli.mjs (BUKAN
dist/cli.mjs — dist tidak pernah dihasilkan). Runtime di-install in-place di
$XDG_DATA_HOME/anytype-mcp agar node_modules hasil bun ikut serta.
"""
from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "lib"))

from xdg import bin_home, data_home, ensure_bin_home, warn_if_bin_not_on_path  # type: ignore[import-not-found]

SRC = ROOT / "vendor/anytype-mcp"
APP_DIR = data_home() / "anytype-mcp"
ENTRY = "bin/cli.mjs"

IGNORES = shutil.ignore_patterns(
    "node_modules", ".git", "__pycache__", "dist", "target", "*.egg-info",
    ".venv", "venv", "*.tsbuildinfo",
)


def run(cmd, cwd=None):
    subprocess.run(cmd, cwd=cwd, check=True)


def main() -> int:
    if not (SRC / "package.json").exists():
        print("Error: anytype-mcp source not found (submodule belum di-init).", file=sys.stderr)
        return 1

    print(f">>> Installing anytype-mcp into {APP_DIR}...")
    if APP_DIR.exists():
        shutil.rmtree(APP_DIR)
    shutil.copytree(SRC, APP_DIR, ignore=IGNORES)

    run(["bun", "install"], APP_DIR)
    run(["bun", "run", "build"], APP_DIR)

    entry = APP_DIR / ENTRY
    if not entry.exists():
        print(f"  Error: entry tidak ditemukan {entry}", file=sys.stderr)
        return 1

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
    print(">>> Successfully installed anytype-mcp")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
