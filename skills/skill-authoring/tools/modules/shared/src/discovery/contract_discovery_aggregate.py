"""Discovery-domain aggregate contract (AES contract layer, ABC trait).

Single entry point over the discovery-side capabilities:
catalog, discover, lister, reader.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from shared.src.discovery.contract_discovery_protocol import (
    ISkillsCatalogProtocol,
    ISkillsDiscoverProtocol,
    ISkillsListerProtocol,
    ISkillsReaderProtocol,
)
from shared.src.discovery.taxonomy_discovery_request import DiscoveryRequest
from shared.src.discovery.taxonomy_discovery_response import DiscoveryResponse

__all__ = [
    "ISkillsCatalogProtocol",
    "ISkillsDiscoverProtocol",
    "ISkillsDiscoveryAggregate",
    "ISkillsListerProtocol",
    "ISkillsReaderProtocol",
]

class ISkillsDiscoveryAggregate(ABC):
    """Single entry point over discovery-side ops; the agent dispatches internally."""

    @abstractmethod
    def execute(self, request: DiscoveryRequest) -> DiscoveryResponse:
        """Run the request the surface/root/CLI asked for; return the response."""
        ...
