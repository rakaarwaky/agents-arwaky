"""Trace value objects (AES taxonomy layer, self-contained in ``app``).

Pure data for the phrases pipeline: ``PhraseRow``, ``PhrasesReport``,
``TraceSessionRecord``, and ``ScanResult``. No imports from utility,
capabilities, agent, root, or surface layers.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from collections.abc import Mapping
from typing import NewType

#: The ``$GROK_HOME`` directory the phrase pipeline reads session traces from.
GrokHome = NewType("GrokHome", str)
#: The run directory one trace scan writes into (``report.md``, ``sessions/``).
TraceRunDir = NewType("TraceRunDir", str)


@dataclass(frozen=True)
class PhraseRow:
    """One repeated-phrase row: the normalized text, distinct-session count, occurrences."""

    phrase: str
    sessions: int
    occurrences: int
    session_ids: tuple[str, ...] = ()


@dataclass(frozen=True)
class PhrasesReport:
    """Repeated exact prompts, repeated instruction lines, and prompt stems.

    Counts are distinct sessions. Surface projects this to a terminal listing
    (and optionally JSON).
    """

    exact_prompts: tuple[PhraseRow, ...] = ()
    stems: tuple[PhraseRow, ...] = ()
    repeated_instruction_lines: tuple[PhraseRow, ...] = ()


@dataclass(frozen=True)
class TraceSessionRecord:
    """One compact per-session record the tracker writes to the run dir.

    The fields are the phrase-mining raw material (turns, sessions).
    """

    id: str
    index: int
    cwd: str
    updated_at: str = ""
    turns: tuple[str, ...] = ()
    slash_commands: Mapping[str, int] = field(default_factory=dict)
    skills_loaded: Mapping[str, int] = field(default_factory=dict)
    trace_path: str = ""


@dataclass(frozen=True)
class ScanResult:
    """Outcome of one tracker scan: the kept records plus scan counters."""

    records: tuple[TraceSessionRecord, ...]
    sessions_seen: int
    dropped: Mapping[str, int] = field(default_factory=dict)


__all__ = [
    "GrokHome",
    "PhraseRow",
    "PhrasesReport",
    "ScanResult",
    "TraceRunDir",
    "TraceSessionRecord",
]
