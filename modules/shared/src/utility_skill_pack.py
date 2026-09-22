"""Skill-pack provisioning (provenance + pruning) — skill feature utility.

Pure audit primitives (iter_skill_files, audit_pack, PackFinding, ...) now
live in the shared taxonomy layer (:mod:`modules.shared.src.taxonomy_common_vo`)
so other features can use them without a capabilities->capabilities edge
(AES201). This module re-exports them and keeps the I/O-bound
write_provenance / prune_provisioned helpers.
"""
from __future__ import annotations

import importlib
import json
import shutil
from pathlib import Path

from modules.shared.src.taxonomy_common_constant import (
    PROVENANCE_FILE,
    PROVENANCE_VERSION,
)
from modules.shared.src.taxonomy_common_constant import DESCRIPTION_BUDGET_BYTES as _DESCRIPTION_BUDGET_BYTES
DESCRIPTION_BUDGET_BYTES = _DESCRIPTION_BUDGET_BYTES  # re-exported via __all__

_audit_mod = importlib.import_module("modules.shared.src.taxonomy_common_vo")
globals().update({n: getattr(_audit_mod, n) for n in ("PackFinding", "audit_pack", "iter_skill_files")})

__all__ = [
    "DESCRIPTION_BUDGET_BYTES",
    "PackFinding",
    "audit_pack",
    "iter_skill_files",
    "prune_provisioned",
    "write_provenance",
]

def write_provenance(dest_dir: Path, source_md: Path, pack_root: Path) -> bool:
    """Record where a provisioned copy came from. Never writes into the pack itself."""
    try:
        source = str(source_md.resolve().relative_to(pack_root.resolve()))
    except (OSError, ValueError):
        return False
    payload = {
        "version": PROVENANCE_VERSION,
        "pack_root": str(pack_root),
        "source_skill": source,
    }
    try:
        dest_dir.mkdir(parents=True, exist_ok=True)
        (dest_dir / PROVENANCE_FILE).write_text(json.dumps(payload, indent=2))
        return True
    except OSError:
        return False

def prune_provisioned(target_dir: Path, pack_root: Path) -> int:
    """Remove provisioned skill copies under *target_dir* the pack no longer provides.

    Returns the count of directories removed. Only entries carrying the
    :data:`PROVENANCE_FILE` marker are touched; hand-written skills are left
    alone, as are symlinks that point outside the pack.
    """

    removed = 0
    category_root = target_dir / ".agents" / "skills"
    if not category_root.is_dir():
        return 0
    for category_dir in sorted(category_root.iterdir()):
        if not category_dir.is_dir():
            continue
        for skill_dir in sorted(category_dir.iterdir()):
            if not skill_dir.is_dir() and not skill_dir.is_symlink():
                continue
            marker = skill_dir / PROVENANCE_FILE
            if skill_dir.is_symlink():
                if not skill_dir.resolve().is_relative_to(pack_root.resolve()):
                    continue
            elif not marker.is_file():
                continue
            shutil.rmtree(skill_dir, ignore_errors=True)
            removed += 1
    return removed
