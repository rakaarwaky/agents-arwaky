"""Lint-arwaky adapter (cargo) — unified install + update + teardown.

Builds internal/lint-arwaky with `cargo build --release` into the XDG cache
directory, atomically installs the five binaries into ~/.local/bin, and wires
the `lac` alias. If cargo is missing it attempts a best-effort rustup
bootstrap; on install a failure skips the tool with a warning (success) so
that `aa install all` completes without crashing; on update it raises.

Stateless leaf (AES404): module-level functions only, no classes.
"""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

from modules.shared.src.taxonomy_core_error import ToolUpdateError

# --- inlined helper dependencies (self-contained; AES404: no utility-to-utility imports) ---
import tempfile

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

from modules.shared.src.taxonomy_paths_constant import REPO_ROOT

ROOT = REPO_ROOT

def generic_owned(
    spec,
    launcher_names: list[str],
    *,
    extra: list[Path] | None = None,
    config: list[str] | None = None,
) -> list[Path]:
    """Generic XDG owned set for one tool: bin launchers + data + cache.

    Adapters extend it with tool-specific extras (internal-bin copies,
    env files, daemon units) via *extra* and with installer-owned
    config subtrees (``config_home() / name``) via *config*.
    """
    from modules.shared.src.taxonomy_xdg_paths import cache_home, config_home, data_home

    paths: list[Path] = [bin_home() / name for name in launcher_names]
    paths.append(data_home() / spec.id)
    paths.append(cache_home() / spec.id)
    for name in config or []:
        paths.append(config_home() / name)
    paths.extend(extra or [])
    return paths

def run(cmd: list[str], cwd: Path | str | None = None) -> None:
    """Run with check=True; raises subprocess.CalledProcessError on failure."""
    subprocess.run(cmd, cwd=str(cwd) if cwd else None, check=True)

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


def satisfied(spec, root: Path | None = None) -> bool:
    from modules.shared.src.taxonomy_xdg_paths import bin_home

    return (bin_home() / "lint-arwaky").exists()


# -- install (from old installer adapter, verbatim mechanics) ----------------
def install(spec, root: Path = ROOT, *, daemons=None) -> list[Path]:
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
def is_pin_satisfied(spec, root: Path) -> tuple[bool, str]:
    source = root / INTERNAL_DIR_REL
    if not source.exists():
        return False, "submodule not initialized"
    return False, "cargo release build (rebuild required)"


def update(spec, root: Path) -> list[Path]:

    if not update_submodule(root, INTERNAL_DIR_REL):
        raise ToolUpdateError(f"submodule update failed: {INTERNAL_DIR_REL}")

    created = _build_and_install(root, spec, raise_on_missing_cargo=True)
    print(">>> Successfully updated lint-arwaky")
    return created


# -- teardown data --------------------------------------------------------------
def owned_paths(spec, root: Path | None = None) -> list[Path]:
    from modules.shared.src.taxonomy_xdg_paths import bin_home

    extra = [bin_home() / "lac"]
    return generic_owned(
        spec, [name for name, _e in LAUNCHERS], extra=extra
    )
