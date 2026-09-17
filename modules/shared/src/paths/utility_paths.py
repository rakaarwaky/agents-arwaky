"""Centralized path resolution with validation (replaces scattered parents[N])."""
from __future__ import annotations

import os
from pathlib import Path


def repo_root() -> Path:
    """Resolve and validate the agents-arwaky repository root.

    This module lives at ``modules/shared/src/paths/``, four levels below the
    repo root, so ``parents[4]`` reaches it. ``AGENTS_ARWAKY_ROOT`` overrides.
    """
    env_root = os.environ.get("AGENTS_ARWAKY_ROOT")
    if env_root:
        root = Path(env_root).resolve()
    else:
        root = Path(__file__).resolve().parents[4]

    manifest = root / "tools" / "config" / "manifest.json"
    if not manifest.exists():
        raise RuntimeError(
            f"agents-arwaky root not found at {root}. "
            f"Expected {manifest} to exist. "
            f"Set AGENTS_ARWAKY_ROOT or run from the repository."
        )
    return root
