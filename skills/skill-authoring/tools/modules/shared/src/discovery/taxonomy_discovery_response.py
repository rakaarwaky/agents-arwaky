"""Discovery response value objects (AES taxonomy layer, response side).

The typed response envelope: ``DiscoveryResponse`` is what the surface
renders after one discovery aggregate op (payload fields are populated
per verb, never re-read from a capability).

The authoring VO fields (``SkillRecord``, ``SkillContent``,
``CatalogReport``, ``DiscoveryResult``) are imported under
``TYPE_CHECKING`` only — they live in the design domain's taxonomy VO
module, and PEP 563 keeps the annotations as strings so there is no
runtime cross-domain import from discovery's taxonomy layer.

No I/O, no imports from utility/capabilities/agent/root/surface layers.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

from shared.src.discovery.taxonomy_discovery_request import DiscoveryVerb

if TYPE_CHECKING:
    # Discovery payloads carry common-layer VO types at type-check time.
    # PEP 563 keeps annotations as strings, so the runtime import stays
    # one-directional: discovery taxonomy imports only its own request
    # module (which imports nothing from common/design).
    from shared.src.common.taxonomy_common_vo import (
        CatalogCheckResult,
        CatalogReport,
        DiscoveryResult,
        SkillContent,
        SkillRecord,
    )


@dataclass(frozen=True)
class DiscoveryResponse:
    """Response to a discovery aggregate request.

    ``ok``/``verb``/``exit_code``/``message`` form the command contract.
    Payload fields are populated per verb: ``records`` for LIST,
    ``content`` for READ, ``catalog_report`` for CATALOG,
    ``discovery`` for DISCOVER. An unserved verb leaves its field empty
    rather than raising.
    """

    ok: bool
    verb: DiscoveryVerb
    exit_code: int = 0
    message: str = ""
    records: tuple[SkillRecord, ...] = ()
    content: SkillContent | None = None
    catalog_report: CatalogReport | None = None
    catalog_check: CatalogCheckResult | None = None
    discovery: DiscoveryResult | None = None
    warning: str | None = None
    root: Path | None = None


__all__ = ["DiscoveryResponse"]
