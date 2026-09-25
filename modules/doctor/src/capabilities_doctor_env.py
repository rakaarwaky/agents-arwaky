"""Environment diagnostic runner — port of cmd_doctor in tools/cli/arwaky.py."""
from __future__ import annotations

import os
import shutil
from collections.abc import Mapping

from modules.shared.src.contract_doctor_protocol import IDoctorProtocol
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

#: Required toolchain binaries every host must provide.
REQUIRED = ("git", "jq", "curl", "python3")
#: Optional toolchain binaries (reported, never failed).
OPTIONAL = ("cargo", "uv", "node", "npm", "bun", "pnpm", "rustc")


# ─── Block 1: Class Definition & Constructor ──────────────
class EnvDiagnosticRunner(IDoctorProtocol):
    """PATH check, required/optional toolchain, container engine detection."""

    def __init__(self) -> None:
        ensure_path()

    # ─── Block 2: Protocol Method Implementation ──────────────
    def execute(self, flags: Mapping[str, bool | str] | None = None) -> ExitCode:
        _ = flags
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

    # ─── Block 3: Dunder Methods, Factories & Helpers ─────────
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

    def __repr__(self) -> str:
        return "EnvDiagnosticRunner()"


