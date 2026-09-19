"""Updater recorder capability — FR-002: log the version transition.

Runs only after a successful FR-001 bump. Writes a human-readable transition
record under the tool's XDG state dir. Idempotent: re-recording the same
transition is a no-op. Recording failures are folded into the result, never
raised.
"""
from __future__ import annotations

import json
from pathlib import Path

from modules.shared.src.taxonomy_xdg_atomic_io import atomic_write_text
from modules.shared.src.taxonomy_xdg_paths import state_home
from modules.shared.src.taxonomy_tool_vo import ToolSpec, UpdateResult
from modules.updater.src.contract_tool_updater_protocol import IToolRecorder


class UpdaterRecorder(IToolRecorder):
    """Record old→new transitions and keep launcher notes current."""

    def record(self, spec: ToolSpec, update_result: UpdateResult) -> UpdateResult:
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


__all__ = ["UpdaterRecorder"]
