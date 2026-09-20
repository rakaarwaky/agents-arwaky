"""Capability — unified per-tool adapter facade (implements IToolAdapterFacade).

Wraps the registry of 13 per-tool leaf adapters + the shared
`utility_tool_mechanics` helper module into one standardized verb
pipeline. This is the single API the four lifecycle capabilities
(installer / updater / uninstaller / runner) consume, replacing their
previous direct "resolve adapter module + call its verbs + reach inlined
helpers" scattering.

Layering (AES201): the capability layer may import `utility` and
`contract(_protocol)` — both allowed. The facade imports the mechanics
module (utility -> here is fine) and the registry built by the root
container (injected, so the capability stays adapter-free until DI).
"""
from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

from modules.shared.src.taxonomy_tool_vo import ToolSpec
from modules.tools.src.contract_tools_adapter_protocol import IToolAdapterFacade
from modules.tools.src.taxonomy_tools_constant import LAUNCHER_NAMES

# Per-tool leaf adapters (stateless module-level verb functions, AES404).
# Importing them here is allowed: capability -> utility (AES201). The
# registry maps tool_id -> adapter module; the 13 tools with a per-tool
# leaf module are exactly these, which also documents the coverage set.
import modules.tools.src.utility_anytype_adapter as _anytype
import modules.tools.src.utility_blender_adapter as _blender
import modules.tools.src.utility_codegraph_adapter as _codegraph
import modules.tools.src.utility_context7_adapter as _context7
import modules.tools.src.utility_fetch_adapter as _fetch
import modules.tools.src.utility_lint_adapter as _lint
import modules.tools.src.utility_mnemosyne_adapter as _mnemosyne
import modules.tools.src.utility_ninerouter_adapter as _ninerouter
import modules.tools.src.utility_ponytail_adapter as _ponytail
import modules.tools.src.utility_qwen_web_adapter as _qwen_web
import modules.tools.src.utility_vision_adapter as _vision
import modules.tools.src.utility_workspace_adapter as _workspace
from modules.tools.src.utility_tool_mechanics import ROOT as MECHANICS_ROOT
from modules.tools.src.utility_tool_mechanics import generic_owned

#: Coverage invariant: every per-tool leaf module above must appear in the
#: registry the root container builds; a new tool lands in both places.
_ADAPTER_MODULES: dict[str, object] = {
    "anytype": _anytype,
    "blender": _blender,
    "codegraph": _codegraph,
    "context7": _context7,
    "fetch": _fetch,
    "lint": _lint,
    "mnemosyne": _mnemosyne,
    "9router": _ninerouter,
    "ponytail": _ponytail,
    "qwen-web": _qwen_web,
    "vision": _vision,
    "workspace": _workspace,
}


class ToolAdapterFacade(IToolAdapterFacade):
    """One injected facade object; no per-instance state beyond the wiring."""

    # ─── Block 1: Class Definition & Constructor ───────────────
    def __init__(
        self,
        registry: dict[str, object],
        daemons=None,
        root: Path | None = None,
    ) -> None:
        self._registry = registry
        self._daemons = daemons
        self._root = root

    # ─── Block 2: Protocol ABC Method Implementation ─────────────
    def resolve(self, spec: ToolSpec) -> object:
        """Uniform verb surface for *spec*; falls back to the leaf module."""
        unit = self._registry.get(spec.id, _ADAPTER_MODULES.get(spec.id))
        # Namespace units (anytype-daemon) already carry the verb surface;
        # raw modules are wrapped so missing verbs fold to safe defaults.
        if not callable(getattr(unit, "install", None)):
            unit = SimpleNamespace(
                satisfied=getattr(unit, "satisfied", None),
                is_pin_satisfied=getattr(unit, "is_pin_satisfied", None),
                install=self._install_for,
                update=self._update_for,
                owned_paths=self._owned_paths_for,
            )
            self._registry[spec.id] = unit
        return unit

    def is_registered(self, spec: ToolSpec) -> bool:
        return spec.id in self._registry

    def satisfied(self, spec: ToolSpec) -> bool:
        unit = self.resolve(spec)
        fn = getattr(unit, "satisfied", None)
        if not callable(fn):
            return False
        return bool(fn(spec, self._root or MECHANICS_ROOT))

    def is_pin_satisfied(self, spec: ToolSpec) -> tuple[bool, str]:
        unit = self.resolve(spec)
        fn = getattr(unit, "is_pin_satisfied", None)
        if not callable(fn):
            return False, "no pin check"
        return fn(spec, self._root or MECHANICS_ROOT)

    def install(self, spec: ToolSpec, root: Path | None = None) -> list[Path]:
        unit = self.resolve(spec)
        fn = getattr(unit, "install", None)
        if not callable(fn):
            return []
        return list(fn(spec, root or self._root or MECHANICS_ROOT) or [])

    def update(self, spec: ToolSpec, root: Path | None = None) -> list[Path]:
        unit = self.resolve(spec)
        fn = getattr(unit, "update", None)
        if not callable(fn):
            return []
        return list(fn(spec, root or self._root or MECHANICS_ROOT) or [])

    def owned_paths(self, spec: ToolSpec, root: Path | None = None) -> list[Path]:
        unit = self.resolve(spec)
        fn = getattr(unit, "owned_paths", None)
        if not callable(fn):
            return []
        return list(fn(spec, root or self._root or MECHANICS_ROOT) or [])

    # ─── Block 3: Dunder Methods, Factories & Helpers ────────────
    def _install_for(self, spec, root):
        """Wrap a module unit's install with the injected daemon aggregate."""
        unit = self._registry.get(spec.id, _ADAPTER_MODULES.get(spec.id))
        fn = getattr(unit, "install", None)
        if not callable(fn):
            return []
        return fn(spec, root, daemons=self._daemons)

    def _update_for(self, spec, root):
        unit = self._registry.get(spec.id, _ADAPTER_MODULES.get(spec.id))
        fn = getattr(unit, "update", None)
        if not callable(fn):
            return []
        return fn(spec, root)

    def _owned_paths_for(self, spec, root):
        unit = self._registry.get(spec.id, _ADAPTER_MODULES.get(spec.id))
        fn = getattr(unit, "owned_paths", None)
        if callable(fn):
            return fn(spec, root)
        # Fallback only for raw module units that lack the verb: generic
        # XDG owned set via shared mechanics, launcher names from the
        # taxonomy table.
        return generic_owned(
            spec, LAUNCHER_NAMES.get(spec.id, [spec.id])
        )

    def __repr__(self) -> str:
        return f"ToolAdapterFacade(tools={len(self._registry)})"


__all__ = ["ToolAdapterFacade"]


__all__ = ["ToolAdapterFacade"]
