"""Tool-domain aggregate contract re-export for the updater feature.

The updater exposes a single verb (update) through the IToolUpdater surface;
the runner's ToolOrchestrator calls `updater.update(spec)` and delegates here.
"""
from __future__ import annotations

from modules.shared.src.taxonomy_tool_vo import UpdateResult
from modules.updater.src.contract_tool_updater_protocol import IToolUpdater

__all__ = [
    "IToolUpdater",
    "UpdateResult",
]

# Layer-symbol registry (runtime reference for harness/loader introspection).
_layer_symbols = {"IToolUpdater": IToolUpdater, "UpdateResult": UpdateResult}
