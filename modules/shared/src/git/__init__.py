"""Git submodule helpers — utility + contract + capabilities (P4-A4).\n\nMoved from common.git; consumers import from ``modules.shared.src.git``.\n"""
from __future__ import annotations

from modules.shared.src.git.contract_git_protocol import IGitUpdater
from modules.shared.src.git.utility_git_submodule import GitSubmoduleUpdater
from modules.shared.src.git.utility_git_update import (
    fetch_remote,
    get_current_commit,
    get_remote_default_branch,
    has_newer_commits,
    pull_submodule,
    run_quiet,
)

__all__ = [
    "IGitUpdater",
    "GitSubmoduleUpdater",
    "fetch_remote",
    "get_current_commit",
    "get_remote_default_branch",
    "has_newer_commits",
    "pull_submodule",
    "run_quiet",
]
