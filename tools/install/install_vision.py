#!/usr/bin/env python3
"""vision installer (Python)."""
from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "lib"))

from xdg import bin_home, ensure_bin_home  # noqa: E402

SRC_DIR = ROOT / "internal/vision-arwaky"


def run(cmd, cwd=None):
    subprocess.run(cmd, cwd=cwd, check=True)


def main() -> int:
    if not SRC_DIR.exists():
        print(f">>> Initializing submodule {SRC_DIR}...", file=sys.stderr)
        run(["git", "-C", str(ROOT), "submodule", "update", "--init", "internal/vision-arwaky"])
    ensure_bin_home()
    print(f">>> Installing vision launchers to {bin_home()}...")
    for launcher in ['vision-arwaky', 'vision-arwaky-cli', 'va', 'vision-arwaky-mcp']:
        target = bin_home() / launcher
        content = "#!/usr/bin/env python3\nimport os, sys\nfrom pathlib import Path\nroot = Path(os.environ.get(\"AGENTS_ARWAKY_ROOT\", str(Path.home() / \"agents-arwaky\")))\nos.execvpe(\"uv\", [\"uv\", \"run\", \"--directory\", str(root / \"internal/vision-arwaky\"), \"vision-arwaky\", *sys.argv[1:]], os.environ.copy())\n"
        target.write_text(content, encoding="utf-8")
        target.chmod(0o755)
    print(f">>> Successfully installed vision -> {bin_home()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
