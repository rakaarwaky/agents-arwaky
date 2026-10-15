"""Service feature shared kernel (contract + taxonomy)."""

from modules.shared.src.service.contract_service_aggregate import (
    IServiceAggregate as IServiceAggregate,
)
from modules.shared.src.service.contract_service_protocol import (
    IServiceControlProtocol as IServiceControlProtocol,
)
from modules.shared.src.service.contract_service_protocol import (
    IServiceInspectProtocol as IServiceInspectProtocol,
)
from modules.shared.src.service.taxonomy_service_vo import (
    RESPONSE_DEFAULT as RESPONSE_DEFAULT,
)
from modules.shared.src.service.taxonomy_service_vo import (
    TARGET_ALL as TARGET_ALL,
)
from modules.shared.src.service.taxonomy_service_vo import (
    TARGET_OMNIROUTE as TARGET_OMNIROUTE,
)
from modules.shared.src.service.taxonomy_service_vo import (
    ExitCode as ExitCode,
)
from modules.shared.src.service.taxonomy_service_vo import (
    ServiceOp as ServiceOp,
)
from modules.shared.src.service.taxonomy_service_vo import (
    ServiceRequest as ServiceRequest,
)
from modules.shared.src.service.taxonomy_service_vo import (
    ServiceResponse as ServiceResponse,
)
from modules.shared.src.service.taxonomy_service_vo import (
    ServiceTarget as ServiceTarget,
)
