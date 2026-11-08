"""Discovery-domain capability contracts (AES contract layer, ABC traits).

One seam per discovery-side capability: catalog, discover, lister, reader.
Capabilities in ``modules/discovery/src`` implement these; the
composition root injects them into the agent.

Capabilities never import one another: where one needs another's data
(the discoverer reads catalog rows), the dependency is expressed as one
of these protocols and wired by the root.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Sequence

from shared.src.common.taxonomy_common_vo import (
    BM25FHit,
    CatalogCheckResult,
    CatalogReport,
    DiscoveryResult,
    SkillContent,
    SkillRecord,
    SkillsJsonPayload,
)
from shared.src.discovery.taxonomy_discovery_request import (
    DiscoveryQuery,
    DiscoveryRoot,
)


class ISkillsListerProtocol(ABC):
    """Read-only listing of the skill pack."""

    @abstractmethod
    def list_skills(self, root: DiscoveryRoot | None = None) -> Sequence[SkillRecord]:
        """Return one record per skill, sorted by name.

        ``root`` overrides the capability's construction-time pack root
        (explicit beats derived); ``None`` keeps it.
        """
        ...

    def list_skills_json(self, root: DiscoveryRoot | None = None) -> SkillsJsonPayload:
        """Return the global-skill JSON list as a pure-data dict.

        One entry per skill (``name``, ``source``, ``path``, ``loaded``);
        the source is the repo pack only.
        """


class ISkillsReaderProtocol(ABC):
    """Read-only content access to one skill's SKILL.md."""

    @abstractmethod
    def show_skill(
        self, query: DiscoveryQuery, root: DiscoveryRoot | None = None
    ) -> SkillContent | None:
        """Return the raw SKILL.md content for *query*, or None if missing."""
        ...


class ISkillsCatalogProtocol(ABC):
    """Render, rebuild, check, and read the tracked ``catalog.json``."""

    @abstractmethod
    def rebuild(self, root: DiscoveryRoot) -> CatalogReport:
        """Walk the tree and rewrite the catalog; return the rendered counts."""
        ...

    @abstractmethod
    def check(self, root: DiscoveryRoot) -> CatalogCheckResult:
        """Return ``in_sync`` plus the diff lines and summary message.

        On sync: ``in_sync=True``, no diff lines. On drift/missing/
        unparseable/non-round-trip: ``in_sync=False`` with the unified
        diff (or per-cell problems) and a summary message. The agent maps
        ``in_sync=False`` to exit code 3; the surface renders message +
        diff lines to stdout and emits ``{skills_root, in_sync, catalog,
        diff}`` in JSON mode, byte-identical to the legacy command.
        """
        ...

    @abstractmethod
    def read(self, root: DiscoveryRoot) -> SkillContent:
        """Return the raw tracked ``catalog.json`` text, or ``""`` if missing.

        A read-only view for the CLI ``catalog --read`` path; never parses,
        drift-checks, or raises — it just hands the bytes back (empty
        string when the file is absent, so the caller decides how to report
        it).
        """
        ...


class ISkillsDiscoverProtocol(ABC):
    """Query the catalog, with a loud fallback when it drifts."""

    @abstractmethod
    def discover(
        self, query: DiscoveryQuery, root: DiscoveryRoot, limit: int
    ) -> DiscoveryResult:
        """Search the catalog rows for *query*, returning top *limit* matches.

        Raises ``SkillsUsageError('Query is empty')`` when the query has no
        search tokens (exit 2). On drift (a missing or corrupt
        ``catalog.json``), sets the result's warning fields, falls back to the
        live tree scan, and returns matches with exit 0.
        """
        ...

    @abstractmethod
    def rank(self, rows: object, tokens: list[str]) -> list[BM25FHit]:
        """Return ranked hits for *rows* scored against *tokens*.

        Each hit carries a float ``score``, the original row, and the
        logical field names that contributed (``matched_fields``).
        Empty *rows* or *tokens* yield an empty list.
        """
        ...


__all__ = [
    "ISkillsCatalogProtocol",
    "ISkillsDiscoverProtocol",
    "ISkillsListerProtocol",
    "ISkillsReaderProtocol",
]

_layer_symbols = {
    "ISkillsCatalogProtocol": ISkillsCatalogProtocol,
    "ISkillsDiscoverProtocol": ISkillsDiscoverProtocol,
    "ISkillsListerProtocol": ISkillsListerProtocol,
    "ISkillsReaderProtocol": ISkillsReaderProtocol,
}
