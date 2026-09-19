"""Ponytail adapter (npm, no build) — unified install + update + teardown.

@dietrichgebert/ponytail has NO build script and no lockfile — just copy
source to $XDG_DATA_HOME/ponytail and install ponytail-mcp dependencies
(@modelcontextprotocol/sdk, zod) via npm. Entry MCP = ponytail-mcp/index.js.

Stateless leaf (AES404): module-level functions only, no classes.
"""
from __future__ import annotations

from pathlib import Path

from modules.shared.src.taxonomy_core_error import ToolUpdateError
from modules.shared.src.taxonomy_xdg_paths import data_home

# --- inlined helper dependencies (self-contained; AES404: no utility-to-utility imports) ---
import shutil
import subprocess
import sys
from modules.shared.src.taxonomy_paths_constant import PROVENANCE_MARKER
from modules.shared.src.taxonomy_xdg_atomic_io import atomic_write_text, ensure_bin_home, ensure_path, warn_if_bin_not_on_path
from modules.shared.src.taxonomy_xdg_atomic_io import ensure_bin_home, warn_if_bin_not_on_path

from modules.shared.src.taxonomy_paths_constant import REPO_ROOT

ROOT = REPO_ROOT

def copy_app(src: Path, app_dir: Path, ignore_patterns: list[str]) -> None:
    """Replace *app_dir* with a copy of *src*, dropping the listed patterns."""
    ignore = shutil.ignore_patterns(*ignore_patterns)
    if app_dir.exists():
        shutil.rmtree(app_dir)
    shutil.copytree(src, app_dir, ignore=ignore)

def ensure_source(root: Path, src_rel: str) -> Path:
    """Ensure `root/src_rel` exists, attempting a git submodule init first."""
    src = root / src_rel
    if not src.exists():
        print(f">>> Initializing submodule {src_rel}...")
        subprocess.run(
            ["git", "-C", str(root), "submodule", "update", "--init", src_rel],
            check=False,
        )
    return src

def finish_bin() -> None:
    """Ensure bin home + PATH warning after launcher writes."""
    ensure_bin_home()
    warn_if_bin_not_on_path()

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

def require(tool: str, reason: str = "") -> bool:
    """True when *tool* is on PATH; otherwise print the missing-tool diagnostic."""
    if shutil.which(tool):
        return True
    print(f"Error: {tool} not found in PATH. {reason}", file=sys.stderr)
    return False

def run(cmd: list[str], cwd: Path | str | None = None) -> None:
    """Run with check=True; raises subprocess.CalledProcessError on failure."""
    subprocess.run(cmd, cwd=str(cwd) if cwd else None, check=True)

def write_node_launcher(name: str, entry: Path) -> Path:
    """Write a node entry launcher via the shared launcher writer."""
    # inlined: write_node_entry_launcher is defined below in this same file
    launcher = write_node_entry_launcher(name, entry)
    print(f"  -> {launcher}")
    return launcher

def write_node_entry_launcher(name: str, entry: Path, aliases: list[str] | None = None) -> Path:
    """Write a launcher that execs `node <entry>` in XDG bin. Returns launcher path."""
    content = (
        "#!/usr/bin/env python3\n"
        f"# {PROVENANCE_MARKER}\n"
        "import os, sys\n"
        f'entry = r"{entry}"\n'
        'os.execvpe("node", ["node", entry, *sys.argv[1:]], os.environ.copy())\n'
    )
    return write_generic_launcher(name, content, aliases=aliases)

def write_generic_launcher(tool_name: str, content: str, aliases: list[str] | None = None) -> Path:
    """Write a generic launcher with aliases. Returns launcher path."""
    ensure_bin_home()
    launcher = bin_home() / tool_name
    atomic_write_text(launcher, content)
    for alias in (aliases or []):
        a = bin_home() / alias
        a.unlink(missing_ok=True)
        a.symlink_to(launcher)
    warn_if_bin_not_on_path()
    ensure_path()
    return launcher

SRC_REL = "vendor/ponytail"
APP_DIR_REL = "ponytail"
ENTRY = "ponytail-mcp/index.js"

# Old node_modules in vendor are not copied (may be stale); deps are reinstalled
# with npm --prefix inside APP_DIR/ponytail-mcp.
IGNORES = ["node_modules", ".git", "__pycache__", "*.egg-info", ".venv", "venv"]


def _build(src: Path) -> None:
    """Copy source and install ponytail-mcp deps (shared install/update step)."""
    app_dir = data_home() / APP_DIR_REL
    copy_app(src, app_dir, IGNORES)
    mcp_dir = app_dir / "ponytail-mcp"
    if (mcp_dir / "package.json").exists():
        run(["npm", "ci", "--no-audit", "--no-fund"], mcp_dir)
    entry = app_dir / ENTRY
    if not entry.exists():
        raise FileNotFoundError(f"entry not found {entry}")


def _write_launcher() -> Path:
    app_dir = data_home() / APP_DIR_REL
    launcher = write_node_launcher("ponytail-mcp", app_dir / ENTRY)
    finish_bin()
    return launcher


def satisfied(spec, root: Path | None = None) -> bool:
    from modules.shared.src.taxonomy_xdg_paths import bin_home
    return (bin_home() / "ponytail-mcp").exists()


# -- install (from old installer adapter, verbatim mechanics) ----------------
def install(spec, root: Path = ROOT, *, daemons=None) -> list[Path]:
    root = root or ROOT
    src = ensure_source(root, SRC_REL)
    if not (src / "package.json").exists():
        raise FileNotFoundError(f"ponytail source not found (submodule not initialized): {src}")
    if not require("npm", "ponytail requires npm (https://nodejs.org)"):
        raise FileNotFoundError("npm is required (https://nodejs.org).")

    print(f">>> Installing ponytail (no build) into {data_home() / APP_DIR_REL}...")
    _build(src)
    launcher = _write_launcher()
    print(">>> Successfully installed ponytail")
    return [launcher]


# -- update (from old updater adapter) ---------------------------------------
def is_pin_satisfied(spec, root: Path) -> tuple[bool, str]:
    source = root / SRC_REL
    if not source.exists():
        return False, "submodule not initialized"
    return False, "npm workspace (rebuild required)"


def update(spec, root: Path) -> list[Path]:
    from modules.shared.src.utility_git_update import update_submodule

    source = root / SRC_REL
    if not update_submodule(root, SRC_REL):
        raise ToolUpdateError(f"submodule update failed: {SRC_REL}")
    if not (source / "package.json").exists():
        raise ToolUpdateError("ponytail source not found (submodule not initialized)")
    if not require("npm", "ponytail requires npm (https://nodejs.org)"):
        raise ToolUpdateError("ponytail requires npm (https://nodejs.org)")

    print(f">>> Updating ponytail into {data_home() / APP_DIR_REL}...")
    _build(source)
    launcher = _write_launcher()
    print(">>> Successfully updated ponytail")
    return [launcher]


# -- teardown data --------------------------------------------------------------
def owned_paths(spec, root: Path | None = None) -> list[Path]:
    return generic_owned(spec, ["ponytail-mcp"])
