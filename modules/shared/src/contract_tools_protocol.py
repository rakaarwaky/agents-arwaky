"""Tool-domain capability contract (AES102 `_protocol`).

One abstract method — ``execute`` — covers every tools capability:
install, update, uninstall, run, resolve, and discover. A capability
receives an operation token plus the optional target, query, and
arguments it needs, and returns the operation's result (an exit code for
``run``).

The former leaf protocols (install / update / uninstall / run / resolve,
the registration and satisfaction probes, and the adapter facade) are
collapsed into this single method: each capability dispatches internally
on *op*, and the agent orchestrator routes every aggregate action
through ``execute``. Capabilities keep their concrete action methods as
internal detail — the protocol surface stays one method.
"""
from __future__ import annotations

from abc import ABC, abstractmethod

from modules.shared.src.taxonomy_common_vo import ToolSpec
from modules.shared.src.taxonomy_tools_vo import ExitCode, ToolArgs, ToolQuery, ToolsOp


class IToolsProtocol(ABC):
    """Single-method capability contract for the tools feature."""

    @abstractmethod
    def execute(
        self,
        op: ToolsOp,
        spec: ToolSpec | None = None,
        query: ToolQuery | None = None,
        args: ToolArgs | None = None,
    ) -> ExitCode | ToolSpec | None:
        """Run one tools operation under *op*; return its result or exit code.

        Args:
            op: Operation token — ``install``, ``update``, ``uninstall``,
                ``run``, ``resolve``, ``discover`` (adapter sub-ops such
                as ``owned_paths`` stay internal to the capability).
            spec: Resolved target tool specification, when the op needs one.
            query: Raw query (id / binary / alias), when the op resolves.
            args: Argument list — run args, owned-path strings, or flags.

        Returns:
            The op's result object, or an ``ExitCode`` for ``run``.
            A failed / non-zero result signals the error to the caller;
            unexpected ops raise a typed domain error (contract breach,
            never a partial dispatch).
        """
        ...


__all__ = [
    "ExitCode",
    "IToolsProtocol",
    "ToolArgs",
    "ToolQuery",
    "ToolsOp",
]

# Layer-symbol registry (runtime reference for harness/loader introspection).
_layer_symbols = {
    "ExitCode": ExitCode,
    "IToolsProtocol": IToolsProtocol,
    "ToolArgs": ToolArgs,
    "ToolQuery": ToolQuery,
    "ToolsOp": ToolsOp,
}
