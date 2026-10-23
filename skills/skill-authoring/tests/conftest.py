"""Pytest path setup for the skill-authoring pack tests.

Adds ``scripts/`` and ``_rules/`` (both siblings of this directory) to
``sys.path`` so tests can ``import model, validate, skill_rules`` the
same way the path-invocable entrypoints do — no packaging involved.
"""

import sys
from pathlib import Path

PACK_ROOT = Path(__file__).resolve().parent.parent
for _entry in (PACK_ROOT / "scripts", PACK_ROOT / "_rules"):
    if str(_entry) not in sys.path:
        sys.path.insert(0, str(_entry))
