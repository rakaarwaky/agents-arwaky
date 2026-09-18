"""Centralized path resolution with validation (replaces scattered parents[N])."""
from __future__ import annotations

import os
from pathlib import Path


def _find_repo_root() -> Path:
    """Walk up from this file's location until config/manifest.json is found.

    Works for the main checkout and any git worktree — no fixed parent depth,
    no hardcoded ``modules/shared/config/`` assumption.
    """
    here = Path(__file__).resolve().parent
    for candidate in (here, *here.parents):
        anchor = candidate / "config" / "manifest.json"
        if anchor.exists():
            return candidate
    raise RuntimeError(
        f"agents-arwaky root not found by walking up from {here}. "
        f"Neither {here} nor any parent contains config/manifest.json. "
        f"Set AGENTS_ARWAKY_ROOT explicitly to a checkout that has it."
    )


def repo_root() -> Path:
    """Resolve and validate the agents-arwaky repository root.

    Uses ``config/manifest.json`` as the anchor.  ``AGENTS_ARWAKY_ROOT`` is
    a soft hint: when it points at a checkout that actually contains the
    anchor it is used; otherwise discovery falls back to walking up from this
    file's own location, which always works for the tree the code is running
    out of (main checkout or any git worktree).
    """
    env_root = os.environ.get("AGENTS_ARWAKY_ROOT")
    if env_root:
        root = Path(env_root).resolve()
        for anchor in ("config/manifest.json", "modules/shared/config/manifest.json"):
            if (root / anchor).exists():
                return root
        # env root is stale / wrong layout — fall through to discovery from
        # the file we are currently running out of, instead of failing.
    return _find_repo_root()
