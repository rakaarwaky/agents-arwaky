"""Pytest path setup for the skill-authoring pack tests.

Adds ``scripts/`` and ``_rules/`` (both siblings of this directory) to
``sys.path`` so tests can ``import model, validate, skill_rules`` the
same way the path-invocable entrypoints do — no packaging involved.

Also hosts the session-scoped autouse fixture ``_clean_skills_root``
(moved from ``test_cli.py`` in PR-5): it restores the pristine skills
tree after the suite completes, so no test module — including the new
``test_catalog.py`` and ``test_discover.py`` — can leave a polluted
worktree.
"""

import subprocess
import sys
from pathlib import Path

import pytest

PACK_ROOT = Path(__file__).resolve().parent.parent
for _entry in (PACK_ROOT / "scripts", PACK_ROOT / "_rules"):
    if str(_entry) not in sys.path:
        sys.path.insert(0, str(_entry))


def _find_repo_root() -> Path:
    """Walk up from PACK_ROOT to the directory that carries ``.git``.

    A git worktree stores its ``.git`` as a file (pointing at
    ``gitdir``), so the marker is present both in the main clone and in
    any worktree — regardless of how many directory levels deep the
    checkout lives.
    """
    for candidate in PACK_ROOT.parents:
        if (candidate / ".git").exists():
            return candidate
    raise RuntimeError(
        f"no .git marker found walking up from {PACK_ROOT} — "
        "test must run inside a git clone or worktree"
    )


_REPO_ROOT = _find_repo_root()
_SKILLS_ROOT = _REPO_ROOT / "skills"


@pytest.fixture(scope="session", autouse=True)
def _clean_skills_root() -> None:
    """Regression guard: restore the pristine skills tree after the suite.

    The tests that drive the canonical CLI without ``--skills-root`` run
    against the repo's own ``skills/`` directory. If a test (or a manual
    run of ``repair --apply`` / ``catalog``) leaves behind an untracked
    file, the 0-issue baseline the suite pins shifts and tests fail on
    the next run. This fixture uses ``git checkout`` to restore
    ``skills/CATALOG.md`` from HEAD after the suite completes and to
    delete untracked files it created, guaranteeing a pristine state
    regardless of what the tests did.
    """
    yield

    # Restore tracked files from HEAD; remove any untracked file a test created.
    git_checkout = [
        "git", "checkout", "--",
        "skills/CATALOG.md",
    ]
    subprocess.run(git_checkout, cwd=str(_REPO_ROOT), capture_output=True, check=False)
