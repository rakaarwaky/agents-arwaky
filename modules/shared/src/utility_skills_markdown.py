"""Markdown text mechanics for the skills feature (AES utility layer).

Stateless escape/clean helpers lifted verbatim from the skill-authoring
SSOT. They are technical string mechanics with no domain decisions, so
they live in Utility rather than Taxonomy; the catalog renderer, the
discoverer, and the surface all share them.
"""

from __future__ import annotations

import json

__all__ = ["clean_one_line", "md_escape", "md_unescape", "yaml_quote"]


def clean_one_line(value: object) -> str:
    """Collapse whitespace to single spaces and strip the edges."""
    return " ".join(str(value).split()).strip()


def md_escape(value: object) -> str:
    """Escape a value for Markdown table cells (pipes, newlines)."""
    return str(value).replace("|", "&#124;").replace("\n", " ").strip()


def md_unescape(value: object) -> str:
    """Inverse of ``md_escape``'s pipe escaping (the ``&#124;`` literal lives here only)."""
    return str(value).replace("&#124;", "|")


def yaml_quote(value: object) -> str:
    """Quote a YAML scalar the way the original ``librarian.py`` did."""
    return json.dumps(str(value), ensure_ascii=False)
