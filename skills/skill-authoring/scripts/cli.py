#!/usr/bin/env python3
"""Back-compat shim for the retired path-invocable skill-authoring CLI.

The implementation moved into the AES feature and is exposed as
``aa skills <verb>`` (``modules/cli/src/surface_skills_command.py`` +
``modules/skills/src/``). This shim keeps the old path working for one
release so agent instructions and muscle memory do not break mid-flight::

    python3 skills/skill-authoring/scripts/cli.py validate --summary

It prints a one-line deprecation notice to **stderr** (never stdout —
callers parse stdout) and delegates to the same surface, so the report
text and exit codes are identical.

Delete this file (and the ``scripts/`` directory) once the shim has
shipped for a release.
"""

from __future__ import annotations

import sys
from pathlib import Path

_SCRIPTS_DIR = Path(__file__).resolve().parent


def _repo_root() -> Path:
    """Walk up from the pack to the directory that carries ``.git``.

    A git worktree stores its ``.git`` as a file, so the marker is present
    both in the main clone and in any worktree.
    """
    for candidate in _SCRIPTS_DIR.parents:
        if (candidate / ".git").exists() or (candidate / "modules").is_dir():
            return candidate
    return _SCRIPTS_DIR.parents[2]


def main(argv: list[str] | None = None) -> int:
    """Delegate to ``aa skills``; return the same exit code."""
    repo_root = _repo_root()
    if str(repo_root) not in sys.path:
        sys.path.insert(0, str(repo_root))

    from modules.cli.src.surface_skills_command import cmd_skills
    from modules.skills.src.root_skills_container import default_aggregate

    print(
        "WARNING: skills/skill-authoring/scripts/cli.py is deprecated; "
        "use `aa skills <command>` instead.",
        file=sys.stderr,
    )
    return cmd_skills(
        list(sys.argv[1:] if argv is None else argv), default_aggregate()
    )


if __name__ == "__main__":
    sys.exit(main())
