"""Tools diagnostic runner — port of cmd_status in tools/cli/arwaky.py."""
from __future__ import annotations

import json as _json
import shutil
from collections.abc import Mapping

from modules.shared.src.contract_doctor_protocol import IDoctorProtocol
from modules.shared.src.taxonomy_common_vo import ExitCode, bin_home, ensure_path
from modules.shared.src.utility_logging_setup import (
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
from modules.shared.src.utility_tool_resolve import (
    is_submodule_missing,
    resolve_executable,
)


# ─── Block 1: Class Definition & Constructor ──────────────
class ToolsDiagnosticRunner(IDoctorProtocol):
    """Submodule-missing check + binary readiness table."""

    def __init__(self) -> None:
        """Prepare the XDG bin home required for binary lookups."""
        ensure_path()

    # ─── Block 2: Protocol Method Implementation ──────────────
    def execute(self, flags: Mapping[str, bool | str] | None = None) -> ExitCode:
        """Print a tool readiness table or JSON summary and return exit code 0."""
        json_mode = bool((flags or {}).get("json"))
        if json_mode:
            out = []
            for tool in load_tools():
                if is_submodule_missing(tool.path):
                    state = "submodule-missing"
                elif resolve_executable(tool.binary):
                    state = "installed"
                elif (bin_home() / tool.binary).exists():
                    state = "ready"
                elif tool.category == "internal":
                    state = "source-ready"
                else:
                    state = "not-installed"
                out.append({"id": tool.id, "category": tool.category, "binary": tool.binary, "status": state})
            print(_json.dumps(out, indent=2, ensure_ascii=False))
            return ExitCode(0)
        banner()
        print(f"{BOLD()}System & Tool Health Status:{RESET()}")
        try:
            term_w = shutil.get_terminal_size((80, 24)).columns
        except (OSError, ValueError):
            term_w = 80
        available = max(60, term_w - 2)
        w_tool, w_cat, w_bin, _w_status = table_widths(available, [2, 1, 3, 4])
        sep = "-" * available
        print(sep)
        print(f"{BOLD()}{pad('TOOL', w_tool)} {pad('CATEGORY', w_cat)} {pad('TARGET BINARY', w_bin)} STATUS{RESET()}")
        print(sep)
        for tool in load_tools():
            cat_color = GREEN() if tool.category == "internal" else CYAN()
            if is_submodule_missing(tool.path):
                status = f"{RED()}[FAIL] Submodule Missing{RESET()}"
            elif resolve_executable(tool.binary):
                status = f"{GREEN()}[OK] Installed ({tool.binary}){RESET()}"
            elif (bin_home() / tool.binary).exists():
                status = f"{GREEN()}[OK] Ready ({bin_home()}){RESET()}"
            elif tool.category == "internal":
                status = f"{BLUE()}[OK] Source Ready (Internal){RESET()}"
            else:
                status = f"{YELLOW()}[WARN] Not Installed{RESET()}"
            print(f"{pad(tool.id, w_tool)} {pad(cat_color + tool.category + RESET(), w_cat)} {pad(tool.binary, w_bin)} {status}")
        print(sep)
        return ExitCode(0)

    # ─── Block 3: Dunder Methods, Factories & Helpers ─────────
    def __repr__(self) -> str:
        return "ToolsDiagnosticRunner()"
