"""Skills-domain errors (AES taxonomy layer).

Typed replacements for the legacy ``mutate.fail()`` channel: the legacy
helper printed ``ERROR: <message>`` to stderr and raised ``SystemExit``.
A capability must never print and never terminate the process, so every
caller-input failure is a ``SkillsError`` subclass that carries the
legacy message text and the legacy exit code. The surface prints
``ERROR: <message>`` and returns ``exit_code``.
"""

from __future__ import annotations

from collections.abc import Sequence

__all__ = [
    "CatalogDrift",
    "CategoryNameError",
    "MutationConflictError",
    "SkillNotFoundError",
    "SkillsError",
    "SkillsRootError",
    "SkillsUsageError",
]


class SkillsError(Exception):
    """Base for skill-domain failures.

    ``exit_code`` defaults to 2 (usage / bad input), matching the legacy
    ``mutate.fail`` -> ``SystemExit(1)`` -> remap-to-2 contract
    (``cli.py::main``); the surface never re-derives it.
    """

    exit_code: int = 2

    def __init__(self, message: str, *, exit_code: int = 2) -> None:
        super().__init__(message)
        self.exit_code = exit_code


class SkillsUsageError(SkillsError):
    """Caller input is wrong: unknown skill, bad category name, missing query."""


class SkillNotFoundError(SkillsUsageError):
    """No skill directory with a ``SKILL.md`` matched the reference."""


class CategoryNameError(SkillsUsageError):
    """The caller-supplied category name violates the naming rules."""


class MutationConflictError(SkillsUsageError):
    """A mutation would overwrite an existing destination."""


class SkillsRootError(SkillsUsageError):
    """The skills root is missing or is not a directory."""


class CatalogDrift(SkillsUsageError):
    """Tracked ``CATALOG.md`` is missing, stale, corrupt, or non-round-tripping.

    Carries the summary message and optional diff lines; explicitly
    carries ``exit_code = 3`` — the CI drift signal. Raised by
    ``ISkillsCatalogProtocol.load_rows`` when loading catalog rows fails
    closed. Under ``discover``, this error is caught and converted to a
    loud warning with live-tree fallback. Under ``catalog --check``, the
    catalog capability's ``check`` method *returns*
    ``CatalogCheckResult(in_sync=False, ...)`` so diff lines, summary, and
    JSON shape are fully preserved for the surface (which maps
    ``in_sync=False`` to exit code 3).
    """

    exit_code: int = 3

    def __init__(self, message: str, diff_lines: Sequence[str] = ()) -> None:
        super().__init__(message, exit_code=3)
        self.diff_lines: tuple[str, ...] = tuple(diff_lines)
