"""Tool runner registry — superseded by the two business-action capabilities.

The runner no longer registers per-tool runner classes: discovery follows one
universal order (XDG bin launcher -> host PATH -> per-tool install dir) and
launch is a plain subprocess exec, so there is no per-tool mechanic family.
This module is retained only to keep external import paths stable and to
document that the per-tool registry was removed.
"""
from __future__ import annotations

__all__ = []
