"""Service-domain protocol contract (capability ABC).

Two seam protocols so the service orchestrator coordinates two subsystems:
- ``IServiceControlProtocol`` — mutation ops (start/stop/restart)
- ``IServiceInspectProtocol`` — read ops (status/logs/help)

Capabilities implement these; the composition root injects them into the
orchestrator.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from modules.shared.src.service.taxonomy_service_vo import (
    TARGET_9ROUTER,
    TARGET_ALL,
    TARGET_OMNIROUTE,
    ExitCode,
    ServiceTarget,
)


class IServiceControlProtocol(ABC):
    """Capability contract for service mutation: start / stop / restart."""

    @abstractmethod
    def start(self, target: ServiceTarget = TARGET_ALL) -> ExitCode:
        """Start the named service(s). Return the exit code."""
        ...

    @abstractmethod
    def stop(self, target: ServiceTarget = TARGET_ALL) -> ExitCode:
        """Stop the named service(s). Return the exit code."""
        ...

    @abstractmethod
    def restart(self, target: ServiceTarget = TARGET_ALL) -> ExitCode:
        """Restart the named service(s). Return the exit code."""
        ...


class IServiceInspectProtocol(ABC):
    """Capability contract for service inspection: status / logs / help."""

    @abstractmethod
    def status(self) -> ExitCode:
        """Report the health of every registered service. Return the exit code."""
        ...

    @abstractmethod
    def logs(self, target: ServiceTarget = TARGET_OMNIROUTE) -> ExitCode:
        """Stream the named service's logs. Return the exit code."""
        ...

    @abstractmethod
    def help(self) -> ExitCode:
        """Print the service command usage. Return the exit code."""
        ...


__all__ = [
    "TARGET_9ROUTER",
    "TARGET_ALL",
    "TARGET_OMNIROUTE",
    "ExitCode",
    "IServiceControlProtocol",
    "IServiceInspectProtocol",
    "ServiceTarget",
]

# Layer-symbol registry (runtime reference for harness/loader introspection).
_layer_symbols = {
    "TARGET_9ROUTER": TARGET_9ROUTER,
    "TARGET_ALL": TARGET_ALL,
    "TARGET_OMNIROUTE": TARGET_OMNIROUTE,
    "ExitCode": ExitCode,
    "ServiceTarget": ServiceTarget,
    "IServiceControlProtocol": IServiceControlProtocol,
    "IServiceInspectProtocol": IServiceInspectProtocol,
}
