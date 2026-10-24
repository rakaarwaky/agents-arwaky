"""Skills feature shared kernel (contract + taxonomy)."""

from modules.shared.src.skills.contract_skills_aggregate import (
    ISkillsAggregate as ISkillsAggregate,
)
from modules.shared.src.skills.contract_skills_protocol import (
    ISkillsIndexProtocol as ISkillsIndexProtocol,
)
from modules.shared.src.skills.contract_skills_protocol import (
    ISkillsReaderProtocol as ISkillsReaderProtocol,
)
from modules.shared.src.skills.taxonomy_skills_vo import (
    SkillContent as SkillContent,
)
from modules.shared.src.skills.taxonomy_skills_vo import (
    SkillDescription as SkillDescription,
)
from modules.shared.src.skills.taxonomy_skills_vo import (
    SkillQuery as SkillQuery,
)
from modules.shared.src.skills.taxonomy_skills_vo import (
    SkillRecord as SkillRecord,
)
from modules.shared.src.skills.taxonomy_skills_vo import (
    SkillsExitCode as SkillsExitCode,
)
from modules.shared.src.skills.taxonomy_skills_vo import (
    SkillsOp as SkillsOp,
)
from modules.shared.src.skills.taxonomy_skills_vo import (
    SkillsRequest as SkillsRequest,
)
from modules.shared.src.skills.taxonomy_skills_vo import (
    SkillsResult as SkillsResult,
)
from modules.shared.src.skills.taxonomy_skills_vo import (
    SkillsRoot as SkillsRoot,
)
