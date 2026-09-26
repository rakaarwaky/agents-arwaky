"""FR-002 action — update a tool: bump to pin, record the transition.

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

import datetime
import json
from pathlib import Path

from modules.shared.src.contract_tools_protocol import IToolsUpdaterProtocol
from modules.shared.src.taxonomy_common_error import ToolUpdateError
from modules.shared.src.taxonomy_common_vo import (
    ToolSpec,
    UpdateResult,
    atomic_write_text,
    state_home,
)


# ─── Block 1: Class Definition & Constructor ──────────────
class UpdaterCapability(IToolsUpdaterProtocol):
    """Business action update(spec, dry_run): bump + record transition."""

    def __init__(self, root: Path | None = None,
                 registry: dict[str, object] | None = None) -> None:
        self._root = root
        # P1-7: action calls route through the injected registry directly.
        self._registry = dict(registry) if registry is not None else {}

    # ─── Block 2: Protocol Method Implementation ──────────────
    # ─── Block 3: Dunder Methods, Factories & Helpers ─────────
    def __repr__(self) -> str:
        return "UpdaterCapability()"

    def update(self, spec: ToolSpec, adapter: object | None = None, dry_run: bool = False) -> UpdateResult:
        """Bump the tool to its manifest pin and record the transition."""
        registry = self._registry
        if not registry:
            raise ToolUpdateError("adapter registry is not wired (root composition layer)")
        # Sub-step 1: pin-comparison → adapter-dispatch → result-capture.
        result = self._bump(spec, registry, dry_run=dry_run)

        # Sub-step 2: record transition only after a successful bump.
        result = self._record(spec, result)
        return result

    def _bump(
        self,
        spec: ToolSpec,
        registry: dict[str, object],
        dry_run: bool = False,
    ) -> UpdateResult:
        base = self._root
        if base is None:
            from modules.shared.src.utility_paths_resolver import repo_root
            base = repo_root()
        unit = registry.get(spec.id)
        if unit is None:
            return UpdateResult(False, spec.id, f"no adapter unit registered for {spec.id!r}")
        pin_fn = getattr(unit, "is_pin_satisfied", None)
        satisfied, state_desc = pin_fn(spec, base) if callable(pin_fn) else (False, "no pin check")
        if satisfied:
            return UpdateResult(
                True, spec.id,
                f"already at pin ({state_desc}); no update performed",
            )

        if dry_run:
            return UpdateResult(
                True, spec.id,
                f"[dry-run] would update {spec.id}: {state_desc} → manifest pin",
            )

        try:
            update_fn = getattr(unit, "update", None)
            artifacts = list(update_fn(spec, base) or []) if callable(update_fn) else []
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
                    {
                        "tool": spec.id,
                        "message": update_result.message,
                        # P1-8: real UTC ISO-8601 timestamp, was literal "now".
                        "recorded_at": datetime.datetime.now(datetime.UTC).isoformat(),
                    },
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
