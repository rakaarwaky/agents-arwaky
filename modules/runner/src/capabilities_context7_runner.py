"""Context7Runner — per-tool runner capability (delegates discovery/execution to RunnerBase)."""
from __future__ import annotations
from modules.shared.src.taxonomy_tool_vo import ToolSpec


from modules.runner.src.contract_tool_runner_protocol import IToolExecutor
from modules.runner.src.contract_runner_base import RunnerBase


# ─── Block 1: Class Definition & Constructor ──────────────

class Context7Runner(RunnerBase, IToolExecutor):
    """Per-tool runner capability for context7; inherits RunnerBase behaviour."""

    # ─── Block 2: Protocol ABC Method Implementation ──────────
    # (inherited from RunnerBase: find_executable, run)

    # ─── Block 3: Dunder Methods, Factories & Helpers ───────
    def __repr__(self) -> str:
        return f"{self.__class__.__name__}()"

__all__ = ['ToolSpec']

#

# Layer-symbol registry (runtime reference for harness/loader introspection).
_layer_symbols = {"ToolSpec": ToolSpec}
