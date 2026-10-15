"""Harness feature shared kernel (contract + taxonomy)."""

from modules.shared.src.harness.contract_harness_aggregate import (
    IHarnessAggregate as IHarnessAggregate,
)
from modules.shared.src.harness.contract_harness_protocol import (
    IHarnessConnectProtocol as IHarnessConnectProtocol,
)
from modules.shared.src.harness.contract_harness_protocol import (
    IHarnessDisconnectProtocol as IHarnessDisconnectProtocol,
)
from modules.shared.src.harness.contract_harness_protocol import (
    IHarnessProviderProtocol as IHarnessProviderProtocol,
)
from modules.shared.src.harness.contract_harness_protocol import (
    IHarnessSkillsProtocol as IHarnessSkillsProtocol,
)
from modules.shared.src.harness.taxonomy_harness_constant import (
    ALIASES as ALIASES,
)
from modules.shared.src.harness.taxonomy_harness_constant import (
    ALL_HARNESS_IDS as ALL_HARNESS_IDS,
)
from modules.shared.src.harness.taxonomy_harness_constant import (
    ASSET_DIRS as ASSET_DIRS,
)
from modules.shared.src.harness.taxonomy_harness_constant import (
    FALLBACK_MCP_COMMANDS as FALLBACK_MCP_COMMANDS,
)
from modules.shared.src.harness.taxonomy_harness_constant import (
    HARNESSES as HARNESSES,
)
from modules.shared.src.harness.taxonomy_harness_constant import (
    LIVE_SKILLS_STATE as LIVE_SKILLS_STATE,
)
from modules.shared.src.harness.taxonomy_harness_constant import (
    PLACEHOLDER_KEYS as PLACEHOLDER_KEYS,
)
from modules.shared.src.harness.taxonomy_harness_vo import (
    ConnectOpts as ConnectOpts,
)
from modules.shared.src.harness.taxonomy_harness_vo import (
    DisconnectOpts as DisconnectOpts,
)
from modules.shared.src.harness.taxonomy_harness_vo import (
    ExitCode as ExitCode,
)
from modules.shared.src.harness.taxonomy_harness_vo import (
    HarnessConfig as HarnessConfig,
)
from modules.shared.src.harness.taxonomy_harness_vo import (
    HarnessFlags as HarnessFlags,
)
from modules.shared.src.harness.taxonomy_harness_vo import (
    HarnessOp as HarnessOp,
)
from modules.shared.src.harness.taxonomy_harness_vo import (
    HarnessRequest as HarnessRequest,
)
from modules.shared.src.harness.taxonomy_harness_vo import (
    HarnessResponse as HarnessResponse,
)
from modules.shared.src.harness.taxonomy_harness_vo import (
    HarnessTargets as HarnessTargets,
)
from modules.shared.src.harness.taxonomy_harness_vo import (
    HarnessVo as HarnessVo,
)
from modules.shared.src.harness.taxonomy_harness_vo import (
    RouterCredentials as RouterCredentials,
)
from modules.shared.src.harness.taxonomy_harness_vo import (
    SkillsOpts as SkillsOpts,
)
from modules.shared.src.harness.taxonomy_harness_vo import (
    UnsupportedHarnessError as UnsupportedHarnessError,
)
