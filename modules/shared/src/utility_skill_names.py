"""Skill-name helpers (utility layer) — re-export of the taxonomy vo module.

Implementation lives in :mod:`modules.shared.src.taxonomy_skill_vo`
(pure skill-name functions; AES201 rule 4 forbids utility->utility imports,
so the real code sits in the taxonomy layer).
"""
from __future__ import annotations

import importlib

_mod = importlib.import_module("modules.shared.src.taxonomy_skill_vo")
globals().update({n: getattr(_mod, n) for n in dir(_mod) if not n.startswith("__")})

__all__ = [n for n in dir(_mod) if not n.startswith("_")]
