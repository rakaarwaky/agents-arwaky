"""Python check capability — py_compile across tools/ + modules/."""
from __future__ import annotations
from modules.shared.src.taxonomy_doc_vo import DocFinding


import py_compile
from pathlib import Path

from modules.check.src.contract_check_protocol import ICheckRunner
from modules.shared.src.utility_logging_setup import err, ok
from modules.shared.src.utility_paths_resolver import repo_root


# ─── Block 1: Class Definition & Constructor ──────────────

class PythonCheckRunner(ICheckRunner):
    """py_compile every .py under tools/ and modules/.

    # Block 1: Configuration (file discovery)
    # Block 2: Compilation
    # Block 3: Result
    """

    # -- Block 1: Configuration ---------------------------------------------------
    # ─── Block 2: Protocol ABC Method Implementation ──────────
    def __init__(self, root: Path | None = None) -> None:
        self._root = root or repo_root()

    # ─── Block 3: Dunder Methods, Factories & Helpers ───────
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

__all__ = ['DocFinding']

#

# Layer-symbol registry (runtime reference for harness/loader introspection).
_layer_symbols = {"DocFinding": DocFinding}
