#!/usr/bin/env python3
"""Installer anytype (MERGED) — anytype-mcp + anytype-daemon.

Merged installer: `aa install anytype` installs BOTH components in one command.
1. anytype-mcp     — @anyproto/anytype-mcp (TypeScript, bun) MCP server
2. anytype-daemon  — headless Anytype container daemon (podman + systemd)

Specifics (mcp): lockfile bun.lock -> `bun install`; build `tsc -build`
(outDir ./build) + scripts/build-cli.js (outfile bin/cli.mjs). Entry CLI =
bin/cli.mjs (NOT dist/cli.mjs — dist is never generated). Runtime installed
in-place at $XDG_DATA_HOME/anytype-mcp so bun node_modules are included.

Specifics (daemon): container service (not a tool binary).
- Prerequisite: podman/docker
- service-install: register systemd user unit (tools/deploy/anytype-daemon.service)
- Launcher `anytype-daemon` + alias `ad` -> tools/daemons/anytype_daemon.py
- Launcher copy placed in internal-bin (same pattern as 9router)
"""
from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "lib"))

from xdg import (
    bin_home,
    data_home,
    ensure_bin_home,
    ensure_path,
    warn_if_bin_not_on_path,
)

# ---------------------------------------------------------------------------
# anytype-mcp
# ---------------------------------------------------------------------------
SRC = ROOT / "vendor/anytype-mcp"
APP_DIR = data_home() / "anytype-mcp"
ENTRY = "bin/cli.mjs"

IGNORES = shutil.ignore_patterns(
    "node_modules", ".git", "__pycache__", "dist", "target", "*.egg-info",
    ".venv", "venv", "*.tsbuildinfo",
)

def run(cmd, cwd=None):
    subprocess.run(cmd, cwd=cwd, check=True)

def _require(tool: str, reason: str) -> bool:
    if shutil.which(tool):
        return True
    print(f"Error: {tool} not found in PATH. {reason}", file=sys.stderr)
    return False

def install_mcp() -> int:
    if not (SRC / "package.json").exists():
        print("Error: anytype-mcp source not found (submodule not initialized).", file=sys.stderr)
        return 1
    if not _require("bun", "anytype-mcp requires bun (curl -fsSL https://bun.sh/install | bash)"):
        return 1

    print(f">>> Installing anytype-mcp into {APP_DIR}...")
    if APP_DIR.exists():
        shutil.rmtree(APP_DIR)
    shutil.copytree(SRC, APP_DIR, ignore=IGNORES)

    run(["bun", "install"], APP_DIR)
    run(["bun", "run", "build"], APP_DIR)

    entry = APP_DIR / ENTRY
    if not entry.exists():
        print(f"  Error: entry not found {entry}", file=sys.stderr)
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

# ---------------------------------------------------------------------------
# anytype-daemon
# ---------------------------------------------------------------------------
TOOL_DIR = ROOT / "tools/daemons"
DATA_DIR = data_home() / "anytype-daemon"
INTERNAL_BIN = DATA_DIR / "internal-bin"

def _write_launcher(path: Path) -> None:
    path.write_text(
        "#!/usr/bin/env python3\n"
        "import os, sys\n"
        "from pathlib import Path\n"
        f'root = Path(os.environ.get("AGENTS_ARWAKY_ROOT", {repr(str(ROOT))}))\n'  # noqa: RUF010
        'daemon = root / "tools/daemons/anytype_daemon.py"\n'
        'os.execvpe("python3", ["python3", str(daemon), *sys.argv[1:]], os.environ.copy())\n',
        encoding="utf-8",
    )
    path.chmod(0o755)

def install_daemon() -> int:
    if not shutil.which("podman") and not shutil.which("docker"):
        print("Warning: podman/docker not found; anytype-daemon skipped.", file=sys.stderr)
        print("  Install podman then re-run 'aa install anytype'.", file=sys.stderr)
        return 0

    ensure_bin_home()
    ensure_path()
    # Buat folder volume mount dulu agar unit systemd bisa langsung start (24/7)
    for d in ("data", "dot-anytype", "config", "share"):
        (DATA_DIR / d).mkdir(parents=True, exist_ok=True)
    daemon_py = TOOL_DIR / "anytype_daemon.py"
    print(">>> Setting up anytype-daemon (container + systemd user service)...")
    if daemon_py.exists():
        subprocess.run([sys.executable, str(daemon_py), "service-install"], check=False)

    launcher = bin_home() / "anytype-daemon"
    _write_launcher(launcher)
    alias = bin_home() / "ad"
    alias.unlink(missing_ok=True)
    alias.symlink_to(launcher)

    INTERNAL_BIN.mkdir(parents=True, exist_ok=True)
    internal = INTERNAL_BIN / "anytype-daemon"
    _write_launcher(internal)

    print(f">>> Successfully installed anytype-daemon -> {launcher} (alias ad)")
    return 0

def main() -> int:
    rc = install_mcp()
    if rc != 0:
        return rc
    return install_daemon()

if __name__ == "__main__":
    raise SystemExit(main())
