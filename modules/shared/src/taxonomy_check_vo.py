"""Check-domain value objects for the unified check feature.

`CheckExitCode` wraps a raw `int` so contract signatures (`ICheckAggregate`,
`ICheckProtocol`) can return the gate result without exposing a primitive
(AES402). `CheckScope` names the gate scope a request asks for (`docs` |
`skill` | `all`); `CheckOnly` is the CLI-scope alias resolved through
`CHECK_SCOPES`. `CheckRequest`/`CheckResponse` are the aggregate's
envelope pair — the consumer verb is a value of `CheckRequest.scope`.
Identity at runtime — bare primitives.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import NewType

#: Gate exit code: 0 = pass, non-zero = fail (count of errors found).
CheckExitCode = NewType("CheckExitCode", int)

#: Selective-run scope: ``docs`` | ``skill`` | ``all`` (or empty = all).
CheckOnly = NewType("CheckOnly", str)

#: Requested gate scope token (``all`` | ``docs`` | ``skill``).
CheckScope = NewType("CheckScope", str)

#: One-line digest summarizing a set of findings.
CheckSummary = NewType("CheckSummary", str)


@dataclass(frozen=True)
class CheckRequest:
    """One check request the surface/root/CLI hands to the aggregate.

    ``scope`` carries the gate scope the consumer asked for; the agent
    resolves it against the registered runners and dispatches to the
    matching protocol method, so the aggregate keeps a single ``execute``
    entry point.
    """

    scope: CheckScope = CheckScope("")


@dataclass(frozen=True)
class CheckResponse:
    """Response envelope returned by ``ICheckAggregate.execute``."""

    exit_code: CheckExitCode
    summary: CheckSummary


#: CLI scope aliases → runner ``name`` (surface + orchestrator share this map).
CHECK_SCOPES: dict[str, str] = {
    "all": "",
    "docs": "docs",
    "doc": "docs",
    "skill": "skill",
    "skills": "skill",
}

__all__ = [
    "CHECK_SCOPES",
    "CheckExitCode",
    "CheckOnly",
    "CheckRequest",
    "CheckResponse",
    "CheckScope",
    "CheckSummary",
]
