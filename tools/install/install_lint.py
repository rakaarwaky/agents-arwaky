#!/usr/bin/env python3
"""Installer lint-arwaky — AES Architecture Linter (Rust, cargo).

Specifics: lint-arwaky is built from Rust source (cargo build --release).
If `cargo` is not found, the installer attempts a non-interactive rustup bootstrap;
if bootstrap fails, the tool is skipped with a warning (return 0) so that
`aa install all` completes without crashing.
"""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "lib"))

from xdg import (  # type: ignore[import-untyped]
    bin_home,
    config_home,
    data_home,
    ensure_bin_home,
)

INTERNAL_DIR = ROOT / "internal/lint-arwaky"
BINARIES = ["lint-arwaky", "la", "lint-arwaky-cli", "lint-arwaky-mcp", "lint-arwaky-tui"]


def run(cmd, cwd=None):
    subprocess.run(cmd, cwd=cwd, check=True)


def _cargo_on_path() -> str | None:
    """Find cargo on PATH or at the default rustup location."""
    found = shutil.which("cargo")
    if found:
        return found
    for cand in (Path.home() / ".cargo/bin/cargo", Path("/usr/local/cargo/bin/cargo")):
        if cand.exists():
            os.environ["PATH"] = str(cand.parent) + os.pathsep + os.environ.get("PATH", "")
            return str(cand)
    return None


def _bootstrap_rustup() -> bool:
    """Install rust toolchain via rustup (non-interactive). Best effort."""
    if shutil.which("curl"):
        cmd = ["curl", "--proto", "=https", "--tlsv1.2", "-sSf",
               "https://sh.rustup.rs", "-o", "/tmp/rustup-init.sh"]
    elif shutil.which("wget"):
        cmd = ["wget", "-qO", "/tmp/rustup-init.sh", "https://sh.rustup.rs"]
    else:
        print("  Warning: no curl/wget found for rustup bootstrap.", file=sys.stderr)
        return False
    try:
        subprocess.run(cmd, check=True, timeout=120)
        subprocess.run(["sh", "/tmp/rustup-init.sh", "-y", "--no-modify-path"],
                       check=True, timeout=600)
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as e:
        print(f"  Warning: rustup bootstrap failed ({e}).", file=sys.stderr)
        return False
    return _cargo_on_path() is not None


_BUILD_DEPS = [
    # (command, apt package)
    ("cc", "gcc"),
    ("sccache", "sccache"),
    ("mold", "mold"),
]


def _preflight_build_deps() -> dict:
    """Ensure build deps are present (apt best-effort via sudo); fallback override env."""
    env = {}
    for cmd, pkg in _BUILD_DEPS:
        if shutil.which(cmd):
            continue
        print(f">>> Build dep '{cmd}' not found; trying apt install {pkg}...", file=sys.stderr)
        try:
            subprocess.run(["sudo", "-n", "apt-get", "install", "-y", pkg],
                           check=True, timeout=300, capture_output=True)
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as e:
            print(f"  Warning: apt install {pkg} failed ({e}); using fallback.", file=sys.stderr)
        if shutil.which(cmd):
            print(f"  -> {cmd} available.")
        else:
            # Fallback: disable wrapper/flag that needs this tool.
            if cmd == "sccache":
                env["CARGO_BUILD_RUSTC_WRAPPER"] = ""
                print("  -> sccache skipped (RUSTC_WRAPPER empty).", file=sys.stderr)
            elif cmd == "mold":
                env["CARGO_TARGET_X86_64_UNKNOWN_LINUX_GNU_RUSTFLAGS"] = ""
                env["CARGO_TARGET_X86_64_UNKNOWN_LINUX_GNU_LINKER"] = "cc"
                print("  -> mold skipped (linker=cc).", file=sys.stderr)
    return env


def main() -> int:
    if not INTERNAL_DIR.exists() or not (INTERNAL_DIR / "Cargo.toml").exists():
        run(["git", "-C", str(ROOT), "submodule", "update", "--init", "internal/lint-arwaky"])

    if _cargo_on_path() is None:
        print(">>> cargo not found; attempting rustup bootstrap...", file=sys.stderr)
        if not _bootstrap_rustup():
            print("  Warning: lint-arwaky skipped (Rust toolchain not available).", file=sys.stderr)
            print("  Re-run 'aa install lint' after installing Rust.", file=sys.stderr)
            return 0

    build_env = _preflight_build_deps()
    build_env["CARGO_INCREMENTAL"] = "0"  # project recommendation for sccache
    env = os.environ.copy()
    env.update(build_env)

    ensure_bin_home()
    (config_home() / "lint-arwaky/rules").mkdir(parents=True, exist_ok=True)
    (data_home() / "lint-arwaky/reports").mkdir(parents=True, exist_ok=True)
    print(">>> Building lint-arwaky (AES Architecture Linter)...")
    subprocess.run(["cargo", "build", "--release"], cwd=INTERNAL_DIR, env=env, check=True)
    release = INTERNAL_DIR / "target/release"
    for b in BINARIES:
        src = release / b
        if src.exists():
            dst = bin_home() / b
            # Atomic replace: avoid ETXTBSY if old binary is still in use
            # by a running process (rename is safe; old process keeps old inode).
            tmp = dst.with_suffix(dst.suffix + ".tmp")
            shutil.copy2(src, tmp)
            tmp.chmod(0o755)
            os.replace(tmp, dst)
            print(f"  -> {dst}")
    if (bin_home() / "lint-arwaky-cli").exists():
        lac = bin_home() / "lac"
        lac.unlink(missing_ok=True)
        lac.symlink_to(bin_home() / "lint-arwaky-cli")
    print(">>> Successfully installed lint-arwaky")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
