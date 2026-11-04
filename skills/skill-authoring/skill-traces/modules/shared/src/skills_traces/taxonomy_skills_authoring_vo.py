"""Authoring value objects for the skills feature (AES taxonomy layer).

The trace-pipeline report VOs (``UsageReport``/``PhrasesReport``) that the
scan capability returns and the surface projects to the legacy
``usage.json`` / ``phrases.json`` shapes. Pure data — no I/O and no
imports from utility, capabilities, agent, root, or surface layers.

These VOs compose the primitives (``SkillUsageItem``/``PhraseRow``)
defined in ``taxonomy_skills_vo.py``; the runtime import lands at the
bottom so ``get_type_hints`` resolves the string annotations after both
modules are loaded.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class UsageReport:
    """The skills-only usage material the LLM reads from ``usage.json``.

    One ``SkillUsageItem`` per loaded skill plus the ``unused_loaded``
    verdict the unlearn step filters on.
    """

    kept_sessions: int
    items: tuple[SkillUsageItem, ...] = ()
    unused_loaded: tuple[str, ...] = ()


@dataclass(frozen=True)
class PhrasesReport:
    """Repeated exact prompts, repeated instruction lines, and prompt stems.

    Counts are distinct sessions; single-turn sessions repeated 3+ times
    are excluded as likely automation. The surface projects this to the
    legacy ``phrases.json`` shape.
    """

    exact_prompts: tuple[PhraseRow, ...] = ()
    stems: tuple[PhraseRow, ...] = ()
    repeated_instruction_lines: tuple[PhraseRow, ...] = ()


__all__ = [
    "PhrasesReport",
    "UsageReport",
]

# Runtime import of the two primitives this module's annotations reference
# (``PhraseRow``, ``SkillUsageItem``). Placed at the bottom because
# ``taxonomy_skills_vo`` re-exports this module's class objects — importing
# it back at the top would cycle. The import lands after this module's
# class definitions, so the primitives (and the module's own classes) are
# both loaded by the time ``get_type_hints`` evaluates the string
# annotations above. AES403-safe: imports only ``modules.shared`` types,
# no I/O.
from shared.src.skills_traces.taxonomy_skills_vo import (
    PhraseRow,
    SkillUsageItem,
)
