"""Tool-domain aggregate contract re-export for the uninstaller feature."""
from __future__ import annotations

from modules.shared.src.taxonomy_tool_vo import UninstallResult
from modules.runner.src.contract_tool_runner_aggregate import IToolAggregate

__all__ = ["IToolAggregate"
    'UninstallResult',
]

# Layer-symbol registry (runtime reference for harness/loader introspection).
_layer_symbols = {'IToolAggregate': IToolAggregate, 'UninstallResult': UninstallResult}
