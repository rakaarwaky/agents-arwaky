"""Markdown text mechanics for the skills feature (AES utility layer).

Stateless escape/clean helpers lifted verbatim from the skill-authoring
SSOT. They are technical string mechanics with no domain decisions, so
they live in Utility rather than Taxonomy; the catalog renderer, the
discoverer, and the surface all share them.
"""

from __future__ import annotations

__all__ = ["clean_one_line"]


def clean_one_line(value: object) -> str:
    """Collapse whitespace to single spaces and strip the edges."""
    return " ".join(str(value).split()).strip()

