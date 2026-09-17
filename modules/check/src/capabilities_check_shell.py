"""Shell check capability — shellcheck for our own .sh files."""
from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

from modules.shared.src.check.contract_check_protocol import ICheckRunner
from modules.shared.src.logging.utility_logging import err, ok, warn
from modules.shared.src.paths.utility_paths import repo_root


class ShellCheckRunner(ICheckRunner):
    """Run shellcheck on tools/**/*.sh (upstream skills/ excluded).

    # Block 1: Configuration (file discovery)
    # Block 2: shellcheck execution
    # Block 3: Result
    """

    # -- Block 1: Configuration ---------------------------------------------------
    def __init__(self, root: Path | None = None) -> None:
        self._root = root or repo_root()

    def _sh_files(self) -> list[Path]:
        out: list[Path] = []
        for base in (self._root / "tools", self._root / "modules"):
            if base.is_dir():
                for path in base.rglob("*.sh"):
                    if "node_modules" not in path.parts and path.relative_to(self._root).parts[0] != "skills":
                        out.append(path)
        return out

    # -- Block 2: shellcheck execution --------------------------------------------------
    def run(self, strict: bool = False) -> int:
        sh_files = self._sh_files()
        if not sh_files:
            return 0
        if not shutil.which("shellcheck"):
            warn("shellcheck not installed; skipping .sh lint")
            return 0
        print("[5/5] Running shellcheck...")
        errors = 0
        for f in sh_files:
            try:
                res = subprocess.run(
                    ["shellcheck", "-x", str(f)],
                    capture_output=True, text=True, input="", timeout=15, check=False,
                )
            except subprocess.TimeoutExpired:
                err(f"shellcheck timeout: {f}")
                errors += 1
                continue
            if res.returncode != 0:
                for line in res.stdout.strip().splitlines()[:3]:
                    err(f"shellcheck {f}: {line}")
                errors += 1
        return errors
