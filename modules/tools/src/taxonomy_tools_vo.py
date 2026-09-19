"""Tool-domain value objects for the unified tools feature.

The four lifecycle results (install/update/uninstall) and the resolved
`ToolSpec` view live in the shared tool domain; re-exported here so the
tools module stays self-contained at the type-annotation level.
"""
from modules.shared.src.taxonomy_tool_vo import (
    InstallResult,
    ToolSpec,
    UninstallResult,
    UpdateResult,
)
from modules.shared.src.taxonomy_manifest_vo import Tool

__all__ = [
    "InstallResult",
    "Tool",
    "ToolSpec",
    "UninstallResult",
    "UpdateResult",
]
