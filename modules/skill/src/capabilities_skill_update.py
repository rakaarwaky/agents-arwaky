"""Skill update capability — pull internal submodule skills into the pack.

Implements ``ISkillUpdateProtocol``: discovers each internal tool's skill home
(``crates/skills``, ``modules/skills``, ``packages/skills``, or the legacy
``.agents/skills`` fallback) and merges the freshest copy into the shared
``skills/`` pack, stamping each merge with its upstream provenance.

All discovery and file mechanics live in
:mod:`modules.shared.src.utility_skill_update` so this capability stays a thin
delegate over the shared utility (AES201: the surface reaches helpers through
the utility layer, never through a sibling capability).
"""
from __future__ import annotations

import sys

from modules.shared.src.contract_skill_update_protocol import ISkillUpdateProtocol
from modules.shared.src.taxonomy_skill_update_vo import UpdateResult
from modules.shared.src.utility_paths_resolver import repo_root
from modules.shared.src.utility_skill_update import (
    deduplicate_sources,
    discover_skill_sources,
    merge_skill_into_pack,
)


def _log(message: str, stream=None) -> None:
    print(message, file=stream if stream is not None else sys.stdout)


# ─── Block 1: Class Definition & Constructor ──────────────
class SkillUpdateCapability(ISkillUpdateProtocol):
    """Merges internal submodule skill homes into the shared pack."""

    # ─── Block 2: Protocol Method Implementation ──────────────
    def update(
        self,
        tool_id: str = "",
        dry_run: bool = False,
        force: bool = False,
    ) -> UpdateResult:
        root = repo_root()
        pack_root = root / "skills"
        raw = discover_skill_sources(pack_root, root, tool_id)
        if not raw:
            _log("No internal skill sources found — nothing to update.")
            return UpdateResult(True, tool_id or "all", 0, "no sources discovered")

        winners, conflicts = deduplicate_sources(raw)
        if conflicts:
            _log("Source conflicts (winning source selected by priority):")
            for conflict in conflicts:
                _log(f"  [CONFLICT] {conflict}")

        total = len(winners)
        merged = unchanged = skipped = 0
        conflict_labels: list[str] = []
        _log(f"Updating skill pack from {total} source skill(s)...")
        for entry in winners:
            label = f"{entry.tool_id} :: {entry.category}/{entry.skill_name}"
            if dry_run:
                _log(f"  [DRY] {label} -> {entry.source_path}")
                continue
            outcome = merge_skill_into_pack(entry, pack_root, force=force)
            if outcome == "merged":
                merged += 1
                _log(f"  [OK]  {label}")
            elif outcome == "unchanged":
                unchanged += 1
                _log(f"  [SKIP] {label} already current")
            elif outcome == "conflict":
                conflict_labels.append(label)
                _log(f"  [CONFLICT] {label} differs from pack copy; re-run with --force")
            else:
                skipped += 1
                _log(f"  [ERROR] {label}: failed to merge source {entry.source_path}")
        success = not conflict_labels and skipped == 0
        message = (
            f"dry-run: {total} source skill(s) planned, {len(conflicts)} source conflict(s)"
            if dry_run
            else f"merged {merged}, unchanged {unchanged}, "
                 f"conflicted {len(conflict_labels)}, errors {skipped}"
        )
        if conflict_labels:
            _log("Conflicts (skipped unless --force):")
            for label in conflict_labels:
                _log(f"  - {label}")
        return UpdateResult(
            success=success,
            tool_id=tool_id or "all",
            merged=total if dry_run else merged,
            conflicted=len(conflict_labels),
            skipped=skipped,
            message=message,
            conflicts=tuple(conflicts + conflict_labels),
        )

    # ─── Block 3: Dunder Methods, Factories & Helpers ─────────
    def __repr__(self) -> str:
        return "SkillUpdateCapability()"


__all__ = ["SkillUpdateCapability"]

# Layer-symbol registry (runtime reference for harness/loader introspection).
_layer_symbols = {
    "SkillUpdateCapability": SkillUpdateCapability,
}
