"""Path helpers for the agents-arwaky repository (utility layer).

Backed by :mod:`modules.shared.src.taxonomy_common_constant` — no other
utility-layer import (AES201 rule 4).
"""
from __future__ import annotations

from modules.shared.src.taxonomy_common_constant import REPO_ROOT


def repo_root() -> type[REPO_ROOT] | object:
    """Return the repository root as a Path."""
    return REPO_ROOT


def repo_dir() -> type[REPO_ROOT] | object:
    """Alias of :func:`repo_root`."""
    return REPO_ROOT
