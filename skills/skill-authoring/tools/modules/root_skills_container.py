"""Skills-design root container (AES composition root).

Wires the six module-side agents (design, discovery, storage, governance,
maintenance, observability) into a single composed aggregate.

The traces capability of the sibling traces app is NOT imported
here — the two packages are independent (AES702). The composed agent
routes each ``SkillsOp`` to its owning module agent; the CLI surface
receives one ``ISkillsAggregate`` (the composed facade), injected at
the call site, so no root→surface coupling exists.

Discovery ops are translated at the boundary: ``SkillsRequest`` →
``DiscoveryRequest`` on the way in, ``DiscoveryResponse`` →
``SkillsResult`` on the way out.
"""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path

from design.src.agent_design_orchestrator import SkillsDesignAgent
from design.src.capabilities_skills_adopter import SkillsAdopter
from design.src.capabilities_skills_runner import SkillsRunner
from discovery.agent_discovery_orchestrator import SkillsDiscoveryAgent
from governance.agent_governance_orchestrator import SkillsGovernanceAgent
from governance.capabilities_skills_locker import SkillsLocker
from governance.capabilities_skills_piner import SkillsPiner
from maintenance.agent_maintenance_orchestrator import SkillsMaintenanceAgent
from maintenance.capabilities_skills_prune import SkillsPrune
from maintenance.capabilities_skills_purge import SkillsPurge
from observability.agent_observability_orchestrator import SkillsObservabilityAgent
from observability.capabilities_skills_ledger import SkillsLedger
from observability.capabilities_skills_telemetry import SkillsTelemetry
from observability.src.agent_skills_phrase_orchestrator import SkillsPhraseAgent
from shared.src.common.taxonomy_common_vo import (
    SkillRecord,
)
from shared.src.design.contract_skills_aggregate import ISkillsAggregate
from shared.src.design.contract_skills_protocol import (
    ISkillsArchiverProtocol,
    ISkillsCatalogProtocol,
    ISkillsCreatorProtocol,
    ISkillsDiscoverProtocol,
    ISkillsLinterProtocol,
    ISkillsListerProtocol,
    ISkillsMoverProtocol,
    ISkillsReaderProtocol,
)
from shared.src.design.taxonomy_skills_request import (
    SkillQuery,
    SkillsOp,
    SkillsRequest,
)
from shared.src.design.taxonomy_skills_response import SkillsResult
from shared.src.discovery.taxonomy_discovery_request import (
    DiscoveryQuery,
    DiscoveryRequest,
    DiscoveryRoot,
    DiscoveryVerb,
)
from shared.src.discovery.taxonomy_discovery_response import DiscoveryResponse
from shared.src.storage.utility_skill_pack import default_pack_root
from storage.agent_storage_orchestrator import SkillsStorageAgent
from storage.capabilities_skills_backup import SkillsBackup
from storage.capabilities_skills_restore import SkillsRestore
from storage.capabilities_skills_rollback import SkillsRollback

__all__ = [
    "SkillsFacade",
    "default_aggregate",
]


def default_aggregate(
    lister: ISkillsListerProtocol | None = None,
    reader: ISkillsReaderProtocol | None = None,
    *,
    linter: ISkillsLinterProtocol | None = None,
    catalog: ISkillsCatalogProtocol | None = None,
    discover: ISkillsDiscoverProtocol | None = None,
    mover: ISkillsMoverProtocol | None = None,
    archiver: ISkillsArchiverProtocol | None = None,
    creator: ISkillsCreatorProtocol | None = None,
    backup: SkillsBackup | None = None,
    restore: SkillsRestore | None = None,
    rollback: SkillsRollback | None = None,
    default_root: Path | None = None,
) -> ISkillsAggregate:
    """Return a composed agent bound to the repo's ``skills/`` pack."""
    root = default_root if default_root is not None else default_pack_root()

    design = SkillsDesignAgent(
        creator=creator,
        adopter=SkillsAdopter(),
        linter=linter,
        runner=SkillsRunner(),
        default_root=root,
    )
    _catalog = catalog if catalog is not None else SkillsCatalog()
    _discover = discover if discover is not None else SkillsDiscover(
        _catalog, SkillsBm25fRanker()
    )
    _lister = lister if lister is not None else SkillsLister()
    _reader = reader if reader is not None else SkillsPackReader()
    discovery = SkillsDiscoveryAgent(
        catalog=_catalog,
        discover=_discover,
        lister=_lister,
        reader=_reader,
        default_root=root,
    )
    governance = SkillsGovernanceAgent(
        locker=SkillsLocker(),
        piner=SkillsPiner(),
        mover=mover,
        default_root=root,
    )
    maintenance = SkillsMaintenanceAgent(
        prune=SkillsPrune(),
        purge=SkillsPurge(),
        default_root=root,
    )
    observability = SkillsObservabilityAgent(
        ledger=SkillsLedger(),
        telemetry=SkillsTelemetry(),
        default_root=root,
    )
    storage = SkillsStorageAgent(
        archiver=archiver,
        backup=backup or SkillsBackup(),
        restore=restore,
        rollback=rollback or SkillsRollback(backup or SkillsBackup()),
        default_root=root,
    )
    traces = SkillsPhraseAgent(default_root=root)

    return _ComposedAggregate(
        design=design,
        discovery=discovery,
        governance=governance,
        maintenance=maintenance,
        observability=observability,
        storage=storage,
        traces=traces,
    )


