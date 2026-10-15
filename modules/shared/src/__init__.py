"""Shared flat module namespace — import via ``modules.shared.src.<module>``.

All shared taxonomy, contract, and utility modules live directly here:

- taxonomy_*: value objects + domain constants
- contract_*: capability protocol + aggregate ABCs
- utility_*: stateless helpers / I/O utilities
"""
from modules.shared.src.backup.contract_backup_aggregate import IBackupAggregate
from modules.shared.src.backup.contract_backup_protocol import IBackupProtocol
from modules.shared.src.config.contract_config_aggregate import IConfigAggregate
from modules.shared.src.config.contract_config_protocol import (
    IConfigModifierProtocol,
    IConfigReaderProtocol,
)
from modules.shared.src.daemon.contract_daemon_aggregate import IDaemonAggregate
from modules.shared.src.daemon.contract_daemon_protocol import IDaemonProtocol
from modules.shared.src.doctor.contract_doctor_aggregate import IDoctorAggregate
from modules.shared.src.doctor.contract_doctor_protocol import IDoctorProtocol
from modules.shared.src.harness.contract_harness_aggregate import IHarnessAggregate
from modules.shared.src.harness.contract_harness_protocol import (
    IHarnessConnectProtocol,
    IHarnessDisconnectProtocol,
    IHarnessProviderProtocol,
    IHarnessSkillsProtocol,
)
from modules.shared.src.mcp.contract_mcp_aggregate import IMcpAggregate
from modules.shared.src.mcp.contract_mcp_protocol import (
    IMcpListProtocol,
    IMcpWriteProtocol,
)
from modules.shared.src.service.contract_service_aggregate import IServiceAggregate
from modules.shared.src.service.contract_service_protocol import (
    IServiceControlProtocol,
    IServiceInspectProtocol,
)
from modules.shared.src.tools.contract_tools_aggregate import IToolsAggregate
from modules.shared.src.tools.contract_tools_protocol import (
    IToolsAdapterProtocol,
    IToolsInstallerProtocol,
    IToolsRunnerProtocol,
    IToolsUninstallerProtocol,
    IToolsUpdaterProtocol,
)

__all__ = [
    "IBackupAggregate",
    "IBackupProtocol",
    "IConfigAggregate",
    "IConfigModifierProtocol",
    "IConfigReaderProtocol",
    "IDaemonAggregate",
    "IDaemonProtocol",
    "IDoctorAggregate",
    "IDoctorProtocol",
    "IHarnessAggregate",
    "IHarnessConnectProtocol",
    "IHarnessDisconnectProtocol",
    "IHarnessProviderProtocol",
    "IHarnessSkillsProtocol",
    "IMcpAggregate",
    "IMcpListProtocol",
    "IMcpWriteProtocol",
    "IServiceAggregate",
    "IServiceControlProtocol",
    "IServiceInspectProtocol",
    "IToolsAdapterProtocol",
    "IToolsAggregate",
    "IToolsInstallerProtocol",
    "IToolsRunnerProtocol",
    "IToolsUninstallerProtocol",
    "IToolsUpdaterProtocol",
]
