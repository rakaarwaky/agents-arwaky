"""Environment diagnostic runner — port of cmd_doctor in tools/cli/arwaky.py."""
from __future__ import annotations

import os
import shutil

from modules.shared.src.contract_doctor_protocol import IDiagnosticRunner
from modules.shared.src.taxonomy_common_vo import ExitCode, bin_home, ensure_path
from modules.shared.src.utility_logging_setup import (
    BOLD,
    DIM,
    GREEN,
    RESET,
    banner,
    err,
    ok,
    warn,
)

REQUIRED = ("git", "jq", "curl", "python3")
OPTIONAL = ("cargo", "uv", "node", "npm", "bun", "pnpm", "rustc")


# ─── Block 1: Class Definition & Constructor ──────────────
class EnvDiagnosticRunner(IDiagnosticRunner):
    """PATH check, required/optional toolchain, container engine detection."""

    def __init__(self) -> None:
        ensure_path()

    # ─── Block 2: Protocol ABC Method Implementation ──────────
    def run(self, json_mode: bool = False) -> ExitCode:
        _ = json_mode
        banner()
        print(f"{BOLD()}Running Environment Diagnostics...{RESET()}")
        print("-" * 54)
        self._check_toolchain()
        engine = shutil.which("podman") or shutil.which("docker")
        if engine:
            ok(f"Container engine: {engine}")
        else:
            warn("Podman/Docker not found (only needed for anytype daemons)")
        print("-" * 54)
        print(f"{GREEN()}Diagnostics complete.{RESET()}")
        return ExitCode(0)

    # ─── Block 3: Dunder Methods, Factories & Helpers ───────
    def _check_toolchain(self) -> None:
        target_bin = str(bin_home())
        if target_bin in os.environ.get("PATH", "").split(os.pathsep):
            ok(f"PATH includes {target_bin}")
        else:
            warn(f"PATH does not include {target_bin}")
        for util in REQUIRED:
            path = shutil.which(util)
            if path:
                ok(f"{util}: {path}")
            else:
                err(f"{util} is required")
        for util in OPTIONAL:
            path = shutil.which(util)
            if path:
                ok(f"{util}: {path}")
            else:
                print(f"  {DIM()}[SKIP]{RESET()} {util} not installed (optional)")
def _resolve_executable(binary: str):
    """shutil.which + bin_home executable fallback (from lib/tool_resolver)."""
    found = shutil.which(binary)
    if found:
        from pathlib import Path
        return Path(found)
    local = bin_home() / binary
    if local.exists() and os.access(local, os.X_OK):
        return local
    return None


def _is_submodule_missing(path_str: str) -> bool:
    """A submodule path is missing when its target (or .git) does not exist."""
    from modules.shared.src.utility_paths_resolver import repo_root

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


