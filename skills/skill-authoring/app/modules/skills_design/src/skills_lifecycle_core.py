"""Shared record/transition helpers for skill lifecycle capabilities.

Pure helpers that read, write, and mutate the per-skill ``.usage.json``
sidecar, plus the archive/restore path resolution used by the transition
capabilities. Imports only ``common_lifecycle_support`` and shared
utilities; never imports a capability module.
"""

from __future__ import annotations

from pathlib import Path

from shared.src.common.utility_skill_pack import default_pack_root
from shared.src.common.utility_skills_mutation import (
    archive_root,
    assert_within_root,
    atomic_write_json,
)
from shared.src.skills_design.taxonomy_skills_constant import ARCHIVE_DIRNAME
from shared.src.skills_design.taxonomy_skills_error import SkillNotFoundError

from skills_design.src.common_lifecycle_support import _read_sidecar, _usage_path

__all__ = [
    "find_skill_dir",
    "read_record",
    "write_record",
    "set_field",
    "set_state",
    "archive_skill",
    "restore_skill",
]


def find_skill_dir(skill: str, root: Path, in_archive: bool = False) -> Path | None:
    search_root = archive_root(root) if in_archive else root
    if not search_root.is_dir():
        return None
    matches: list[Path] = []
    for p in search_root.rglob("SKILL.md"):
        if not in_archive and ARCHIVE_DIRNAME in p.parts:
            continue
        if p.parent.name == skill:
            matches.append(p.parent)
    return sorted(matches)[0] if matches else None


def read_record(skill_dir: Path) -> dict:
    return _read_sidecar(_usage_path(skill_dir))


def write_record(skill_dir: Path, record: dict) -> None:
    atomic_write_json(_usage_path(skill_dir), record)


def set_field(skill_dir: Path, field: str, value: object) -> None:
    record = read_record(skill_dir)
    record[field] = value
    write_record(skill_dir, record)


def set_state(skill_dir: Path, state: str, archived_at: str | None = None) -> None:
    record = read_record(skill_dir)
    record["state"] = state
    if archived_at is not None:
        record["archived_at"] = archived_at
    write_record(skill_dir, record)


def archive_skill(skill: str, pack_root: Path) -> dict:
    skill_dir = find_skill_dir(skill, pack_root, in_archive=False)
    if skill_dir is None:
        if find_skill_dir(skill, pack_root, in_archive=True) is not None:
            return {"skill": skill, "archived": False, "reason": "already-archived"}
        raise SkillNotFoundError(f"No skill directory found for: {skill}")

    from skills_design.src.common_lifecycle_support import _now_iso

    category = skill_dir.parent.name
    destination = archive_root(pack_root) / category / skill
    assert_within_root(destination, pack_root)
    record = read_record(skill_dir)
    prior_state = record.get("state", "active")
    now_iso_val = _now_iso()

    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists():
        from shared.src.skills_design.taxonomy_skills_error import (
            MutationConflictError,
        )

        raise MutationConflictError(f"Archive slot already exists: {destination}")
    set_state(skill_dir, "archived", archived_at=now_iso_val)
    try:
        skill_dir.replace(destination)
    except OSError:
        record["state"] = prior_state
        record.pop("archived_at", None)
        write_record(skill_dir, record)
        from shared.src.skills_design.taxonomy_skills_error import (
            MutationConflictError,
        )

        raise MutationConflictError(
            f"Archive of {skill} failed mid-transaction; rolled back."
        ) from None

    return {"skill": skill, "archived": True, "archived_at": now_iso_val}


def restore_skill(skill: str, pack_root: Path, reanchor=None) -> dict:
    archived_dir = find_skill_dir(skill, pack_root, in_archive=True)
    if archived_dir is None:
        if find_skill_dir(skill, pack_root, in_archive=False) is None:
            raise SkillNotFoundError(f"No skill directory found for: {skill}")
        return {"skill": skill, "restored": False, "reason": "not-archived"}

    from skills_design.src.common_lifecycle_support import _now_iso

    category = archived_dir.parent.name
    destination = pack_root / category / skill
    assert_within_root(destination, pack_root)
    record = read_record(archived_dir)
    prior_state = record.get("state", "archived")
    prior_archived_at = record.get("archived_at")

    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists():
        from shared.src.skills_design.taxonomy_skills_error import (
            MutationConflictError,
        )

        raise MutationConflictError(f"Restore slot already exists: {destination}")

    record["state"] = "active"
    record.pop("archived_at", None)
    record["activity_window_start"] = _now_iso()
    write_record(archived_dir, record)
    try:
        archived_dir.replace(destination)
    except OSError:
        record["state"] = prior_state
        if prior_archived_at is not None:
            record["archived_at"] = prior_archived_at
        write_record(archived_dir, record)
        from shared.src.skills_design.taxonomy_skills_error import (
            MutationConflictError,
        )

        raise MutationConflictError(
            f"Restore of {skill} failed mid-transaction; rolled back."
        ) from None

    if reanchor is not None:
        reanchor(skill, pack_root)
    return {"skill": skill, "restored": True, "state": "active"}
