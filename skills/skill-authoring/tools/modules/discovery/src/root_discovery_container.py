"""Discovery composition root — wires four capabilities into the orchestrator.

The AES root layer is the only layer allowed to construct capabilities.
This module builds the four discovery capabilities (catalog, discover,
lister, reader), injects them into ``SkillsDiscoveryAgent``, and exposes
the ``ISkillsDiscoveryAggregate`` contract to the surface and entry layers.

Wiring only: no business logic, no orchestration policy, no technical
parsing, no UI behaviour — those live in capabilities / agent / surface.

Drift contract (carried over from the discover capability): if the catalog
is missing, corrupt, or empty, discovery falls back to a read-only tree
scan and sets the warning fields; the drift gate lives in ``catalog --check``.
"""

from __future__ import annotations

from pathlib import Path

from agent_discovery_orchestrator import SkillsDiscoveryAgent
from capabilities_discovery_catalog import SkillsCatalog
from capabilities_discovery_finder import SkillsDiscover
from capabilities_discovery_lister import SkillsLister
from capabilities_discovery_reader import SkillsPackReader
from shared.src.discovery.contract_discovery_aggregate import (
    ISkillsDiscoveryAggregate,
)
from shared.src.discovery.contract_discovery_protocol import (
    ISkillsCatalogProtocol,
    ISkillsDiscoverProtocol,
    ISkillsListerProtocol,
    ISkillsReaderProtocol,
)
from shared.src.discovery.taxonomy_discovery_vo import SkillsBm25fRanker
from shared.src.storage.utility_skill_pack import default_pack_root

__all__ = [
    "DiscoveryContainer",
    "create_discovery_feature",
]


class DiscoveryContainer:
    """Construct the four capabilities and the discovery orchestrator (wiring only)."""

    def __init__(
        self,
        lister: ISkillsListerProtocol | None = None,
        reader: ISkillsReaderProtocol | None = None,
        catalog: ISkillsCatalogProtocol | None = None,
        discover: ISkillsDiscoverProtocol | None = None,
        default_root: Path | None = None,
    ) -> None:
        root = default_root if default_root is not None else default_pack_root()
        self._catalog = catalog or SkillsCatalog()
        self._discover = discover or SkillsDiscover(self._catalog, SkillsBm25fRanker())
        self._lister = lister or SkillsLister(pack_root=root)
        self._reader = reader or SkillsPackReader(pack_root=root)
        self._orchestrator = SkillsDiscoveryAgent(
            catalog=self._catalog,
            discover=self._discover,
            lister=self._lister,
            reader=self._reader,
            default_root=root,
        )

    @property
    def aggregate(self) -> ISkillsDiscoveryAggregate:
        """Expose the discovery aggregate contract, never a concrete orchestrator."""
        return self._orchestrator


def create_discovery_feature(
    root: Path | None = None,
    *,
    lister: ISkillsListerProtocol | None = None,
    reader: ISkillsReaderProtocol | None = None,
    catalog: ISkillsCatalogProtocol | None = None,
    discover: ISkillsDiscoverProtocol | None = None,
) -> ISkillsDiscoveryAggregate:
    """Fully-wired discovery feature aggregate (factory for entry / DI).

    ``root`` overrides the default pack root; individual capability overrides
    are for DI / test injection.
    """
    return DiscoveryContainer(
        lister=lister,
        reader=reader,
        catalog=catalog,
        discover=discover,
        default_root=root,
    ).aggregate
