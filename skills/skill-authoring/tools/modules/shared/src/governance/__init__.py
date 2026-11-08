"""Skills-design shared kernel — governance layer.

Typed error contracts for the skills feature: the base ``SkillsError`` and
its typed subclasses carrying the legacy message text and exit codes.
"""
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