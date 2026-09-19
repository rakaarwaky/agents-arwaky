"""Updater bumper capability — FR-001: bring a tool to its manifest pin.

Pin comparison first (idempotence); on unsatisfied state dispatch the selected
adapter's update sequence; capture adapter diagnostics into the result without
raising. Dry-run reports the planned invocation with zero side effects.
"""
from __future__ import annotations

from pathlib import Path
from typing import Sequence

from modules.shared.src.taxonomy_tool_vo import ToolSpec, UpdateResult
from modules.updater.src.contract_tool_updater_protocol import (
    IToolBumper,
    IToolUpdaterAdapter,
)


class UpdaterBumper(IToolBumper):
    """Drive the pin-comparison → adapter-dispatch → result-capture flow."""

    def bump(
        self,
        spec: ToolSpec,
        adapter: IToolUpdaterAdapter,
        dry_run: bool = False,
        *,
        root: Path,
    ) -> UpdateResult:
        satisfied, state_desc = adapter.is_pin_satisfied(spec, root)
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
            artifacts = adapter.update(spec, root)
        except Exception as exc:  # adapter raises; bumper folds it in
            return UpdateResult(False, spec.id, f"adapter failure: {exc}")

        touched = ", ".join(str(p) for p in artifacts) or "no artifacts"
        return UpdateResult(
            True, spec.id,
            f"{spec.id} updated ({state_desc} → manifest pin); touched: {touched}",
        )


__all__ = ["UpdaterBumper"]
