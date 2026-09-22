"""Check-domain value objects for the unified check feature.

`CheckExitCode` wraps a raw `int` so contract signatures (`ICheckAggregate`,
`ICheckRunner`) can return the gate result without exposing a primitive
(AES402). Identity at runtime — a bare integer.
"""
from __future__ import annotations

from typing import NewType

#: Gate exit code: 0 = pass, non-zero = fail (count of errors found).
CheckExitCode = NewType("CheckExitCode", int)

__all__ = ["CheckExitCode"]
