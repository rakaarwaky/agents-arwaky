"""Root composition — harness connector registry (P4-A21 self-registration).

The AES root layer is the only layer allowed to import `capabilities*`;
this module owns the per-harness registration wiring so that
`agent_harness_orchestrator` stays capability-free (AES201 rule 8).
"""
from __future__ import annotations

from modules.harness.src.capabilities_harness_antigravity import register as _register_antigravity
from modules.harness.src.capabilities_harness_grok_build import register as _register_grok_build
from modules.harness.src.capabilities_hermes import register as _register_hermes
from modules.harness.src.capabilities_harness_opencode import register as _register_opencode
from modules.harness.src.capabilities_harness_qwencode import register as _register_qwencode

#: harness_id -> connector entry dict (registered at import time).
HARNESSES: dict[str, dict] = {}
ALIASES: dict[str, str] = {}
for _mod in (_register_antigravity, _register_hermes, _register_opencode, _register_qwencode, _register_grok_build):
    _entry = _mod()
    HARNESSES[_entry["id"]] = _entry
    for _alias in _entry["aliases"]:
        ALIASES[_alias] = _entry["id"]
ALL_HARNESS_IDS = tuple(HARNESSES.keys())
