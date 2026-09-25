"""Harness-domain constants — alias table + supported set (taxonomy layer).

Pure data: the alias table maps raw CLI tokens (ids / aliases) onto canonical
harness ids. Unknown tokens are surfaced to the CLI, never raised here.
"""
from __future__ import annotations

#: canonical harness id -> raw CLI tokens that resolve to it (id itself + aliases).
HARNESSES: dict[str, tuple[str, ...]] = {
    "hermes": ("hermes",),
    "opencode": ("opencode",),
    "grok-build": ("grok-build", "grok"),
}

ALIASES: dict[str, str] = {}
for _harness_id, _tokens in HARNESSES.items():
    for _token in _tokens:
        ALIASES[_token] = _harness_id

ALL_HARNESS_IDS: tuple[str, ...] = tuple(HARNESSES)
