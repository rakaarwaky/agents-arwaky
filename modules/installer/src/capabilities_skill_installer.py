"""Skill installer (in-house Python) — exposes the skill manager via a launcher.

The skill manager logic lives in modules/skill/src/ (port of the original
tools/skill/skill.py). This installer writes a python3 launcher into
$XDG_BIN_HOME that imports the module's surface and runs it, so the
`skill.py` binary in the manifest resolves to the module implementation.
"""
from __future__ import annotations

import stat
import subprocess

from modules.shared.src.utility_paths import repo_root
from modules.shared.src.taxonomy_tool_vo import InstallResult, ToolSpec
from modules.installer.src.contract_tool_installer import IToolInstaller
from modules.shared.src.utility_xdg_atomic_io import (
    atomic_write_text,
    ensure_bin_home,
    ensure_path,
)
from modules.shared.src.utility_xdg_paths import bin_home


SKILL_MODULE_REL = "modules/skill/src/surface_skill_command.py"


class SkillInstaller(IToolInstaller):
    """Write a launcher that runs the skill manager from modules/skill/."""

    def __init__(self, root=None) -> None:
        self._root = root or repo_root()

    def install(self, spec: ToolSpec) -> InstallResult:
        root = self._root
        script = root / SKILL_MODULE_REL
        if not script.exists():
            return InstallResult(False, spec.id, f"skill module not found at {script}")

        # Ensure the module source carries the executable bit (harmless).
        st = script.stat()
        if not st.st_mode & stat.S_IXUSR:
            script.chmod(st.st_mode | stat.S_IXUSR)

        ensure_bin_home()
        ensure_path()
        launcher = bin_home() / "skill.py"
        atomic_write_text(
            launcher,
            "#!/usr/bin/env python3\n"
            "import os, sys\n"
            "from pathlib import Path\n"
            f'root = Path(os.environ.get("AGENTS_ARWAKY_ROOT", {str(root)!r}))\n'
            "sys.path.insert(0, str(root))\n"
            'from modules.skill.src.surface_skill_command import cmd_skill\n'
            'from modules.skill.src.root_skill_container import create_skill_feature\n'
            'sys.exit(cmd_skill(sys.argv[1:], create_skill_feature()))\n',
        )
        print(f"  -> {launcher}")
        return InstallResult(True, spec.id, "skill.py launcher wired to modules/skill/")
