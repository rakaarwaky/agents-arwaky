"""Harness-domain constants — registry tables (taxonomy layer, AES201 rule 8).

Pure data shared with the agent layer. The connect/disconnect callables are
attached by the per-harness capability modules' register() functions, invoked
from :mod:`modules.harness.src.root_harness_container` (root layer).
"""
from __future__ import annotations

#: harness_id -> {"aliases": [...], "connect": callable, "disconnect": callable}.
HARNESSES: dict[str, dict] = {
    "antigravity": {"aliases": ["antigravity"], "connect": None, "disconnect": None},
    "hermes": {"aliases": ["hermes"], "connect": None, "disconnect": None},
    "opencode": {"aliases": ["opencode"], "connect": None, "disconnect": None},
    "qwencode": {"aliases": ["qwencode"], "connect": None, "disconnect": None},
    "grok-build": {"aliases": ["grok", "grok-build"], "connect": None, "disconnect": None},
}
ALIASES: dict[str, str] = {}
for _harness_id, _entry in HARNESSES.items():
    for _alias in _entry["aliases"]:
        ALIASES[_alias] = _harness_id
ALL_HARNESS_IDS = tuple(HARNESSES.keys())
