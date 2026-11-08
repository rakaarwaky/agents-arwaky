"""Discovery request value objects (AES taxonomy layer, request side).

The typed envelope the surface and agent exchange: ``DiscoveryRequest``
carries the verb, the skill name or search query, and the pack-root
override. ``DiscoveryVerb`` names every operation the discovery
aggregate understands.

No I/O, no imports from utility/capabilities/agent/root/surface layers.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import NewType

DiscoveryQuery = NewType("DiscoveryQuery", str)
"""A skill name / identifier to look up in the pack."""

DiscoveryRoot = NewType("DiscoveryRoot", Path)
"""An explicit discovery root; ``None`` on a request means 'use the default'."""


class DiscoveryVerb(Enum):
    """Consumer verbs carried by the discovery aggregate's single entry point."""

    LIST = "list"
    LIST_ARCHIVED = "list-archived"
    LIST_UNMANAGED = "list-unmanaged"
    READ = "read"
    CATALOG = "catalog"
    DISCOVER = "discover"


@dataclass(frozen=True)
class DiscoveryRequest:
    """The aggregate entry point's single argument (AES401)."""

    verb: DiscoveryVerb
    query: DiscoveryQuery = field(default_factory=lambda: DiscoveryQuery(""))
    root: DiscoveryRoot | None = None
    flags: Mapping[str, str] = field(default_factory=dict)


__all__ = [
    "DiscoveryQuery",
    "DiscoveryRequest",
    "DiscoveryRoot",
    "DiscoveryVerb",
]
