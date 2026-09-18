"""Tools diagnostic runner — port of cmd_status in tools/cli/arwaky.py."""
from __future__ import annotations

import json as _json
import shutil

from modules.doctor.src.contract_doctor_protocol import IDiagnosticRunner
from modules.shared.src.utility_logging import (
    BLUE,
    BOLD,
    CYAN,
    GREEN,
    RED,
    RESET,
    YELLOW,
    banner,
    pad,
    table_widths,
)
from modules.shared.src.utility_manifest_reader import load_tools
from modules.shared.src.utility_xdg_atomic_io import ensure_path
from modules.shared.src.utility_xdg_paths import bin_home


# ─── Block 1: Class Definition & Constructor ──────────────
class ToolsDiagnosticRunner(IDiagnosticRunner):
    """Submodule-missing check + binary readiness table."""

    # -- Block 1: Configuration ---------------------------------------------------
    def __init__(self) -> None:
        ensure_path()

    # -- Block 2: Protocol ABC Method Implementation --------------------------------
    def run(self, json_mode: bool = False) -> int:
        if json_mode:
            out = []
            for tool in load_tools():
                if _is_submodule_missing(tool.path):
                    state = "submodule-missing"
                elif _resolve_executable(tool.binary):
                    state = "installed"
                elif (bin_home() / tool.binary).exists():
                    state = "ready"
                elif tool.category == "internal":
                    state = "source-ready"
                else:
                    state = "not-installed"
                out.append({"id": tool.id, "category": tool.category, "binary": tool.binary, "status": state})
            print(_json.dumps(out, indent=2, ensure_ascii=False))
            return 0
        banner()
        print(f"{BOLD()}System & Tool Health Status:{RESET()}")
        try:
            term_w = shutil.get_terminal_size((80, 24)).columns
        except (OSError, ValueError):
            term_w = 80
        available = max(60, term_w - 2)
        w_tool, w_cat, w_bin, w_status = table_widths(available, [2, 1, 3, 4])
        sep = "-" * available
        print(sep)
        print(f"{BOLD()}{pad('TOOL', w_tool)} {pad('CATEGORY', w_cat)} {pad('TARGET BINARY', w_bin)} STATUS{RESET()}")
        print(sep)
        for tool in load_tools():
            cat_color = GREEN() if tool.category == "internal" else CYAN()
            if _is_submodule_missing(tool.path):
                status = f"{RED()}[FAIL] Submodule Missing{RESET()}"
            elif _resolve_executable(tool.binary):
                status = f"{GREEN()}[OK] Installed ({tool.binary}){RESET()}"
            elif (bin_home() / tool.binary).exists():
                status = f"{GREEN()}[OK] Ready ({bin_home()}){RESET()}"
            elif tool.category == "internal":
                status = f"{BLUE()}[OK] Source Ready (Internal){RESET()}"
            else:
                status = f"{YELLOW()}[WARN] Not Installed{RESET()}"
            print(f"{pad(tool.id, w_tool)} {pad(cat_color + tool.category + RESET(), w_cat)} {pad(tool.binary, w_bin)} {status}")
        print(sep)
        return 0

    # -- Block 3: Dunder Methods, Factories & Helpers ----------------------------
    def __repr__(self) -> str:
        return "ToolsDiagnosticRunner()"


def _resolve_executable(binary: str):  # noqa: D103 — Block 3 helper, domain-specific, stateless but single-consumer duplicate to avoid sibling import
    found = shutil.which(binary)
    if found:
        from pathlib import Path

        return Path(found)
    local = bin_home() / binary
    import os

    if local.exists() and os.access(local, os.X_OK):
        return local
    return None


def _is_submodule_missing(path_str: str) -> bool:  # noqa: D103 — duplicated from EnvDiagnosticRunner to satisfy AES forbidden sibling-import rule; shared extraction to utility_git_submodule when ≥2 consumers stabilized
    from pathlib import Path

    from modules.shared.src.utility_paths import repo_root

    root = repo_root()
    target = root / path_str
    if not target.exists() or not (target / ".git").exists():
        gitmodules = root / ".gitmodules"
        if gitmodules.exists():
            try:
                text = gitmodules.read_text(encoding="utf-8", errors="replace")
            except OSError:
                return False
            return f"path = {path_str}" in text
        return False
    return False
