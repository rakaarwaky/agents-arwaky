#!/usr/bin/env python3
"""Updater fetch-mcp — force reinstall zcaceres/fetch-mcp (TypeScript, bun).

Always removes APP_DIR and rebuilds from source.
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

SRC = ROOT / "vendor/fetch-mcp"
APP_DIR = data_home() / "fetch-mcp"

CLI_ARGS = {"html", "markdown", "readable", "txt", "json", "youtube", "--help", "-h", "--version", "-v"}

IGNORES = shutil.ignore_patterns(
    "node_modules", ".git", "__pycache__", "target", "*.egg-info",
    ".venv", "venv", "*.tsbuildinfo",
)


def run(cmd, cwd=None):
    subprocess.run(cmd, cwd=cwd, check=True)


def _require(tool: str, reason: str) -> bool:
    if shutil.which(tool):
        return True
    print(f"Error: {tool} not found in PATH. {reason}", file=sys.stderr)
    return False


def main() -> int:
    # Pull latest from remote
    sys.path.insert(0, str(ROOT / "tools" / "lib"))
    from git_update import update_submodule
    update_submodule(ROOT, "vendor/fetch-mcp")

    if not (SRC / "package.json").exists():
        print("Error: fetch-mcp source not found (submodule not initialized).", file=sys.stderr)
        return 1
    if not _require("bun", "fetch-mcp requires bun (curl -fsSL https://bun.sh/install | bash)"):
        return 1

    print(f">>> Updating fetch-mcp into {APP_DIR}...")
    if APP_DIR.exists():
        shutil.rmtree(APP_DIR)
    shutil.copytree(SRC, APP_DIR, ignore=IGNORES)

    run(["bun", "install"], APP_DIR)
    run(["bun", "run", "build"], APP_DIR)

    index_js = APP_DIR / "dist/index.js"
    cli_js = APP_DIR / "dist/cli.js"
    if not index_js.exists() or not cli_js.exists():
        print(f"  Error: build output incomplete ({index_js}, {cli_js})", file=sys.stderr)
        return 1

    ensure_bin_home()
    content = (
        "#!/usr/bin/env python3\n"
        "import os, sys\n"
        f'index_js = r"{index_js}"\n'
        f'cli_js = r"{cli_js}"\n'
        "cli = " + repr(sorted(CLI_ARGS)) + "\n"
        "script = cli_js if (len(sys.argv) > 1 and sys.argv[1] in cli) else index_js\n"
        'env = os.environ.copy()\n'
        'os.execvpe("node", ["node", script, *sys.argv[1:]], env)\n'
    )
    for name in ("fetch-mcp", "mcp-fetch"):
        launcher = bin_home() / name
        launcher.write_text(content, encoding="utf-8")
        launcher.chmod(0o755)
        print(f"  -> {launcher}")

    warn_if_bin_not_on_path()
    print(">>> Successfully updated fetch-mcp")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
