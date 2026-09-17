"""Lint updater (cargo, force rebuild) — port of tools/update/update_lint.py.

Always pulls internal/lint-arwaky, runs `cargo build --release` into the
XDG cache dir, and atomically overwrites the five binaries + `lac` alias.
Unlike the installer there is no "already installed" skip: this is a
force rebuild.
"""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from modules.shared.src.git.utility_git_update import update_submodule
from modules.shared.src.paths.utility_paths import repo_root
from modules.shared.src.tool.taxonomy_tool_vo import ToolSpec, UpdateResult
from modules.shared.src.tool.contract_tool_protocol import IToolUpdater
from modules.shared.src.xdg.utility_xdg_atomic_io import ensure_bin_home
from modules.shared.src.xdg.utility_xdg_paths import (
    bin_home,
    cache_home,
    config_home,
    data_home,
)


BINARIES = ["lint-arwaky", "la", "lint-arwaky-cli", "lint-arwaky-mcp", "lint-arwaky-tui"]

_BUILD_DEPS = [
    # (command, apt package)
    ("cc", "gcc"),
    ("sccache", "sccache"),
    ("mold", "mold"),
]


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
    fd, script = tempfile.mkstemp(prefix="rustup-init-", suffix=".sh")
    os.close(fd)
    try:
        if shutil.which("curl"):
            cmd = ["curl", "--proto", "=https", "--tlsv1.2", "-sSf",
                   "https://sh.rustup.rs", "-o", script]
        elif shutil.which("wget"):
            cmd = ["wget", "-qO", script, "https://sh.rustup.rs"]
        else:
            print("  Warning: no curl/wget found for rustup bootstrap.", file=sys.stderr)
            return False
        subprocess.run(cmd, check=True, timeout=120)
        subprocess.run(["sh", script, "-y", "--no-modify-path"],
                       check=True, timeout=600)
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as e:
        print(f"  Warning: rustup bootstrap failed ({e}).", file=sys.stderr)
        return False
    finally:
        os.unlink(script)
    return _cargo_on_path() is not None


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


class LintUpdater(IToolUpdater):
    """Force-rebuild internal/lint-arwaky (Rust) and overwrite XDG bin binaries."""

    def __init__(self, root=None) -> None:
        self._root = root or repo_root()

    def update(self, spec: ToolSpec) -> UpdateResult:
        root = self._root
        print(">>> Updating lint-arwaky (AES Architecture Linter)...")

        if not update_submodule(root, "internal/lint-arwaky"):
            return UpdateResult(False, spec.id, "submodule update failed: internal/lint-arwaky")

        internal_dir = root / "internal/lint-arwaky"
        if _cargo_on_path() is None:
            print(">>> cargo not found; attempting rustup bootstrap...", file=sys.stderr)
            if not _bootstrap_rustup():
                print("  Warning: lint-arwaky update skipped (Rust toolchain not available).", file=sys.stderr)
                return UpdateResult(True, spec.id, "skipped (Rust toolchain not available)")

        build_env = _preflight_build_deps()
        build_env["CARGO_INCREMENTAL"] = "0"  # project recommendation for sccache
        env = os.environ.copy()
        env.update(build_env)

        ensure_bin_home()
        (config_home() / "lint-arwaky/rules").mkdir(parents=True, exist_ok=True)
        (data_home() / "lint-arwaky/reports").mkdir(parents=True, exist_ok=True)

        # Build in cache directory (XDG spec: transient build artifacts in ~/.cache/)
        cache_dir = cache_home() / "lint-arwaky"
        cache_dir.mkdir(parents=True, exist_ok=True)
        print(f">>> Building lint-arwaky (AES Architecture Linter) into {cache_dir}...")
        env["CARGO_TARGET_DIR"] = str(cache_dir)
        try:
            subprocess.run(["cargo", "build", "--release"], cwd=internal_dir, env=env, check=True)
        except subprocess.CalledProcessError as exc:
            return UpdateResult(False, spec.id, f"cargo build failed: {exc}")

        release = cache_dir / "release"
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
        print(">>> Successfully updated lint-arwaky")
        return UpdateResult(True, spec.id, "lint-arwaky rebuilt and updated")
