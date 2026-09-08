#!/usr/bin/env python3
"""Installer anytype-daemon — headless Anytype container daemon (podman + systemd).

Specifics: anytype-daemon is a container service (not a tool binary).
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
)

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
def main() -> int:
    if not shutil.which("podman") and not shutil.which("docker"):
        print("Warning: podman/docker not found; anytype-daemon skipped.", file=sys.stderr)
        print("  Install podman then re-run 'aa install anytype-daemon'.", file=sys.stderr)
        return 0

    ensure_bin_home()
    ensure_path()
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
if __name__ == "__main__":
    raise SystemExit(main())
