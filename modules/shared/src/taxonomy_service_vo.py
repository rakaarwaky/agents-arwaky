"""Service-domain value objects for the AES service feature."""
from __future__ import annotations

from typing import NewType

#: Process or command exit code (0 = success, non-zero = failure).
ExitCode = NewType("ExitCode", int)

#: Service target name ("omniroute", "anytype", "all").
ServiceTarget = NewType("ServiceTarget", str)

#: Service operation token routed through the protocol (status/start/stop/...).
ServiceOp = NewType("ServiceOp", str)

#: Module-level singletons for default arguments (B008).
TARGET_ALL: ServiceTarget = ServiceTarget("all")
TARGET_OMNIROUTE: ServiceTarget = ServiceTarget("omniroute")
