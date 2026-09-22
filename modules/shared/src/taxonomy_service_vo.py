"""Service-domain value objects for the AES service feature."""
from __future__ import annotations

from typing import NewType

#: Process or command exit code (0 = success, non-zero = failure).
ExitCode = NewType("ExitCode", int)

#: Service target name ("omniroute", "anytype", "all").
ServiceTarget = NewType("ServiceTarget", str)
