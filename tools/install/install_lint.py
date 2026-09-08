#!/usr/bin/env python3
"""lint-arwaky installer (Python, cargo)."""
from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "lib"))

from xdg import bin_home, config_home, data_home, ensure_bin_home

INTERNAL_DIR = ROOT / "internal/lint-arwaky"
BINARIES = ["lint-arwaky", "la", "lint-arwaky-cli", "lint-arwaky-mcp", "lint-arwaky-tui"]


def run(cmd, cwd=None):
    subprocess.run(cmd, cwd=cwd, check=True)


def main() -> int:
    if not INTERNAL_DIR.exists() or not (INTERNAL_DIR / "Cargo.toml").exists():
        run(["git", "-C", str(ROOT), "submodule", "update", "--init", "internal/lint-arwaky"])
    if not shutil.which("cargo"):
        print("Error: cargo is required to build lint-arwaky.", file=sys.stderr)
        return 1
    ensure_bin_home()
    (config_home() / "lint-arwaky/rules").mkdir(parents=True, exist_ok=True)
    (data_home() / "lint-arwaky/reports").mkdir(parents=True, exist_ok=True)
    print(">>> Building lint-arwaky (AES Architecture Linter)...")
    run(["cargo", "build", "--release"], INTERNAL_DIR)
    release = INTERNAL_DIR / "target/release"
    for b in BINARIES:
        src = release / b
        if src.exists():
            dst = bin_home() / b
            shutil.copy2(src, dst)
            dst.chmod(0o755)
            print(f"  -> {dst}")
    if (bin_home() / "lint-arwaky-cli").exists():
        lac = bin_home() / "lac"
        lac.unlink(missing_ok=True)
        lac.symlink_to(bin_home() / "lint-arwaky-cli")
    print(">>> Successfully installed lint-arwaky")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
