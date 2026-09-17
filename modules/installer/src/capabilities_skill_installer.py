"""Skill installer (in-house Python script) — makes tools/skill/skill.py runnable.

The skill manager is in-house Python (no build step). Its "install" verifies
the script exists under tools/skill/, ensures it carries the executable bit,
and writes a `skill.py` launcher into $XDG_BIN_HOME that runs it via python3
with AGENTS_ARWAKY_ROOT baked in (same pattern as the ninerouter daemon).
"""
from __future__ import annotations

import stat
import subprocess
import sys

from modules.shared.src.paths.utility_paths import repo_root
from modules.shared.src.tool.taxonomy_tool_vo import InstallResult, ToolSpec
from modules.shared.src.tool.contract_tool_protocol import IToolInstaller
from modules.shared.src.xdg.utility_xdg_atomic_io import (
    atomic_write_text,
    ensure_bin_home,
    ensure_path,
)
from modules.shared.src.xdg.utility_xdg_paths import bin_home


SKILL_DIR_REL = "tools/skill"
SCRIPT_NAME = "skill.py"


class SkillInstaller(IToolInstaller):
    """Ensure the in-house skill manager script is executable and launchable."""

    def __init__(self, root=None) -> None:
        self._root = root or repo_root()

    def install(self, spec: ToolSpec) -> InstallResult:
        root = self._root
        script = root / SKILL_DIR_REL / SCRIPT_NAME
        if not script.exists():
            return InstallResult(False, spec.id, f"skill manager script not found at {script}")

        # Ensure the script has the executable bit set.
        st = script.stat()
        if not st.st_mode & stat.S_IXUSR:
            script.chmod(st.st_mode | stat.S_IXUSR)

        # Write a launcher into XDG bin so `aa` and the shell can find it.
        ensure_bin_home()
        ensure_path()
        launcher = bin_home() / "skill.py"
        atomic_write_text(
            launcher,
            "#!/usr/bin/env python3\n"
            "import os, sys\n"
            "from pathlib import Path\n"
            f'root = Path(os.environ.get("AGENTS_ARWAKY_ROOT", {str(root)!r}))\n'
            f'script = root / "{SKILL_DIR_REL}/{SCRIPT_NAME}"\n'
            'os.execvpe("python3", ["python3", str(script), *sys.argv[1:]], os.environ.copy())\n',
        )
        print(f"  -> {launcher}")
        return InstallResult(True, spec.id, "skill.py is executable and launchable")
