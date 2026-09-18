"""JSON check capability — validates all JSON files under tools/ + configs."""
from __future__ import annotations

import json
from pathlib import Path

from modules.shared.src.check.contract_check_protocol import ICheckRunner
from modules.shared.src.logging.utility_logging import err, ok
from modules.shared.src.paths.utility_paths import repo_root


class JsonCheckRunner(ICheckRunner):
    """JSON syntax validation across tools/ and config files.

    # Block 1: Configuration (file discovery)
    # Block 2: Validation
    # Block 3: Result
    """

    # -- Block 1: Configuration ---------------------------------------------------
    def __init__(self, root: Path | None = None) -> None:
        self._root = root or repo_root()

    def _json_files(self) -> list[Path]:
        out: list[Path] = []
        for base in (self._root / "modules",):
            if base.is_dir():
                for path in base.rglob("*.json"):
                    if "node_modules" not in path.parts and ".git" not in path.parts:
                        out.append(path)
        return out

    # -- Block 2: Validation ---------------------------------------------------------
    def run(self, strict: bool = False) -> int:
        print("[1/5] Validating JSON files...")
        errors = 0
        for json_file in self._json_files():
            try:
                json.loads(json_file.read_text(encoding="utf-8"))
                ok(str(json_file.relative_to(self._root)))
            except (OSError, ValueError) as e:
                err(f"Invalid JSON: {json_file}: {e}")
                errors += 1
        return errors
