"""Git submodule update helpers (moved from tools/lib/git_update.py)."""
from __future__ import annotations

from modules.shared.src.git.capabilities_git_submodule import GitSubmoduleUpdater
from modules.shared.src.git.contract_git_protocol import IGitUpdater
from modules.shared.src.git.utility_git_update import (
    fetch_remote,
    get_current_commit,
    get_remote_default_branch,
    has_newer_commits,
    pull_submodule,
    run_quiet,
    update_submodule,
    write_install_stamp,
)

__all__ = [
    "GitSubmoduleUpdater",
    "IGitUpdater",
    "fetch_remote",
    "get_current_commit",
    "get_remote_default_branch",
    "has_newer_commits",
    "pull_submodule",
    "run_quiet",
    "update_submodule",
    "write_install_stamp",
]
