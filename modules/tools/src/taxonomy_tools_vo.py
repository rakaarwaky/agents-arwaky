"""Tool-domain value objects for the unified tools feature.

The lifecycle results (install/update/uninstall) and the resolved
`ToolSpec` view live in the shared tool domain and are aliased here so the
tools module stays self-contained at the type-annotation level. The two
local VOs below keep primitive `str`/`int` out of the contract signatures
(AES402):

- `ToolQuery`: manifest id / binary / alias text a spec is resolved from.
- `ExitCode`: process exit code returned by the run verb.
"""
from __future__ import annotations

from typing import NewType

from modules.shared.src.taxonomy_tool_vo import (
    InstallResult as _InstallResult,
)
from modules.shared.src.taxonomy_tool_vo import (
    ToolSpec as _ToolSpec,
)
from modules.shared.src.taxonomy_tool_vo import (
    UninstallResult as _UninstallResult,
)
from modules.shared.src.taxonomy_tool_vo import (
    UpdateResult as _UpdateResult,
)

#: Alias so annotations read from the local taxonomy layer (AES501: this
#: module is imported by contract_* and the root entry, never orphaned).
ToolSpec = _ToolSpec
InstallResult = _InstallResult
UninstallResult = _UninstallResult
UpdateResult = _UpdateResult

#: Manifest lookup text (id / binary / alias). Identity at runtime.
ToolQuery = NewType("ToolQuery", str)

#: Process exit code from the run verb. Identity at runtime.
ExitCode = NewType("ExitCode", int)

__all__ = [
    "ExitCode",
    "InstallResult",
    "ToolQuery",
    "ToolSpec",
    "UninstallResult",
    "UpdateResult",
]
