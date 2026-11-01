"""Daemon import capability contract (AES102 `_protocol`).

Single protocol seam for the OmniRoute -> 9router credential import
capability. A capability implements this class outright; the surface and
root never import the capability module directly.
"""
from __future__ import annotations

from abc import ABC, abstractmethod

from modules.shared.src.daemon.taxonomy_daemon_vo import ExitCode


class I9routerImportOmnirouteProtocol(ABC):
    """Capability contract for the 9router OmniRoute import verb.

    One method: ``run_import``. The caller supplies the daemon stop/start
    callables so the capability stays free of direct capability imports
    (AES201) and of I/O beyond the SQLite write it owns.
    """

    @abstractmethod
    def run_import(
        self,
        argv: list[str],
        stop_fn,
        start_fn,
    ) -> ExitCode:
        """Run ``9router import-omniroute [--dry-run] [--provider X]``.

        *argv* are the CLI arguments after ``import-omniroute``.
        *stop_fn* / *start_fn* are injected by the surface or root so this
        capability never imports a sibling capability module.
        """
        ...


__all__ = ["I9routerImportOmnirouteProtocol"]

# Layer-symbol registry (runtime reference for harness/loader introspection).
_layer_symbols = {
    "I9routerImportOmnirouteProtocol": I9routerImportOmnirouteProtocol,
    "ExitCode": ExitCode,
}
