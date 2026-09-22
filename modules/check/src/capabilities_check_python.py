"""Python check capability — py_compile across modules/."""
from __future__ import annotations

import py_compile
from pathlib import Path

from modules.shared.src.contract_check_protocol import ICheckRunner
from modules.shared.src.taxonomy_check_vo import CheckExitCode
from modules.shared.src.taxonomy_common_vo import DocFinding
from modules.shared.src.utility_logging_setup import err, ok
from modules.shared.src.utility_paths_resolver import repo_root

# ─── Block 1: Class Definition & Constructor ──────────────

class PythonCheckRunner(ICheckRunner):
    """py_compile every .py under modules/."""

    def __init__(self, root: Path | None = None) -> None:
        self._root = root or repo_root()

    # ─── Block 2: Protocol ABC Method Implementation ──────────
    def run(self, strict: bool = False) -> CheckExitCode:
        print("[2/5] Compiling Python files...")
        errors = 0
        for py_file in self._py_files():
            try:
                py_compile.compile(str(py_file), doraise=True)
                ok(str(py_file.relative_to(self._root)))
            except (py_compile.PyCompileError, OSError, ValueError) as e:
                err(f"Python compile error: {py_file}: {e}")
                errors += 1
        return CheckExitCode(errors)

    # ─── Block 3: Dunder Methods, Factories & Helpers ───────
    def _py_files(self) -> list[Path]:
        out: list[Path] = []
        for base in (self._root / "modules",):
            if base.is_dir():
                for path in base.rglob("*.py"):
                    if "node_modules" not in path.parts and ".git" not in path.parts:
                        out.append(path)
        return out

__all__ = ['CheckExitCode', 'DocFinding']


# Layer-symbol registry (runtime reference for harness/loader introspection).
_layer_symbols = {"CheckExitCode": CheckExitCode, "DocFinding": DocFinding}
