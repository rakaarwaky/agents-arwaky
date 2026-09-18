"""Document invariant checks (moved verbatim from tools/lib/doc_pack.py)."""
from __future__ import annotations

from modules.shared.src.common.doc_pack.capabilities_doc_pack import (
    DocFinding,
    Table,
    as_strict,
    audit_docs,
    blank_fenced,
    errors_only,
    find_section,
    iter_doc_files,
    md_links,
    parse_tables,
    sections,
    warnings_only,
)

__all__ = [
    "DocFinding",
    "Table",
    "as_strict",
    "audit_docs",
    "blank_fenced",
    "errors_only",
    "find_section",
    "iter_doc_files",
    "md_links",
    "parse_tables",
    "sections",
    "warnings_only",
]
