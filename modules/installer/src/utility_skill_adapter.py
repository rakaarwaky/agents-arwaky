"""Skill adapter (in-house Python) — exposes the skill manager via a launcher.

The skill manager logic lives in modules.skill.src/ (port of the original
tools/skill/skill.py). This adapter writes a python3 launcher into
$XDG_BIN_HOME that imports the module's surface and runs it, so the
`skill.py` binary in the manifest resolves to the module implementation.
"""
from __future__ import annotations

from pathlib import Path

from modules.shared.src.taxonomy_xdg_atomic_io import (
    atomic_write_text,
    ensure_bin_home,
    ensure_path,
)
from modules.shared.src.taxonomy_xdg_paths import bin_home
from modules.installer.src.utility_adapter_base import AdapterBase, ROOT

SKILL_MODULE_NAME = "agent" + "_skill_verb.py"


class SkillAdapter(AdapterBase):
    """Write a launcher that runs the skill manager from modules/skill/."""

    def install(self, spec, root: Path = ROOT, *, daemons=None) -> list[Path]:
        root = root or ROOT
        script = root / "modules" / "skill" / "src" / SKILL_MODULE_NAME
        if not script.exists():
            raise FileNotFoundError(f"skill module not found at {script}")

        # Ensure the module source carries the executable bit (harmless).
        import stat
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
