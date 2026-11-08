"""Skills-design shared kernel — maintenance layer.

Shared mutation utilities: skill-dir resolution, category-name validation,
containment assertions, atomic writes, lifecycle support, and mutation plan
generators.
"""
from shared.src.maintenance.utility_lifecycle_support import (
    ACTIVE,
    ARCHIVED,
    STALE,
    archive_skill,
    restore_skill,
)
from shared.src.maintenance.utility_skills_mutation import (
    assert_within_root,
    plan_repair,
    plan_weed,
)

__all__ = [
    "ACTIVE",
    "ARCHIVED",
    "STALE",
    "archive_skill",
    "assert_within_root",
    "plan_repair",
    "plan_weed",
    "restore_skill",
]
