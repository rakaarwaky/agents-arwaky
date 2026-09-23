"""Shared flat module namespace — import via ``modules.shared.src.<module>``.

All shared taxonomy, contract, and utility modules live directly here:

- taxonomy_*: value objects + domain constants
- contract_*: capability protocol + aggregate ABCs
- utility_*: stateless helpers / I/O utilities
"""
from modules.shared.src.contract_backup_aggregate import IBackupAggregate
from modules.shared.src.contract_backup_protocol import (
    IBackupGateway,
    IBackupProtocol,
    IListArchivesProtocol,
    IRestoreProtocol,
)
from modules.shared.src.contract_check_aggregate import ICheckAggregate
from modules.shared.src.contract_check_protocol import ICheckProtocol
from modules.shared.src.contract_config_protocol import (
    IConfigDetectFormatProtocol,
    IConfigListMcpProtocol,
    IConfigLoadProtocol,
    IConfigMergeMcpProtocol,
    IConfigModifier,
    IConfigRemoveEnvKeysProtocol,
    IConfigRemoveMcpProtocol,
    IConfigSaveProtocol,
    IConfigSetEnvKeysProtocol,
    IConfigWriter,
)
from modules.shared.src.contract_daemon_aggregate import IDaemonAggregate
from modules.shared.src.contract_daemon_protocol import (
    IDaemonLogsProtocol,
    IDaemonManager,
    IDaemonRestartProtocol,
    IDaemonStartProtocol,
    IDaemonStatusProtocol,
    IDaemonStopProtocol,
)
from modules.shared.src.contract_doctor_aggregate import IDoctorAggregate
from modules.shared.src.contract_doctor_protocol import IDoctorProtocol
from modules.shared.src.contract_mcp_aggregate import IMcpAggregate
from modules.shared.src.contract_mcp_protocol import IMcpConfigProtocol
from modules.shared.src.contract_service_aggregate import IServiceAggregate
from modules.shared.src.contract_service_protocol import (
    IServiceHelpProtocol,
    IServiceLogsProtocol,
    IServiceManager,
    IServiceRestartProtocol,
    IServiceStartProtocol,
    IServiceStatusProtocol,
    IServiceStopProtocol,
)
from modules.shared.src.contract_skill_aggregate import ISkillAggregate
from modules.shared.src.contract_skill_protocol import (
    ISkillAuditProtocol,
    ISkillCheckProtocol,
    ISkillInstallCmdProtocol,
    ISkillInstallProtocol,
    ISkillListProtocol,
    ISkillPruneProtocol,
    ISkillProvisioner,
    ISkillRegistry,
    ISkillShowProtocol,
    ISkillUninstallCmdProtocol,
)
from modules.shared.src.contract_tools_aggregate import IToolsAggregate
from modules.shared.src.contract_tools_protocol import (
    IToolAdapterFacade,
    IToolAdapterInstallProtocol,
    IToolAdapterUpdateProtocol,
    IToolInstallProtocol,
    IToolIsPinSatisfiedProtocol,
    IToolIsRegisteredProtocol,
    IToolOwnedPathsProtocol,
    IToolResolveProtocol,
    IToolRunProtocol,
    IToolSatisfiedProtocol,
    IToolUninstallProtocol,
    IToolUpdateProtocol,
)

__all__ = [
    "IBackupAggregate",
    "IBackupGateway",
    "IBackupProtocol",
    "ICheckAggregate",
    "ICheckProtocol",
    "IConfigDetectFormatProtocol",
    "IConfigListMcpProtocol",
    "IConfigLoadProtocol",
    "IConfigMergeMcpProtocol",
    "IConfigModifier",
    "IConfigRemoveEnvKeysProtocol",
    "IConfigRemoveMcpProtocol",
    "IConfigSaveProtocol",
    "IConfigSetEnvKeysProtocol",
    "IConfigWriter",
    "IDaemonAggregate",
    "IDaemonLogsProtocol",
    "IDaemonManager",
    "IDaemonRestartProtocol",
    "IDaemonStartProtocol",
    "IDaemonStatusProtocol",
    "IDaemonStopProtocol",
    "IDoctorAggregate",
    "IDoctorProtocol",
    "IListArchivesProtocol",
    "IMcpAggregate",
    "IMcpConfigProtocol",
    "IRestoreProtocol",
    "IServiceAggregate",
    "IServiceHelpProtocol",
    "IServiceLogsProtocol",
    "IServiceManager",
    "IServiceRestartProtocol",
    "IServiceStartProtocol",
    "IServiceStatusProtocol",
    "IServiceStopProtocol",
    "ISkillAggregate",
    "ISkillAuditProtocol",
    "ISkillCheckProtocol",
    "ISkillInstallCmdProtocol",
    "ISkillInstallProtocol",
    "ISkillListProtocol",
    "ISkillPruneProtocol",
    "ISkillProvisioner",
    "ISkillRegistry",
    "ISkillShowProtocol",
    "ISkillUninstallCmdProtocol",
    "IToolAdapterFacade",
    "IToolAdapterInstallProtocol",
    "IToolAdapterUpdateProtocol",
    "IToolInstallProtocol",
    "IToolIsPinSatisfiedProtocol",
    "IToolIsRegisteredProtocol",
    "IToolOwnedPathsProtocol",
    "IToolResolveProtocol",
    "IToolRunProtocol",
    "IToolSatisfiedProtocol",
    "IToolUninstallProtocol",
    "IToolUpdateProtocol",
    "IToolsAggregate",
]
