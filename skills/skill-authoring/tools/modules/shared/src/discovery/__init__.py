"""Skills-design shared kernel — discovery layer.

Stateless discovery helpers: tree walking, frontmatter parsing, markdown
string mechanics, cross-process locking, and the discovery loaders that
turn a skills root into skill records and BM25F hits.
"""
from shared.src.discovery.contract_discovery_protocol import (
    ISkillsCatalogProtocol,
    ISkillsDiscoverProtocol,
    ISkillsListerProtocol,
    ISkillsReaderProtocol,
)
from shared.src.discovery.taxonomy_discovery_request import (
    DiscoveryQuery,
    DiscoveryRequest,
    DiscoveryRoot,
    DiscoveryVerb,
)
from shared.src.discovery.taxonomy_discovery_response import DiscoveryResponse
from shared.src.discovery.utility_discovery_core import (
    category_dirs,
    category_summaries,
    clean_one_line,
    cross_process_lock,
    parse_frontmatter,
    relpath,
    skill_entries,
)

__all__ = [
    "DiscoveryQuery",
    "DiscoveryRequest",
    "DiscoveryResponse",
    "DiscoveryRoot",
    "DiscoveryVerb",
    "ISkillsCatalogProtocol",
    "ISkillsDiscoverProtocol",
    "ISkillsListerProtocol",
    "ISkillsReaderProtocol",
    "category_dirs",
    "category_summaries",
    "clean_one_line",
    "cross_process_lock",
    "parse_frontmatter",
    "relpath",
    "skill_entries",
]

_layer_symbols = {
    "ISkillsCatalogProtocol": ISkillsCatalogProtocol,
    "ISkillsDiscoverProtocol": ISkillsDiscoverProtocol,
    "ISkillsListerProtocol": ISkillsListerProtocol,
    "ISkillsReaderProtocol": ISkillsReaderProtocol,
}
