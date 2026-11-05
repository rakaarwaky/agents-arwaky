"""BM25F ranker contract (AES contract layer, ABC trait).

Seam for the offline BM25F field-weighted ranker used by the
discover capability: one abstract method that scores catalog rows
against query tokens and returns ranked hits with the logical field
names that contributed to each score.

``BM25FHit`` is the typed hit returned by ``rank``; the concrete
dataclass lives in ``capabilities_skills_bm25f`` (the capability
that implements this protocol). Callers use the string type hint
``"BM25FHit"`` — no runtime import cycle.
"""

from __future__ import annotations

from abc import ABC, abstractmethod


class IBM25FRankerProtocol(ABC):
    """Scores rows against query tokens; pure data in, ranked hits out."""

    @abstractmethod
    def rank(self, rows: object, tokens: list[str]) -> list["BM25FHit"]:
        """Return ranked hits for *rows* scored against *tokens*.

        Each hit carries a float ``score``, the original row, and the
        logical field names that contributed (``matched_fields``).
        Empty *rows* or *tokens* yield an empty list.
        """
        ...


__all__ = ["IBM25FRankerProtocol"]
