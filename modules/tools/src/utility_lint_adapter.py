"""Lint-arwaky adapter (cargo) — unified install + update + teardown.

Builds internal/lint-arwaky with `cargo build --release` into the XDG cache
directory, atomically installs the five binaries into ~/.local/bin, and wires
the `lac` alias. If cargo is missing it attempts a best-effort rustup
bootstrap; on install a failure skips the tool with a warning (success) so
that `aa install all` completes without crashing; on update it raises.
"""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from modules.shared.src.taxonomy_core_error import ToolUpdateError
from modules.tools.src.utility_tool_mechanics import ROOT, generic_owned, run
from modules.tools.src.utility_cargo_helpers import (
    _bootstrap_rustup,
    _cargo_on_path,
    _preflight_build_deps,
)

INTERNAL_DIR_REL = "internal/lint-arwaky"
BINARIES = ["lint-arwaky", "la", "lint-arwaky-cli", "lint-arwaky-mcp", "lint-arwaky-tui"]
LAUNCHERS = [
    ("lint-arwaky", "lint-arwaky"),
    ("la", "la"),
    ("lint-arwaky-cli", "lint-arwaky-cli"),
    ("lint-arwaky-mcp", "lint-arwaky-mcp"),
    ("lint-arwaky-tui", "lint-arwaky-tui"),
    ("lac", "lac"),
]


def _build_and_install(root: Path, spec, *, raise_on_missing_cargo: bool) -> list[Path]:
    """Cargo release build into XDG cache + atomic binary install + `lac` alias.

    Shared by the install and update verbs; only the cargo-missing policy
    differs (install skips with a warning, update raises).
    """
    from modules.shared.src.taxonomy_xdg_atomic_io import ensure_bin_home
    from modules.shared.src.taxonomy_xdg_paths import (
        bin_home,
        cache_home,
        config_home,
        data_home,
    )

    internal_dir = root / INTERNAL_DIR_REL
    if _cargo_on_path() is None:
        print(">>> cargo not found; attempting rustup bootstrap...", file=sys.stderr)
        if not _bootstrap_rustup():
            if not raise_on_missing_cargo:
                print("  Warning: lint-arwaky skipped (Rust toolchain not available).", file=sys.stderr)
                print("  Re-run 'aa install lint' after installing Rust.", file=sys.stderr)
                return []
            raise ToolUpdateError("lint-arwaky update failed (Rust toolchain not available)")

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
    subprocess.run(["cargo", "build", "--release"], cwd=internal_dir, env=env, check=True)

    release = cache_dir / "release"
    artifacts: list[Path] = []
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
            artifacts.append(dst)
            print(f"  -> {dst}")
    if (bin_home() / "lint-arwaky-cli").exists():
        lac = bin_home() / "lac"
        lac.unlink(missing_ok=True)
        lac.symlink_to(bin_home() / "lint-arwaky-cli")
        artifacts.append(lac)
    return artifacts


class LintAdapter:
    """Build internal/lint-arwaky (Rust) and install its binaries to XDG bin."""

    def satisfied(self, spec, root: Path | None = None) -> bool:
        from modules.shared.src.taxonomy_xdg_paths import bin_home

        return (bin_home() / "lint-arwaky").exists()

    # -- install (from old installer adapter, verbatim mechanics) ----------------
    def install(self, spec, root: Path = ROOT, *, daemons=None) -> list[Path]:
        from modules.shared.src.taxonomy_xdg_atomic_io import ensure_bin_home
        from modules.shared.src.taxonomy_xdg_paths import (
            bin_home,
            cache_home,
            config_home,
            data_home,
        )

        root = root or ROOT
        internal_dir = root / INTERNAL_DIR_REL

        if not (internal_dir.exists() and (internal_dir / "Cargo.toml").exists()):
            run(["git", "-C", str(root), "submodule", "update", "--init", INTERNAL_DIR_REL])

        artifacts = _build_and_install(root, spec, raise_on_missing_cargo=False)
        if not artifacts:
            return []
        print(">>> Successfully installed lint-arwaky")
        return artifacts

    # -- update (from old updater adapter) ---------------------------------------
    def is_pin_satisfied(self, spec, root: Path) -> tuple[bool, str]:
        source = root / INTERNAL_DIR_REL
        if not source.exists():
            return False, "submodule not initialized"
        return False, "cargo release build (rebuild required)"

    def update(self, spec, root: Path) -> list[Path]:
        from modules.shared.src.utility_git_update import update_submodule

        if not update_submodule(root, INTERNAL_DIR_REL):
            raise ToolUpdateError(f"submodule update failed: {INTERNAL_DIR_REL}")

        created = _build_and_install(root, spec, raise_on_missing_cargo=True)
        print(">>> Successfully updated lint-arwaky")
        return created

    # -- teardown data --------------------------------------------------------------
    def owned_paths(self, spec, root: Path | None = None) -> list[Path]:
        from modules.shared.src.taxonomy_xdg_paths import bin_home, config_home, data_home

        extra = [bin_home() / "lac"]
        return generic_owned(
            spec, [name for name, _e in LAUNCHERS], extra=extra
        )
