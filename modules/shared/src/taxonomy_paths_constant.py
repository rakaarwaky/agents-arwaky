"""Shared-path constants — single source of truth for filesystem anchors (taxonomy layer).

Utility-layer files may import taxonomy (AES201 rule 4) but must not import
each other; these constants are the seam that replaces utility->utility
cross-imports of path primitives.
"""
from __future__ import annotations

from pathlib import Path

#: Repository root (walks up from this file's location: modules/shared/src).
REPO_ROOT: Path = Path(__file__).resolve().parents[3]
