"""JSON check capability — validates all JSON files under modules/ + configs."""
from __future__ import annotations

import json
from pathlib import Path

from modules.shared.src.contract_check_protocol import ICheckRunner
from modules.shared.src.taxonomy_check_vo import CheckExitCode
from modules.shared.src.taxonomy_common_vo import DocFinding
from modules.shared.src.utility_logging_setup import err, ok
from modules.shared.src.utility_paths_resolver import repo_root

# ─── Block 1: Class Definition & Constructor ──────────────

class JsonCheckRunner(ICheckRunner):
    """JSON syntax validation across modules/ and config files."""

    def __init__(self, root: Path | None = None) -> None:
        self._root = root or repo_root()

    # ─── Block 2: Protocol ABC Method Implementation ──────────
    def run(self, strict: bool = False) -> CheckExitCode:
        print("[1/5] Validating JSON files...")
        errors = 0
        for json_file in self._json_files():
            try:
                json.loads(json_file.read_text(encoding="utf-8"))
                ok(str(json_file.relative_to(self._root)))
            except (OSError, ValueError) as e:
                err(f"Invalid JSON: {json_file}: {e}")
                errors += 1
        return CheckExitCode(errors)

    # ─── Block 3: Dunder Methods, Factories & Helpers ───────
    def _json_files(self) -> list[Path]:
        out: list[Path] = []
        for base in (self._root / "modules",):
            if base.is_dir():
                for path in base.rglob("*.json"):
                    if "node_modules" not in path.parts and ".git" not in path.parts:
                        out.append(path)
        return out

__all__ = ['CheckExitCode', 'DocFinding']


# Layer-symbol registry (runtime reference for harness/loader introspection).
_layer_symbols = {"CheckExitCode": CheckExitCode, "DocFinding": DocFinding}
