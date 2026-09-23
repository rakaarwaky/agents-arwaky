"""Shared flat module namespace — import via ``modules.shared.src.<module>``.

All shared taxonomy, contract, and utility modules live directly here:

- taxonomy_*: value objects + domain constants
- contract_*: capability protocol + aggregate ABCs
- utility_*: stateless helpers / I/O utilities
"""
from modules.shared.src.contract_backup_aggregate import IBackupAggregate
from modules.shared.src.contract_backup_protocol import IBackupProtocol
from modules.shared.src.contract_check_aggregate import ICheckAggregate
from modules.shared.src.contract_check_protocol import ICheckProtocol
from modules.shared.src.contract_config_aggregate import IConfigAggregate
from modules.shared.src.contract_config_protocol import IConfigProtocol
from modules.shared.src.contract_daemon_aggregate import IDaemonAggregate
from modules.shared.src.contract_daemon_protocol import IDaemonProtocol
from modules.shared.src.contract_doctor_aggregate import IDoctorAggregate
from modules.shared.src.contract_doctor_protocol import IDoctorProtocol
from modules.shared.src.contract_harness_aggregate import IHarnessAggregate
from modules.shared.src.contract_harness_protocol import IHarnessProtocol
from modules.shared.src.contract_mcp_aggregate import IMcpAggregate
from modules.shared.src.contract_mcp_protocol import IMcpProtocol
from modules.shared.src.contract_service_aggregate import IServiceAggregate
from modules.shared.src.contract_service_protocol import IServiceProtocol
from modules.shared.src.contract_skill_aggregate import ISkillAggregate
from modules.shared.src.contract_skill_protocol import ISkillProtocol
from modules.shared.src.contract_tools_aggregate import IToolsAggregate
from modules.shared.src.contract_tools_protocol import IToolsProtocol

__all__ = [
    "IBackupAggregate",
    "IBackupProtocol",
    "ICheckAggregate",
    "ICheckProtocol",
    "IConfigAggregate",
    "IConfigProtocol",
    "IDaemonAggregate",
    "IDaemonProtocol",
    "IDoctorAggregate",
    "IDoctorProtocol",
    "IHarnessAggregate",
    "IHarnessProtocol",
    "IMcpAggregate",
    "IMcpProtocol",
    "IServiceAggregate",
    "IServiceProtocol",
    "ISkillAggregate",
    "ISkillProtocol",
    "IToolsAggregate",
    "IToolsProtocol",
]
