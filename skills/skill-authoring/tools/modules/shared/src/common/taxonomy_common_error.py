"""Skills-domain errors (AES common layer).

Typed replacements for the legacy ``mutate.fail()`` channel: the legacy
helper printed ``ERROR: <message>`` to stderr and raised ``SystemExit``.
A capability must never print and never terminate the process, so every
caller-input failure is a ``SkillsError`` subclass that carries the
legacy message text and the legacy exit code. The surface prints
``ERROR: <message>`` and returns ``exit_code``.

The full hierarchy is moved here because it is consumed by every module
domain (discovery, design, storage, maintenance, governance,
observability); no module may define its own subclass of this hierarchy.
"""

from __future__ import annotations

from shared.src.common.taxonomy_common_vo import ErrorMessage

__all__ = [
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

    def __init__(self, message: ErrorMessage, *, exit_code: int = 2) -> None:
        super().__init__(str(message))
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
