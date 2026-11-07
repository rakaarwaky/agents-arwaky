"""Curator config value object (AES taxonomy layer, config side).

``CuratorConfig`` mirrors the ``curator:`` keys from the Hermes Agent
Curator config spec (``curator-config.md``) with their defaults,
flattening the nested ``backup`` keys into ``backup_enabled`` /
``backup_keep``. ``load_curator_config`` overlays
``<pack_root>/.curator_config.json`` over the dataclass defaults; a
missing or invalid file returns the bare defaults, so capabilities stay
config-free and never raise on a bad file.

No I/O beyond the one config read; no imports from
utility/capabilities/agent/root/surface layers.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from pathlib import Path

from shared.src.common.utility_skill_pack import default_pack_root
from shared.src.skills_design.taxonomy_skills_request import SkillsRoot

logger = logging.getLogger(__name__)

#: Curator config filename under the pack root.
CONFIG_FILENAME = ".curator_config.json"

__all__ = [
    "CONFIG_FILENAME",
    "CuratorConfig",
    "load_curator_config",
]

@dataclass(frozen=True)
class CuratorConfig:
    """Defaults for the curator lifecycle (``curator-config.md`` table)."""

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

def load_curator_config(pack_root: SkillsRoot | None = None) -> CuratorConfig:
    """Read the curator config overlay, falling back to the defaults.

    Resolves the pack root via ``default_pack_root()`` when ``pack_root``
    is ``None``; reads ``<pack_root>/.curator_config.json`` and overlays
    its values over the ``CuratorConfig`` defaults. A missing file,
    invalid JSON, or wrong-typed keys all return the bare defaults
    (a logged warning, never an exception).
    """
    defaults = CuratorConfig()
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
        # ``bool`` subclasses ``int``, so a JSON ``true`` for an int key
        # (or a JSON int for a bool key) must be rejected with a strict
        # type check.
        if not (
            expected is int
            and type(value) is int
            or expected is bool
            and type(value) is bool
            or expected is not int and expected is not bool and isinstance(value, expected)
        ):
            logger.warning(
                "curator config %r has wrong type %s, using default",
                key,
                type(value).__name__,
            )
            continue
        overrides[key] = value
    # Nested ``backup`` keys flatten to ``backup_enabled`` / ``backup_keep``.
    backup = data.get("backup")
    if isinstance(backup, dict):
        if isinstance(backup.get("enabled"), bool) and type(backup["enabled"]) is bool:
            overrides["backup_enabled"] = backup["enabled"]
        keep = backup.get("keep")
        if isinstance(keep, int) and type(keep) is int:
            overrides["backup_keep"] = keep
    if overrides:
        return CuratorConfig(**overrides)  # type: ignore[arg-type]
    return defaults
