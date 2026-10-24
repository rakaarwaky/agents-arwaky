"""Path helpers for the agents-arwaky repository (utility layer).

Backed by :mod:`modules.shared.src.taxonomy_common_constant` — no other
utility-layer import (AES201 rule 4).
"""
from __future__ import annotations

from pathlib import Path

from modules.shared.src.taxonomy_common_constant import REPO_ROOT


def repo_root() -> type[REPO_ROOT] | object:
    """Return the repository root as a Path."""
    return REPO_ROOT


def repo_dir() -> type[REPO_ROOT] | object:
    """Alias of :func:`repo_root`."""
    return REPO_ROOT


def resolve_skills_root(explicit: str | Path | None = None) -> Path:
    """Resolve the skills root: explicit ``--skills-root`` beats derived.

    The derived value is the repository's ``skills/`` pack (the SSOT for
    skill content). An explicit path is expanded (``~``) and resolved so a
    relative CLI argument behaves the same from any working directory.
    """
    if explicit is not None:
        return Path(explicit).expanduser().resolve()
    return REPO_ROOT / "skills"
