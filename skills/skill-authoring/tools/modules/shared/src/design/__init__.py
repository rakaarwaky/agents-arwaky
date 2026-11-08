"""Skills-design shared kernel — design layer.

SSOT for validation budgets, naming rules, layout invariants, domain
entities, value objects, request/response envelopes, and the aggregate
dispatch contract.
"""
from shared.src.common.taxonomy_common_constant import (
    BM25F_SCORE_SCALE,
    CATEGORY_DESCRIPTION_FILENAME,
    IGNORED_CATEGORY_DIRS,
    NAME_MAX,
    NAME_MIN,
    NAME_RE,
)
from shared.src.design.taxonomy_skills_constant import (
    ARCHIVE_DIRNAME,
)
from shared.src.common.taxonomy_common_entity import (
    CategorySummary,
    SkillEntry,
)
from shared.src.design.taxonomy_skills_entity import (
    Issue,
)
from shared.src.common.taxonomy_common_vo import (
    BM25FHit,
    CatalogCheckResult,
    CatalogReport,
    CategoryName,
    DiscoveryMatch,
    DiscoveryResult,
    SkillContent,
    SkillDescription,
    SkillName,
    SkillRecord,
    SkillsJsonPayload,
)
from shared.src.design.taxonomy_skills_vo import (
    LintReport,
    MutationOutcome,
    MutationPlan,
    MutationStep,
    NewCategoryPlan,
    SkillCreatePlan,
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