#!/usr/bin/env python3
"""Installer context7 — @upstash/context7 (pnpm monorepo: MCP server + CLI).

Specifics: context7 is a pnpm workspace, not a regular bun/npm project.
- Install deps with `pnpm install` (required, lockfile pnpm-lock.yaml)
- pnpm blocks postinstall deps by default -> allow via
  `dangerouslyAllowAllBuilds: true` in the copied pnpm-workspace.yaml
- Runtime installed in-place to $XDG_DATA_HOME/context7 (deps are linked
  within the workspace, cannot be copied piecemeal)
- Launchers: context7-mcp -> packages/mcp/dist/index.js,
  ctx7 -> packages/cli/dist/index.js
"""
from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "lib"))

from xdg import (  
    atomic_write_text,
    bin_home,
    data_home,
    ensure_bin_home,
    warn_if_bin_not_on_path,
)

SRC = ROOT / "vendor/context7"
APP_DIR = data_home() / "context7"
# Vendor artifacts that must not be included: stale node_modules (may contain
# broken symlinks), git, old build output, etc.
IGNORES = shutil.ignore_patterns(
    "node_modules", ".git", ".old_modules*", "__pycache__", "mcpb",
    "dist", "target", "*.egg-info", ".venv", "venv", ".next", ".turbo",
)

LAUNCHERS = {
    "context7-mcp": "packages/mcp/dist/index.js",
    "ctx7": "packages/cli/dist/index.js",
}
def run(cmd, cwd=None):
    subprocess.run(cmd, cwd=cwd, check=True)
def main() -> int:
    if not (SRC / "pnpm-workspace.yaml").exists():
        print("Error: context7 source not found (submodule not initialized).", file=sys.stderr)
        return 1
    if not shutil.which("pnpm"):
        print("Error: pnpm is required (context7 is a pnpm workspace).", file=sys.stderr)
        return 1

    print(f">>> Installing context7 (pnpm workspace) into {APP_DIR}...")
    if APP_DIR.exists():
        shutil.rmtree(APP_DIR)
    shutil.copytree(SRC, APP_DIR, ignore=IGNORES)

    # pnpm blocks postinstall deps by default -> allow in this copy only
    ws = APP_DIR / "pnpm-workspace.yaml"
    if "dangerouslyAllowAllBuilds" not in ws.read_text(encoding="utf-8", errors="replace"):
        with ws.open("a", encoding="utf-8") as f:
            f.write("\ndangerouslyAllowAllBuilds: true\n")

    run(["pnpm", "install"], APP_DIR)
    run(["pnpm", "run", "build"], APP_DIR)

    ensure_bin_home()
    for name, entry in LAUNCHERS.items():
        target = APP_DIR / entry
        if not target.exists():
            print(f"  Warning: entry not found {target}", file=sys.stderr)
            continue
        launcher = bin_home() / name
        atomic_write_text(launcher,
            "#!/usr/bin/env python3\n"
            "import os, sys\n"
            f'entry = r"{target}"\n'
            'os.execvpe("node", ["node", entry, *sys.argv[1:]], os.environ.copy())\n')
        print(f"  -> {launcher}")

    warn_if_bin_not_on_path()
    print(">>> Successfully installed context7")
    return 0
if __name__ == "__main__":
    raise SystemExit(main())
