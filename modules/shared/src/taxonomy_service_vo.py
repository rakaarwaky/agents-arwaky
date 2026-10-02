"""Service-domain value objects for the AES service feature."""
from __future__ import annotations

from dataclasses import dataclass
from typing import NewType

#: Process or command exit code (0 = success, non-zero = failure).
ExitCode = NewType("ExitCode", int)

#: Service target name ("anytype", "omniroute", "all").
ServiceTarget = NewType("ServiceTarget", str)

#: Service operation token carried by a ServiceRequest (``status``/``start``/...).
ServiceOp = NewType("ServiceOp", str)

#: Service response envelope returned by ``IServiceAggregate.execute``.
ServiceResponse = NewType("ServiceResponse", ExitCode)

#: Module-level singletons for default arguments (B008).
TARGET_ALL: ServiceTarget = ServiceTarget("all")

#: Default single-daemon target for ``logs``; the first host-native gateway.
TARGET_OMNIROUTE: ServiceTarget = ServiceTarget("omniroute")

#: Module-level singleton for the empty response (B008).
RESPONSE_DEFAULT: ServiceResponse = ServiceResponse(ExitCode(0))


@dataclass(frozen=True)
class ServiceRequest:
    """One service request the surface/root/CLI hands to the aggregate.

    Every consumer verb of the service feature is a value of ``op``; the
    aggregate dispatches to the matching protocol method internally, so the
    aggregate keeps a single ``execute`` entry point.
    """

    op: ServiceOp
    target: ServiceTarget = TARGET_ALL
    logs_target: ServiceTarget = TARGET_OMNIROUTE


__all__ = [
    "RESPONSE_DEFAULT",
    "TARGET_OMNIROUTE",
    "TARGET_ALL",
    "ExitCode",
    "ServiceOp",
    "ServiceRequest",
    "ServiceResponse",
    "ServiceTarget",
]