class _ComposedAggregate(ISkillsAggregate):
    def __init__(
        self,
        design,
        discovery,
        governance,
        maintenance,
        observability,
        storage,
        traces,
    ) -> None:
        self._design = design
        self._discovery = discovery
        self._governance = governance
        self._maintenance = maintenance
        self._observability = observability
        self._storage = storage
        self._traces = traces

    def execute(self, request: SkillsRequest) -> SkillsResult:
        op = request.op
        if op in _DESIGN_OPS:
            result = self._design.execute(request)
        elif op in _DISCOVERY_OPS:
            dreq = DiscoveryRequest(
                verb=DiscoveryVerb(op.value),
                query=DiscoveryQuery(request.query),
                root=DiscoveryRoot(request.root) if request.root is not None else None,
                flags=request.flags,
            )
            dresp = self._discovery.execute(dreq)
            result = _discovery_response_to_result(dresp, op)
        elif op in _GOVERNANCE_OPS:
            result = self._governance.execute(request)
        elif op in _MAINTENANCE_OPS:
            result = self._maintenance.execute(request)
        elif op in _OBSERVABILITY_OPS:
            result = self._observability.execute(request)
        elif op in _STORAGE_OPS:
            result = self._storage.execute(request)
        elif op in _TRACES_OPS:
            result = self._traces.execute(request)
        else:
            return SkillsResult(
                ok=False,
                op=op,
                exit_code=2,
                message=f"Unknown skills op: {op}",
            )
        if result.ok:
            skill_name = str(request.query or "").strip()
            if skill_name:
                self._observability.record_view(skill_name)
        return result


def _discovery_response_to_result(
    dresp: DiscoveryResponse, op: SkillsOp
) -> SkillsResult:
    """Translate a discovery response back into a SkillsResult for the surface."""
    payload: dict[str, object] = {}
    if dresp.records:
        payload["records"] = dresp.records
    if dresp.content is not None:
        payload["content"] = dresp.content
    if dresp.catalog_report is not None:
        payload["catalog"] = dresp.catalog_report
    if dresp.catalog_check is not None:
        payload["check"] = dresp.catalog_check
    if dresp.discovery is not None:
        payload["matches"] = dresp.discovery.matches
    if dresp.warning:
        payload["warning"] = dresp.warning

    return SkillsResult(
        ok=dresp.ok,
        op=op,
        exit_code=dresp.exit_code,
        message=dresp.message,
        root=dresp.root,
        **payload,
    )


_DESIGN_OPS = frozenset(
    {
        SkillsOp.ADOPT,
        SkillsOp.CREATE,
        SkillsOp.LINT,
        SkillsOp.PAUSE,
        SkillsOp.RESUME,
        SkillsOp.RUN,
    }
)
_DISCOVERY_OPS = frozenset(
    {
        SkillsOp.CATALOG,
        SkillsOp.DISCOVER,
        SkillsOp.LINT,
        SkillsOp.LIST,
        SkillsOp.LIST_ARCHIVED,
        SkillsOp.LIST_UNMANAGED,
        SkillsOp.READ,
    }
)
_GOVERNANCE_OPS = frozenset(
    {
        SkillsOp.LOCK,
        SkillsOp.MOVE,
        SkillsOp.PIN,
        SkillsOp.UNLOCK,
        SkillsOp.UNPIN,
    }
)
_MAINTENANCE_OPS = frozenset({SkillsOp.PRUNE, SkillsOp.PURGE})
_OBSERVABILITY_OPS = frozenset({SkillsOp.LEDGER, SkillsOp.USAGE})
_STORAGE_OPS = frozenset(
    {SkillsOp.ARCHIVE, SkillsOp.BACKUP, SkillsOp.RESTORE, SkillsOp.ROLLBACK}
)
_TRACES_OPS = frozenset({SkillsOp.TRACES})


class SkillsFacade:
    """Composition root for the skills feature (read + authoring)."""

    def __init__(
        self,
        lister: ISkillsListerProtocol | None = None,
        reader: ISkillsReaderProtocol | None = None,
        *,
        linter: ISkillsLinterProtocol | None = None,
        catalog: ISkillsCatalogProtocol | None = None,
        discover: ISkillsDiscoverProtocol | None = None,
        mover: ISkillsMoverProtocol | None = None,
        archiver: ISkillsArchiverProtocol | None = None,
        creator: ISkillsCreatorProtocol | None = None,
        default_root: Path | None = None,
    ) -> None:
        root = default_root if default_root is not None else default_pack_root()
        self._aggregate = default_aggregate(
            lister=lister,
            reader=reader,
            linter=linter,
            catalog=catalog,
            discover=discover,
            mover=mover,
            archiver=archiver,
            creator=creator,
            default_root=root,
        )

    def execute(self, request: SkillsRequest) -> SkillsResult:
        return self._aggregate.execute(request)

    # ─── Read wrappers ───────────────────────────────────────
    def list_skills(self) -> Sequence[SkillRecord]:
        """Return one record per skill in the pack, sorted by name."""
        from shared.src.design.taxonomy_skills_request import SkillsRequest as _SR

        result = self._aggregate.execute(
            _SR(op=SkillsOp.LIST, query=SkillQuery(""), root=None)
        )
        return result.records or []