"""Capability — lint-arwaky tool adapter (cargo release build).

Implements `IToolsProtocol` (AES403) and exports the `lint`
`AdapterUnit` merged into `TOOLS_REGISTRY` by the root container.
Shared mechanics live in `utility_tool_mechanics`.
"""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from modules.shared.src.contract_tools_protocol import IToolsProtocol
from modules.shared.src.taxonomy_common_error import ToolUpdateError
from modules.shared.src.taxonomy_common_vo import (
    ToolSpec,
    bin_home,
    cache_home,
    config_home,
    data_home,
    ensure_bin_home,
)
from modules.shared.src.taxonomy_tools_constant import (
    LINT_BINARIES,
    LINT_BUILD_DEPS,
    LINT_INTERNAL_DIR_REL,
    LINT_LAUNCHERS,
)
from modules.shared.src.taxonomy_tools_vo import AdapterUnit
from modules.shared.src.utility_git_submodule import update_submodule
from modules.shared.src.utility_tool_mechanics import (
    ROOT,
    make_owned,
    make_pin_check,
    make_satisfied,
    run,
)


# ─── Block 1: Class Definition & Constructor ──────────────
class LintToolsAdapter(IToolsProtocol):
    """Lint actions behind the tools protocol (AES403 implementor)."""

    def __init__(self, units: dict[str, AdapterUnit] | None = None) -> None:
        self._units = dict(units) if units is not None else dict(ADAPTER_UNITS)

    # ─── Block 2: Protocol Method Implementation ──────────────
    def execute(
        self,
        op: str,
        spec: ToolSpec | None = None,
        query: object | None = None,
        args: list[str] | None = None,
    ) -> object:
        """Dispatch *op* against this file's lint unit."""
        if spec is None:
            raise ToolUpdateError(f"lint adapter got op={op!r} without a spec")
        unit = self._units.get(spec.id)
        if unit is None:
            raise ToolUpdateError(f"lint adapter has no unit for {spec.id!r}")
        root = Path(args[0]) if args else None
        if op == "satisfied":
            return unit.satisfied(spec, root)
        if op == "is_pin_satisfied":
            return unit.is_pin_satisfied(spec, root or ROOT)
        if op == "owned_paths":
            return unit.owned_paths(spec, root or ROOT)
        if op == "install":
            try:
                return list(unit.install(spec, root or ROOT, daemons=query) or [])
            except TypeError:
                return list(unit.install(spec, root or ROOT) or [])
        if op == "update":
            return list(unit.update(spec, root or ROOT) or [])
        raise ToolUpdateError(f"unsupported lint adapter op {op!r}")

    # ─── Block 3: Dunder Methods, Factories & Helpers ─────────
    def __repr__(self) -> str:
        return f"LintToolsAdapter(tools={len(self._units)})"


# ---------------------------------------------------------------------------
# Build helpers (cargo — rustup bootstrap + atomic install)
# ---------------------------------------------------------------------------
def _lint_bootstrap_rustup() -> bool:
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
        subprocess.run(["sh", script, "-y", "--no-modify-path"], check=True, timeout=600)
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as e:
        print(f"  Warning: rustup bootstrap failed ({e}).", file=sys.stderr)
        return False
    finally:
        os.unlink(script)
    return _lint_cargo_on_path() is not None


def _lint_cargo_on_path() -> str | None:
    """Find cargo on PATH or at the default rustup location."""
    found = shutil.which("cargo")
    if found:
        return found
    for cand in (Path.home() / ".cargo/bin/cargo", Path("/usr/local/cargo/bin/cargo")):
        if cand.exists():
            os.environ["PATH"] = str(cand.parent) + os.pathsep + os.environ.get("PATH", "")
            return str(cand)
    return None


def _lint_preflight_build_deps() -> dict:
    """Ensure build deps are present (apt best-effort via sudo); fallback override env."""
    env: dict = {}
    for cmd, pkg in LINT_BUILD_DEPS:
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


def _lint_build_and_install(root: Path, *, raise_on_missing_cargo: bool) -> list[Path]:
    """Cargo release build into XDG cache + atomic binary install + `lac` alias."""
    internal_dir = root / LINT_INTERNAL_DIR_REL
    if _lint_cargo_on_path() is None:
        print(">>> cargo not found; attempting rustup bootstrap...", file=sys.stderr)
        if not _lint_bootstrap_rustup():
            if not raise_on_missing_cargo:
                print("  Warning: lint-arwaky skipped (Rust toolchain not available).",
                      file=sys.stderr)
                print("  Re-run 'aa install lint' after installing Rust.", file=sys.stderr)
                return []
            raise ToolUpdateError("lint-arwaky update failed (Rust toolchain not available)")

    build_env = _lint_preflight_build_deps()
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
    artifacts: list[Path] = []
    for b in LINT_BINARIES:
        src = release / b
        if src.exists():
            dst = bin_home() / b
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


lint_satisfied = make_satisfied("lint-arwaky")
lint_is_pin_satisfied = make_pin_check(
    LINT_INTERNAL_DIR_REL, "cargo release build (rebuild required)")
lint_owned_paths = make_owned(
    LINT_LAUNCHERS, extra=lambda: [bin_home() / "lac"])


def lint_install(spec, root=ROOT, *, daemons=None):
    root = root or ROOT
    internal_dir = root / LINT_INTERNAL_DIR_REL
    if not (internal_dir.exists() and (internal_dir / "Cargo.toml").exists()):
        run(["git", "-C", str(root), "submodule", "update", "--init", LINT_INTERNAL_DIR_REL])
    artifacts = _lint_build_and_install(root, raise_on_missing_cargo=False)
    if not artifacts:
        return []
    print(">>> Successfully installed lint-arwaky")
    return artifacts


def lint_update(spec, root):
    if not update_submodule(root, LINT_INTERNAL_DIR_REL):
        raise ToolUpdateError(f"submodule update failed: {LINT_INTERNAL_DIR_REL}")
    created = _lint_build_and_install(root, raise_on_missing_cargo=True)
    print(">>> Successfully updated lint-arwaky")
    return created


def _unit(*, satisfied, install, update, is_pin_satisfied, owned_paths) -> AdapterUnit:
    return AdapterUnit(
        satisfied=satisfied,
        install=install,
        update=update,
        is_pin_satisfied=is_pin_satisfied,
        owned_paths=owned_paths,
    )


#: tool_id → unit for lint-arwaky (merged by root_tools_container).
ADAPTER_UNITS: dict[str, AdapterUnit] = {
    "lint-arwaky": _unit(
        satisfied=lint_satisfied,
        install=lint_install,
        update=lint_update,
        is_pin_satisfied=lint_is_pin_satisfied,
        owned_paths=lint_owned_paths,
    ),
}


__all__ = [
    "ADAPTER_UNITS",
    "LintToolsAdapter",
    "lint_install",
    "lint_is_pin_satisfied",
    "lint_owned_paths",
    "lint_satisfied",
    "lint_update",
]
