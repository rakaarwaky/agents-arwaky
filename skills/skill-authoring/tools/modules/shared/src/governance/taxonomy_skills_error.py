"""Skills-domain errors (AES governance layer).

Re-exports the full error hierarchy from the shared common layer. The
canonical definitions live in ``shared.src.common.taxonomy_common_error``
so that every module domain (discovery, design, storage, maintenance,
governance, observability) imports from a single SSOT.
"""

from __future__ import annotations

from shared.src.common.taxonomy_common_error import (
    CategoryNameError,
    MutationConflictError,
    SkillNotFoundError,
    SkillsError,
    SkillsRootError,
    SkillsUsageError,
)

__all__ = [
    "CategoryNameError",
    "MutationConflictError",
    "SkillNotFoundError",
    "SkillsError",
    "SkillsRootError",
    "SkillsUsageError",
]
