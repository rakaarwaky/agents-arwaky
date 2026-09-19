"""Lint updater adapter — leaf utility for one manifest tool.

Mirrors the original tools/update/update_lint.py mechanics: submodule
bump, optional rustup bootstrap, build-dependency preflight, cargo release
build into XDG cache dir, binary copy to XDG bin, cli alias symlink.
"""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

from modules.shared.src.taxonomy_core_error import ToolUpdateError
from modules.shared.src.taxonomy_xdg_atomic_io import ensure_bin_home
from modules.shared.src.taxonomy_xdg_paths import (
    bin_home,
    cache_home,
    config_home,
    data_home,
)
from modules.shared.src.utility_git_update import update_submodule
from modules.shared.src.taxonomy_tool_vo import ToolSpec

BINARIES = ["lint-arwaky", "la", "lint-arwaky-cli", "lint-arwaky-mcp", "lint-arwaky-tui"]
_BUILD_DEPS = [
    ("cc", "gcc"),
    ("sccache", "sccache"),
    ("mold", "mold"),
]


class LintUpdaterAdapter:
    """Lint-arwaky (cargo) update sequence."""

    def is_pin_satisfied(self, spec: ToolSpec, root: Path) -> tuple[bool, str]:
        source = root / "internal/lint-arwaky"
        if not source.exists():
            return False, "submodule not initialized"
        return False, "cargo release build (rebuild required)"

    def update(self, spec: ToolSpec, root: Path) -> list[Path]:
        if not update_submodule(root, "internal/lint-arwaky"):
            raise ToolUpdateError("submodule update failed: internal/lint-arwaky")

        internal_dir = root / "internal/lint-arwaky"
        if self._cargo_on_path() is None:
            print(">>> cargo not found; attempting rustup bootstrap...", file=sys.stderr)
            if not self._bootstrap_rustup():
                raise ToolUpdateError("lint-arwaky update failed (Rust toolchain not available)")

        build_env = self._preflight_build_deps()
        build_env["CARGO_INCREMENTAL"] = "0"
        env = os.environ.copy()
        env.update(build_env)

        ensure_bin_home()
        (config_home() / "lint-arwaky/rules").mkdir(parents=True, exist_ok=True)
        (data_home() / "lint-arwaky/reports").mkdir(parents=True, exist_ok=True)

        cache_dir = cache_home() / "lint-arwaky"
        cache_dir.mkdir(parents=True, exist_ok=True)
        print(f">>> Building lint-arwaky (AES Architecture Linter) into {cache_dir}...")
        env["CARGO_TARGET_DIR"] = str(cache_dir)
        subprocess.run(["cargo", "build", "--release"], cwd=internal_dir, env=env, check=True)

        release = cache_dir / "release"
        created: list[Path] = []
        for binary in BINARIES:
            src = release / binary
            if src.exists():
                dst = bin_home() / binary
                tmp = dst.with_suffix(dst.suffix + ".tmp")
                shutil.copy2(src, tmp)
                tmp.chmod(0o755)
                os.replace(tmp, dst)
                created.append(dst)
                print(f"  -> {dst}")

        if (bin_home() / "lint-arwaky-cli").exists():
            lac = bin_home() / "lac"
            lac.unlink(missing_ok=True)
            lac.symlink_to(bin_home() / "lint-arwaky-cli")
            created.append(lac)

        print(">>> Successfully updated lint-arwaky")
        return created

    @staticmethod
    def _cargo_on_path() -> str | None:
        found = shutil.which("cargo")
        if found:
            return found
        for cand in (Path.home() / ".cargo/bin/cargo", Path("/usr/local/cargo/bin/cargo")):
            if cand.exists():
                os.environ["PATH"] = str(cand.parent) + os.pathsep + os.environ.get("PATH", "")
                return str(cand)
        return None

    @staticmethod
    def _bootstrap_rustup() -> bool:
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
        return LintUpdaterAdapter._cargo_on_path() is not None

    @staticmethod
    def _preflight_build_deps() -> dict:
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
                if cmd == "sccache":
                    env["CARGO_BUILD_RUSTC_WRAPPER"] = ""
                    print("  -> sccache skipped (RUSTC_WRAPPER empty).", file=sys.stderr)
                elif cmd == "mold":
                    env["CARGO_TARGET_X86_64_UNKNOWN_LINUX_GNU_RUSTFLAGS"] = ""
                    env["CARGO_TARGET_X86_64_UNKNOWN_LINUX_GNU_LINKER"] = "cc"
                    print("  -> mold skipped (linker=cc).", file=sys.stderr)
        return env
