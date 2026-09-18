"""Document-invariant VOs — shared taxonomy layer.

Frozen dataclasses describing a doc finding, a parsed markdown section, and a
parsed markdown table. These are pure data types with no behaviour beyond
property helpers, so they belong in the taxonomy layer (AES404: utility files
must be stateless).
"""
from __future__ import annotations

from dataclasses import dataclass

from modules.shared.src.taxonomy_doc_constant import ERROR


@dataclass(frozen=True)
class DocFinding:
    """One violated document invariant, ready for CLI reporting."""

    code: str
    message: str
    path: str = ""
    severity: str = ERROR

    @property
    def is_error(self) -> bool:
        """Whether the finding must be fixed before the documents can be trusted."""
        return self.severity == ERROR


@dataclass(frozen=True)
class Section:
    """A markdown heading and the raw lines under it, up to the next heading."""

    level: int
    title: str
    body: str
    line: int


@dataclass(frozen=True)
class Table:
    """A parsed markdown table: header cells, ``(line, cells)`` rows, header line."""

    header: list[str]
    rows: list[tuple[int, list[str]]]
    line: int
