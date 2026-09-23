"""Check-domain value objects for the unified check feature.

`CheckExitCode` wraps a raw `int` so contract signatures (`ICheckAggregate`,
`ICheckProtocol`) can return the gate result without exposing a primitive
(AES402). `CheckOnly` scopes a selective run (`docs` | `skill` | `all`).
Identity at runtime — bare primitives.
"""
from __future__ import annotations

from typing import NewType

#: Gate exit code: 0 = pass, non-zero = fail (count of errors found).
CheckExitCode = NewType("CheckExitCode", int)

#: Selective-run scope: ``docs`` | ``skill`` | ``all`` (or empty = all).
CheckOnly = NewType("CheckOnly", str)

__all__ = ["CheckExitCode", "CheckOnly"]

