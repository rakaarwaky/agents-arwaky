"""Lifecycle config value object (AES taxonomy layer, config side).

``LifecycleConfig`` defines the lifecycle settings with sensible defaults.
``load_lifecycle_config`` reads ``.lifecycle_config.json`` from the pack
root and overlays it over the dataclass defaults.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from pathlib import Path

from shared.src.common.utility_skill_pack import default_pack_root
from shared.src.skills_design.taxonomy_skills_request import SkillsRoot

logger = logging.getLogger(__name__)

CONFIG_FILENAME = ".lifecycle_config.json"

__all__ = [
    "CONFIG_FILENAME",
    "LifecycleConfig",
    "load_lifecycle_config",
]

@dataclass(frozen=True)
class LifecycleConfig:
    """Defaults for skill lifecycle management."""

    enabled: bool = True
    interval_hours: int = 168
    min_idle_hours: int = 2
    stale_after_days: int = 14
    archive_after_days: int = 30
    consolidate: bool = False
    backup_enabled: bool = True
    backup_keep: int = 2
    archive_ttl_days: int = 0
    pause: bool = False


def load_lifecycle_config(pack_root: SkillsRoot | None = None) -> LifecycleConfig:
    """Read lifecycle config, falling back to defaults."""
    defaults = LifecycleConfig()
    root = Path(pack_root) if pack_root is not None else default_pack_root()
    path = root / CONFIG_FILENAME
    try:
        raw = path.read_text(encoding="utf-8")
        data = json.loads(raw)
    except (OSError, ValueError):
        return defaults
    if not isinstance(data, dict):
        return defaults
    overrides: dict[str, object] = {}
    for key in (
        "enabled",
        "interval_hours",
        "min_idle_hours",
        "stale_after_days",
        "archive_after_days",
        "consolidate",
        "backup_enabled",
        "backup_keep",
        "archive_ttl_days",
        "pause",
    ):
        if key not in data:
            continue
        value = data[key]
        expected = type(getattr(defaults, key))
        if not (
            expected is int
            and type(value) is int
            or expected is bool
            and type(value) is bool
            or expected is not int and expected is not bool and isinstance(value, expected)
        ):
            logger.warning(
                "lifecycle config %r has wrong type %s, using default",
                key,
                type(value).__name__,
            )
            continue
        overrides[key] = value
    backup = data.get("backup")
    if isinstance(backup, dict):
        if isinstance(backup.get("enabled"), bool) and type(backup["enabled"]) is bool:
            overrides["backup_enabled"] = backup["enabled"]
        keep = backup.get("keep")
        if isinstance(keep, int) and type(keep) is int:
            overrides["backup_keep"] = keep
    if overrides:
        return LifecycleConfig(**overrides)
    return defaults
