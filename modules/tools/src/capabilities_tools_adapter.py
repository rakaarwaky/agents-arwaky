"""Capability — tool adapter facade (implements IToolsProtocol).

Uniform facade over every tool id: the registry is injected by the root
container (`TOOLS_REGISTRY`, merged from the twelve sibling
`capabilities_tools_*_adapter` modules). This file holds no recipes —
config-driven tools live in their own provider modules (AES201 forbids
importing sibling capabilities here).

Skill structure (`create-capabilities`, AES403) — honoured in-file:

- Role `adapter` is an allowed external role; exactly 1 class
  (`ToolAdapterFacade`) implements the `IToolsProtocol` protocol
  (≥1 implementor, ≤3 types). Imports are taxonomy + `_protocol`
  contract + utility only.
- 3-Block order, class FIRST. Recipes, unit builders, and lifecycles
  live in `utility_tool_mechanics` (≥2 capability consumers).
"""
from __future__ import annotations

from pathlib import Path

from modules.shared.src.contract_tools_protocol import IToolsProtocol
from modules.shared.src.taxonomy_common_error import ToolUpdateError
from modules.shared.src.taxonomy_common_vo import ToolSpec
from modules.shared.src.taxonomy_tools_constant import LAUNCHER_NAMES
from modules.shared.src.utility_tool_mechanics import ROOT, generic_owned


# ─── Block 1: Class Definition & Constructor ─────────────────────────
class ToolAdapterFacade(IToolsProtocol):
    """Unified facade: one injected object holding every tool's actions."""

    def __init__(
        self,
        registry: dict[str, object] | None = None,
        daemons=None,
        root: Path | None = None,
    ) -> None:
        self._registry = dict(registry) if registry is not None else {}
        self._daemons = daemons
        self._root = root

    # ─── Block 2: Public Contract (domain protocol ONLY, protocol order) ──
    def execute(
        self,
        op: str,
        spec: ToolSpec | None = None,
        query: object | None = None,
        args: list[str] | None = None,
    ) -> object:
        """Single protocol entry: dispatch *op* to the facade's shared mechanics."""
        if op == "owned_paths":
            if spec is None:
                raise ToolUpdateError("facade got op='owned_paths' without a spec")
            root = Path(args[0]) if args else None
            return self.owned_paths(spec, root)
        if op == "resolve":
            if spec is None:
                raise ToolUpdateError("facade got op='resolve' without a spec")
            return self.resolve(spec)
        if op == "install":
            if spec is None:
                raise ToolUpdateError("facade got op='install' without a spec")
            root = Path(args[0]) if args else None
            return self.install(spec, root)
        if op == "update":
            if spec is None:
                raise ToolUpdateError("facade got op='update' without a spec")
            root = Path(args[0]) if args else None
            return self.update(spec, root)
        if op == "satisfied":
            if spec is None:
                raise ToolUpdateError("facade got op='satisfied' without a spec")
            return self.satisfied(spec)
        if op == "is_pin_satisfied":
            if spec is None:
                raise ToolUpdateError("facade got op='is_pin_satisfied' without a spec")
            return self.is_pin_satisfied(spec)
        if op == "is_registered":
            if spec is None:
                raise ToolUpdateError("facade got op='is_registered' without a spec")
            return self.is_registered(spec)
        raise ToolUpdateError(f"unsupported facade op {op!r}")

    def resolve(self, spec: ToolSpec) -> object:
        """Uniform action surface for *spec* (unit lookup)."""
        return self._unit(spec)

    def is_registered(self, spec: ToolSpec) -> bool:
        return spec.id in self._registry

    def satisfied(self, spec: ToolSpec) -> bool:
        """Adapter's idempotence probe (True when the tool is already at pin)."""
        unit = self._unit(spec)
        fn = getattr(unit, "satisfied", None)
        return bool(fn(spec, self._root_for(None))) if callable(fn) else False

    def is_pin_satisfied(self, spec: ToolSpec) -> tuple[bool, str]:
        """Adapter's pin-check for the updater (True, reason) when satisfied."""
        unit = self._unit(spec)
        fn = getattr(unit, "is_pin_satisfied", None)
        return fn(spec, self._root_for(None)) if callable(fn) else (False, "no pin check")

    def install(self, spec: ToolSpec, root: Path | None = None) -> list[Path]:
        """Run the tool's install build (source-init lives inside the action)."""
        r = self._root_for(root)
        unit = self._unit(spec)
        fn = getattr(unit, "install", None)
        if not callable(fn):
            return []
        try:
            return list(fn(spec, r, daemons=self._daemons) or [])
        except TypeError:
            return list(fn(spec, r) or [])

    def update(self, spec: ToolSpec, root: Path | None = None) -> list[Path]:
        """Run the tool's update build (git-update lives inside the action)."""
        r = self._root_for(root)
        unit = self._unit(spec)
        fn = getattr(unit, "update", None)
        return list(fn(spec, r) or []) if callable(fn) else []

    def owned_paths(self, spec: ToolSpec, root: Path | None = None) -> list[Path]:
        """The tool's teardown set (per-tool action, generic fallback)."""
        unit = self._unit(spec)
        fn = getattr(unit, "owned_paths", None)
        if callable(fn):
            return list(fn(spec, self._root_for(root)) or [])
        return generic_owned(spec, LAUNCHER_NAMES.get(spec.id, [spec.id]))

    # ─── Block 3: Dunder Methods, Factories & Helpers ────────────────
    def __repr__(self) -> str:
        return f"ToolAdapterFacade(tools={len(self._registry)})"

    def _unit(self, spec: ToolSpec):
        """Resolve the action namespace for *spec* (injected registry)."""
        return self._registry.get(spec.id)

    def _root_for(self, root: Path | None) -> Path:
        """Effective repo root: explicit arg, else injected, else REPO_ROOT."""
        return root or self._root or ROOT


__all__ = ["ToolAdapterFacade"]
