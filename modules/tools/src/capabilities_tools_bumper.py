"""FR-003 capability — bring a tool to its manifest pin.

Pin comparison first (idempotence); on unsatisfied state dispatch the
selected adapter's update sequence; capture adapter diagnostics into the
result without raising. Dry-run reports the planned invocation with zero
side effects.
"""
from __future__ import annotations

from pathlib import Path

from modules.shared.src.taxonomy_tool_vo import ToolSpec, UpdateResult
from modules.tools.src.contract_tools_protocol import IToolAdapter, IToolBumper


class BumperCapability(IToolBumper):
    """Drive the pin-comparison → adapter-dispatch → result-capture flow."""

    def __init__(self, root: Path | None = None) -> None:
        self._root = root

    def bump(
        self,
        spec: ToolSpec,
        adapter: IToolAdapter,
        dry_run: bool = False,
        *,
        root: Path | None = None,
    ) -> UpdateResult:
        base = root or self._root
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
        except Exception as exc:  # adapter raises; bumper folds it in
            return UpdateResult(False, spec.id, f"adapter failure: {exc}")

        touched = ", ".join(str(p) for p in artifacts) or "no artifacts"
        return UpdateResult(
            True, spec.id,
            f"{spec.id} updated ({state_desc} → manifest pin); touched: {touched}",
        )


__all__ = ["BumperCapability"]
