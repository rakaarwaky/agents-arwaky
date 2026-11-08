"""Skills-design shared kernel — design layer.

SSOT for validation budgets, naming rules, layout invariants, domain
entities, value objects, request/response envelopes, and the aggregate
dispatch contract.
"""
from shared.src.design.taxonomy_skills_constant import (
    ARCHIVE_DIRNAME,
    BM25F_SCORE_SCALE,
    CATEGORY_DESCRIPTION_FILENAME,
    IGNORED_CATEGORY_DIRS,
    NAME_MAX,
    NAME_MIN,
    NAME_RE,
)
from shared.src.design.taxonomy_skills_entity import (
    CategorySummary,
    Issue,
    SkillEntry,
)
from shared.src.design.taxonomy_skills_vo import (
    BM25FHit,
    CatalogCheckResult,
    CatalogReport,
    CategoryName,
    DiscoveryMatch,
    DiscoveryResult,
    LintReport,
    MutationOutcome,
    MutationPlan,
    MutationStep,
    NewCategoryPlan,
    SkillContent,
    SkillCreatePlan,
    SkillDescription,
    SkillName,
    SkillRecord,
    SkillsJsonPayload,
    TelemetryRow,
    ValidationReport,
)
from shared.src.design.taxonomy_skills_request import (
    SkillQuery,
    SkillsOp,
    SkillsRequest,
    SkillsRoot,
)
from shared.src.design.taxonomy_skills_response import (
    SkillsExitCode,
    SkillsResult,
)
from shared.src.design.contract_skills_aggregate import ISkillsAggregate
from shared.src.design.contract_skills_protocol import (
    ISkillsArchiverProtocol,
    ISkillsAdopterProtocol,
    ISkillsBackupProtocol,
    ISkillsCatalogProtocol,
    ISkillsCreatorProtocol,
    ISkillsDiscoverProtocol,
    ISkillsLedgerProtocol,
    ISkillsListerProtocol,
    ISkillsLockerProtocol,
    ISkillsLinterProtocol,
    ISkillsMoverProtocol,
    ISkillsPinerProtocol,
    ISkillsPruneProtocol,
    ISkillsPurgeProtocol,
    ISkillsReaderProtocol,
    ISkillsRestoreProtocol,
    ISkillsRollbackProtocol,
    ISkillsRunnerProtocol,
    ISkillsTelemetryProtocol,
)
