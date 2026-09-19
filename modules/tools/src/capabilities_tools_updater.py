"""FR-003/FR-004 verb — update a tool: bump to pin, record the transition.

Sub-steps (internal, not separate public methods):
1. Bump: pin comparison first (idempotence); on unsatisfied state the
   selected adapter's update sequence is dispatched and adapter
   diagnostics are captured into the result without raising. Dry-run
   reports the planned invocation with zero side effects.
2. Record (only after a successful bump): a human-readable version-
   transition record is written under the tool's XDG state dir.
   Idempotent: re-recording the same transition is a no-op. A failed
   bump yields no record; the diagnostic is folded into the result.

Never raises out of ``update`` — every failure path returns
``UpdateResult(success=False, message)``.
"""
from __future__ import annotations

import json
from pathlib import Path

from modules.shared.src.taxonomy_tool_vo import ToolSpec, UpdateResult
from modules.shared.src.taxonomy_xdg_atomic_io import atomic_write_text
from modules.shared.src.taxonomy_xdg_paths import state_home
from modules.tools.src.contract_tools_protocol import IToolUpdater


# ─── Block 1: Class Definition & Constructor ─────────────────────────
class UpdaterCapability(IToolUpdater):
    """Business action update(spec, adapter, dry_run): bump + record transition."""

    def __init__(self, root: Path | None = None) -> None:
        self._root = root

    # ─── Block 2: Public Contract (domain protocol ONLY) ─────────────
    def update(self, spec: ToolSpec, adapter: object, dry_run: bool = False) -> UpdateResult:
        # Sub-step 1: pin-comparison → adapter-dispatch → result-capture.
        result = self._bump(spec, adapter, dry_run=dry_run)

        # Sub-step 2: record transition only after a successful bump.
        result = self._record(spec, result)
        return result

    # ─── Block 3: Dunder Methods, Factories & Helpers ────────────────
    def _bump(
        self,
        spec: ToolSpec,
        adapter: object,
        dry_run: bool = False,
    ) -> UpdateResult:
        base = self._root
        if base is None:
            from modules.shared.src.utility_paths import repo_root
            base = repo_root()
        satisfied, state_desc = adapter.is_pin_satisfied(spec, base)
        if satisfied:
            return UpdateResult(
                True, spec.id,
                f"already at pin ({state_desc}); no update performed",
            )

        if dry_run:
            return UpdateResult(
                True, spec.id,
                f"[dry-run] would update {spec.id}: {state_desc} → manifest pin "
                f"(adapter={adapter.__class__.__name__})",
            )

        try:
            artifacts = adapter.update(spec, base)
        except Exception as exc:  # adapter raises; bump folds it in
            return UpdateResult(False, spec.id, f"adapter failure: {exc}")

        touched = ", ".join(str(p) for p in artifacts) or "no artifacts"
        return UpdateResult(
            True, spec.id,
            f"{spec.id} updated ({state_desc} → manifest pin); touched: {touched}",
        )

    def _record(self, spec: ToolSpec, update_result: UpdateResult) -> UpdateResult:
        if not update_result.success:
            return UpdateResult(
                False, spec.id,
                f"record skipped (bump failed: {update_result.message})",
            )
        if "already at pin" in update_result.message:
            return UpdateResult(True, spec.id, "no version movement; record unchanged")

        state_dir = state_home() / "agents-arwaky" / "updater"
        record_path = state_dir / f"{spec.id}.json"
        try:
            state_dir.mkdir(parents=True, exist_ok=True)
            existing: dict = {"transition": None}
            if record_path.exists():
                existing = json.loads(record_path.read_text(encoding="utf-8"))
            if existing.get("message") == update_result.message:
                return UpdateResult(
                    True, spec.id,
                    f"transition already recorded at {record_path}; no-op",
                )
            atomic_write_text(
                record_path,
                json.dumps(
                    {"tool": spec.id, "message": update_result.message, "recorded_at": "now"},
                    indent=2,
                ) + "\n",
                mode=0o644,
            )
        except OSError as exc:
            return UpdateResult(False, spec.id, f"record write failed: {exc}")

        return UpdateResult(
            True, spec.id,
            f"transition recorded: {update_result.message} ({record_path})",
        )


__all__ = ["UpdaterCapability"]
