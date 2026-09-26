"""Tool-domain value objects for the unified tools feature.

The lifecycle results (install/update/uninstall) and the resolved
`ToolSpec` view live in the shared tool domain and are aliased here so the
tools module stays self-contained at the type-annotation level. The
local VOs below keep primitive `str`/`int`/bare `dict` out of the
capability signatures (AES402):

- `ToolQuery`: manifest id / binary / alias text a spec is resolved from.
- `ExitCode`: process exit code returned by the run action.
- `ToolLifecycleConfig`: immutable install recipe of a config-driven tool
  (one per provider `capabilities_tools_<tool>_adapter` module).
- `AdapterUnit`: the five action callables registered per tool id
  (replaces the adapter's ad-hoc `SimpleNamespace` units).
"""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path
from typing import NewType

from modules.shared.src.taxonomy_common_vo import (
    InstallResult,
    Tool,
    ToolSpec,
    UninstallResult,
    UpdateResult,
)

#: Alias so annotations read from the local taxonomy layer (AES501: this
#: module is imported by contract_* and the root entry, never orphaned).


#: Manifest lookup text (id / binary / alias). Identity at runtime.
ToolQuery = NewType("ToolQuery", str)

#: Legacy op token; new contracts route each verb to a named rich method.
ToolsOp = NewType("ToolsOp", str)

#: Process argument list accepted by the run action.
ToolArgs = NewType("ToolArgs", list)

#: Path list reported by owned_paths / install / update (AES402 VO).
ToolPaths = NewType("ToolPaths", list)

#: (satisfied, reason) pair returned by is_pin_satisfied.
PinCheck = NewType("PinCheck", tuple)

#: Process exit code from the run action. Identity at runtime.
ExitCode = NewType("ExitCode", int)

#: Concrete path (or None) discovered by the runner.
ToolExecutable = NewType("ToolExecutable", Path)


@dataclass(frozen=True)
class ToolRequest:
    """One tools request the surface/root/CLI hands to the aggregate.

    Every consumer verb of the tools feature is a value of ``op``; the
    aggregate dispatches to the matching rich protocol method internally,
    so the aggregate keeps a single ``execute`` entry point.
    """

    op: ToolsOp
    query: ToolQuery = ToolQuery("")
    spec: ToolSpec | None = None
    args: ToolArgs = field(default_factory=lambda: ToolArgs([]))
    owned: tuple[Path, ...] = ()


@dataclass(frozen=True)
class ToolResponse:
    """Tools response envelope returned by ``IToolsAggregate.execute``.

    Each op fills the field its own result shape needs; the aggregate
    surfaces the op-specific payload to the caller.
    """

    spec: ToolSpec | None = None
    tools: tuple[Tool, ...] = ()
    executable: ToolExecutable | None = None
    install: InstallResult | None = None
    update: UpdateResult | None = None
    uninstall: UninstallResult | None = None
    run: ExitCode | None = None


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
    #: Per-tool node writer override (default: single `entry` launcher).
    node_write_launchers_fn: Callable[[Path, bool], list[Path]] | None = None
    #: Per-tool post-copy hook (e.g. pnpm flag append, npm ci bootstrap).
    node_post_copy_hook: Callable[[Path], None] | None = None
    # teardown extras (any family)
    extra_paths: tuple[Path, ...] | None = None
    config_dirs: tuple[str, ...] | None = None


@dataclass(frozen=True)
class AdapterUnit:
    """The five adapter action callables registered for one tool id."""

    satisfied: Callable[..., bool]
    install: Callable[..., ToolPaths]
    update: Callable[..., ToolPaths]
    is_pin_satisfied: Callable[..., PinCheck]
    owned_paths: Callable[..., ToolPaths]


__all__ = [
    "AdapterUnit",
    "ExitCode",
    "InstallResult",
    "Tool",
    "PinCheck",
    "ToolArgs",
    "ToolExecutable",
    "ToolPaths",
    "ToolLifecycleConfig",
    "ToolQuery",
    "ToolRequest",
    "ToolResponse",
    "ToolSpec",
    "ToolPaths",
    "ToolsOp",
    "UninstallResult",
    "UpdateResult",
]
