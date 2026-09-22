"""Tool-domain value objects for the unified tools feature.

The lifecycle results (install/update/uninstall) and the resolved
`ToolSpec` view live in the shared tool domain and are aliased here so the
tools module stays self-contained at the type-annotation level. The
local VOs below keep primitive `str`/`int`/bare `dict` out of the
capability signatures (AES402):

- `ToolQuery`: manifest id / binary / alias text a spec is resolved from.
- `ExitCode`: process exit code returned by the run verb.
- `ToolLifecycleConfig`: immutable install recipe of a config-driven tool
  (extracted from the adapter's `SIMPLE_TOOLS_CONFIG` dicts).
- `AdapterUnit`: the five verb callables registered per tool id
  (replaces the adapter's ad-hoc `SimpleNamespace` units).
"""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import NewType

from modules.shared.src.taxonomy_common_vo import (
    InstallResult as _InstallResult,
)
from modules.shared.src.taxonomy_common_vo import (
    ToolSpec as _ToolSpec,
)
from modules.shared.src.taxonomy_common_vo import (
    UninstallResult as _UninstallResult,
)
from modules.shared.src.taxonomy_common_vo import (
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


@dataclass(frozen=True)
class ToolLifecycleConfig:
    """Immutable install/update recipe for one config-driven tool.

    `lifecycle` picks the runner family (`uv_venv` / `uv_project` /
    `node`); the remaining fields are consumed by that family only.
    Launcher entries are `(name, target)` pairs for uv families and
    plain binary names for the node family.
    """

    lifecycle: str
    src_rel: str
    launchers: tuple[str | tuple[str, str], ...]
    tool_name: str | None = None
    pin_reason: str = "rebuild required"
    satisfied_bin: str | None = None
    # uv_venv family
    init_message: str = ""
    post_install_hook: Callable[[Path, Path], None] | None = None
    extra_paths_fn: Callable[[], list[Path]] | None = None
    # uv_project family
    uv_args: tuple[str, ...] | None = None
    alias_second_to_first: bool = False
    # node family
    app_name: str | None = None
    entry: str | None = None
    ignores: tuple[str, ...] | None = None
    requires: tuple[str, str] | None = None
    src_marker: str = "package.json"
    install_cmd: tuple[str, ...] = ()
    build_cmd: tuple[str, ...] = ()
    # teardown extras (any family)
    extra_paths: tuple[Path, ...] | None = None
    config_dirs: tuple[str, ...] | None = None


@dataclass(frozen=True)
class AdapterUnit:
    """The five adapter verb callables registered for one tool id."""

    satisfied: Callable[..., bool]
    install: Callable[..., list[Path]]
    update: Callable[..., list[Path]]
    is_pin_satisfied: Callable[..., tuple[bool, str]]
    owned_paths: Callable[..., list[Path]]


__all__ = [
    "AdapterUnit",
    "ExitCode",
    "InstallResult",
    "ToolLifecycleConfig",
    "ToolQuery",
    "ToolSpec",
    "UninstallResult",
    "UpdateResult",
]
