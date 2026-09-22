"""Shell check capability — shellcheck for our own .sh files."""
from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

from modules.shared.src.contract_check_protocol import ICheckRunner
from modules.shared.src.taxonomy_check_vo import CheckExitCode
from modules.shared.src.taxonomy_common_vo import DocFinding
from modules.shared.src.utility_logging_setup import err, warn
from modules.shared.src.utility_paths_resolver import repo_root

# ─── Block 1: Class Definition & Constructor ──────────────

class ShellCheckRunner(ICheckRunner):
    """Run shellcheck on modules/**/*.sh (upstream skills/ excluded)."""

    def __init__(self, root: Path | None = None) -> None:
        self._root = root or repo_root()

    # ─── Block 2: Protocol ABC Method Implementation ──────────
    def run(self, strict: bool = False) -> CheckExitCode:
        sh_files = self._sh_files()
        if not sh_files:
            return CheckExitCode(0)
        if not shutil.which("shellcheck"):
            warn("shellcheck not installed; skipping .sh lint")
            return CheckExitCode(0)
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
        return CheckExitCode(errors)

    # ─── Block 3: Dunder Methods, Factories & Helpers ───────
    def _sh_files(self) -> list[Path]:
        out: list[Path] = []
        for base in (self._root / "modules",):
            if base.is_dir():
                for path in base.rglob("*.sh"):
                    if "node_modules" not in path.parts and path.relative_to(self._root).parts[0] != "skills":
                        out.append(path)
        return out

__all__ = ['CheckExitCode', 'DocFinding']


# Layer-symbol registry (runtime reference for harness/loader introspection).
_layer_symbols = {"CheckExitCode": CheckExitCode, "DocFinding": DocFinding}
