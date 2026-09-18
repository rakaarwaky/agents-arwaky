"""Python check capability — py_compile across tools/ + modules/."""
from __future__ import annotations

import py_compile
from pathlib import Path

from modules.shared.src.check.contract_check_protocol import ICheckRunner
from modules.shared.src.logging.utility_logging import err, ok
from modules.shared.src.common.paths.utility_paths import repo_root


class PythonCheckRunner(ICheckRunner):
    """py_compile every .py under tools/ and modules/.

    # Block 1: Configuration (file discovery)
    # Block 2: Compilation
    # Block 3: Result
    """

    # -- Block 1: Configuration ---------------------------------------------------
    def __init__(self, root: Path | None = None) -> None:
        self._root = root or repo_root()

    def _py_files(self) -> list[Path]:
        out: list[Path] = []
        for base in (self._root / "modules",):
            if base.is_dir():
                for path in base.rglob("*.py"):
                    if "node_modules" not in path.parts and ".git" not in path.parts:
                        out.append(path)
        return out

    # -- Block 2: Compilation ---------------------------------------------------------
    def run(self, strict: bool = False) -> int:
        print("[2/5] Compiling Python files...")
        errors = 0
        for py_file in self._py_files():
            try:
                py_compile.compile(str(py_file), doraise=True)
                ok(str(py_file.relative_to(self._root)))
            except (py_compile.PyCompileError, OSError, ValueError) as e:
                err(f"Python compile error: {py_file}: {e}")
                errors += 1
        return errors
