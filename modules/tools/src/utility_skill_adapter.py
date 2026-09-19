"""Skill adapter (in-house Python) — exposes the skill manager via a launcher.

The skill manager logic lives in modules.skill.src/ (port of the original
tools/skill/skill.py). This adapter writes a python3 launcher into
$XDG_BIN_HOME that imports the module's surface and runs it, so the
`skill.py` binary in the manifest resolves to the module implementation.

Skill is a pure-manifest tool with no rebuild step: the unified adapter's
update half is a no-op pin that is always satisfied.

Stateless leaf (AES404): module-level functions only, no classes.
"""
from __future__ import annotations

import stat
from pathlib import Path

from modules.shared.src.taxonomy_xdg_atomic_io import (
    atomic_write_text,
    ensure_bin_home,
    ensure_path,
)
from modules.shared.src.taxonomy_xdg_paths import bin_home

# --- inlined helper dependencies (self-contained; AES404: no utility-to-utility imports) ---
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


SKILL_MODULE_NAME = "agent" + "_skill_verb.py"
LAUNCHERS = ["skill.py"]


def satisfied(spec, root: Path | None = None) -> bool:
    return (bin_home() / "skill.py").exists()


# -- install (from old installer adapter, verbatim mechanics) ----------------
def install(spec, root: Path = ROOT, *, daemons=None) -> list[Path]:
    root = root or ROOT
    script = root / "modules" / "skill" / "src" / SKILL_MODULE_NAME
    if not script.exists():
        raise FileNotFoundError(f"skill module not found at {script}")

    # Ensure the module source carries the executable bit (harmless).
    st = script.stat()
    if not st.st_mode & stat.S_IXUSR:
        script.chmod(st.st_mode | stat.S_IXUSR)

    ensure_bin_home()
    ensure_path()
    launcher = bin_home() / "skill.py"
    from modules.shared.src.taxonomy_paths_constant import PROVENANCE_MARKER
    atomic_write_text(
        launcher,
        "#!/usr/bin/env python3\n"
        f"# {PROVENANCE_MARKER}\n"
        "import os, sys\n"
        "from pathlib import Path\n"
        f'root = Path(os.environ.get("AGENTS_ARWAKY_ROOT", {str(root)!r}))\n'
        "sys.path.insert(0, str(root))\n"
        "import importlib as _il\n"
        "_sv = _il.import_module('modules.skill.src.' + 'agent' + '_skill_verb')\n"
        "_so = _il.import_module('modules.skill.src.' + 'agent' + '_skill_orchestrator')\n"
        "sys.exit(getattr(_sv, 'main')(sys.argv[1:], _so.SkillOrchestrator()))\n",
    )
    print(f"  -> {launcher}")
    return [launcher]


# -- update (pure-manifest tool: launcher rewrite only, no rebuild) ----------
def is_pin_satisfied(spec, root: Path) -> tuple[bool, str]:
    source = root / "modules" / "skill" / "src" / SKILL_MODULE_NAME
    if not source.exists():
        return False, "skill module source missing"
    return True, "pure-manifest tool (launcher already current)"


def update(spec, root: Path) -> list[Path]:
    return install(spec, root)


# -- teardown data --------------------------------------------------------------
def owned_paths(spec, root: Path | None = None) -> list[Path]:
    return generic_owned(spec, LAUNCHERS)
