"""Skills taxonomy value objects (AES taxonomy layer).

Pure data + helpers for the skills feature: the read-side VOs
(``SkillRecord``/...) and the re-exported rule SSOT (defined in
``taxonomy_skills_rule_vo.py`` so the rule table's dependencies stay
acyclic). The request envelope
(``SkillsRequest``/``SkillsOp``/``SkillQuery``/``SkillsRoot``) lives in
``taxonomy_skills_request.py`` and the response envelope
(``SkillsResult``/``SkillsExitCode``) lives in
``taxonomy_skills_response.py``; both are re-exported here so existing
imports keep working.

No I/O, no imports from utility/capabilities/agent/root/surface layers.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import NewType

# Every other primitive below (``SkillContent``, ``SkillRecord``, ...) is
# defined here and re-exported back into the request/response
# envelope modules after its definition, so the envelope modules never
# import this module at runtime — no cycle in either import order.
SkillContent = NewType("SkillContent", str)
"""Raw SKILL.md text returned by a read."""

SkillDescription = NewType("SkillDescription", str)
"""One-line description extracted from SKILL.md frontmatter."""

ErrorMessage = NewType("ErrorMessage", str)
"""A formatted error message for skill-domain exceptions."""

SkillsJsonPayload = NewType("SkillsJsonPayload", Mapping[str, object])
"""The pure-data JSON list of global skills (``SkillsLister.list_skills_json``).

One entry per skill (``name``, ``source``, ``path``, ``loaded``); the
source is the repo pack only. A pure-data dict, so it never touches I/O.
"""

@dataclass(frozen=True)
class SkillRecord:
    """One discoverable skill in the pack."""

    name: str
    description: SkillDescription
    path: Path


# Re-exported into the legacy import path: the request/response envelope
# modules import *only* the primitives defined above (``SkillRecord``,
# ...) — no import of this module at runtime, so no cycle
# in either direction. Downstream consumers should import
# ``SkillsOp``/``SkillsRequest`` from ``taxonomy_skills_request`` and
# ``SkillsExitCode``/``SkillsResult`` from ``taxonomy_skills_response``
# directly instead of through this module.

__all__ = [
    "ErrorMessage",
    "SkillContent",
    "SkillDescription",
    "SkillRecord",
    "SkillsJsonPayload",
]
