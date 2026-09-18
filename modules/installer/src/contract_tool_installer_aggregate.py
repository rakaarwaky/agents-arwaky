"""Tool-domain aggregate contracts (AES102 `_aggregate`) — cross-module tool aggregate.

The runner feature owns the aggregate contract; installer/updater/uninstaller
agents reference it so the AES202 agent layer requires an aggregate import.
"""
from __future__ import annotations

from modules.shared.src.taxonomy_tool_vo import InstallResult
from modules.runner.src.contract_tool_runner_aggregate import IToolAggregate

__all__ = ["IToolAggregate"
    'InstallResult',
]

# Layer-symbol registry (runtime reference for harness/loader introspection).
_layer_symbols = {'IToolAggregate': IToolAggregate, 'InstallResult': InstallResult}
