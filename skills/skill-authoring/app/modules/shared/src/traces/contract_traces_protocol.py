"""Trace-domain contract protocol (AES contract layer, self-contained in ``app``).

One seam for the phrase scan: scan sessions and mine repeated phrases.
Capabilities implement this; the composition root injects it into the
agent. No import of ``skill-traces`` — ``app`` is independent (AES702).
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from shared.src.traces.taxonomy_traces_vo import (
    GrokHome,
    PhrasesReport,
    ScanResult,
    TraceRunDir,
)


class ISkillsTracesProtocol(ABC):
    """Scan sessions and mine repeated phrases."""

    @abstractmethod
    def scan_sessions(
        self,
        grok_home: GrokHome,
        run_dir: TraceRunDir,
        days: int = 0,
        since_last: bool = False,
        min_turns: int = 1,
        limit: int = 0,
    ) -> ScanResult:
        """Walk ``$GROK_HOME/sessions`` and return a compact scan outcome.

        Writes ``manifest.json`` plus ``sessions/*.json`` into *run_dir*.
        """

    @abstractmethod
    def build_phrases(
        self,
        grok_home: GrokHome,
        run_dir: TraceRunDir,
        min_sessions: int = 2,
    ) -> PhrasesReport:
        """Mine repeated exact prompts and repeated instruction lines from session records."""


__all__ = ["ISkillsTracesProtocol"]
