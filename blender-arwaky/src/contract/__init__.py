"""
Contract layer exports — AES Ports, Protocols, and Aggregate/VO types.

Naming convention:
- *_aggregate.py    : Structural contracts for agents/orchestrators
- *_vo.py           : Data Transfer Objects (Value Objects)
- *_protocol.py     : Protocol (typing.Protocol) definitions
- *_port.py         : Port interfaces and connection/configuration abstractions
"""

# ============== Aggregate types (Structural) ==============

from .adapter_blender_port import BlenderPort
from .agent_base_aggregate import AgentBaseContainerAggregate
from .agent_di_aggregate import AgentDiContainerAggregate
from .agent_factory_aggregate import AgentFactoryRegistryAggregate
from .ai_generation_protocol import GenerationProtocol
from .api_polyhaven_port import PolyhavenApiPort
from .api_sketchfab_port import SketchfabApiPort
from .app_config_port import ConfigPort, ConfigValue
from .asset_search_protocol import AssetSearchProtocol
from .capture_viewport_port import ViewportCapturePort

# ============== Ports ==============
from .command_catalog_port import CommandCatalogPort
from .connection_blender_port import BlenderConnectionPort
from .connection_factory_port import BlenderConnectionFactoryPort
from .core_agent_aggregate import CoreAgentOrchestratorAggregate
from .execute_action_protocol import ExecuteActionProtocol
from .execution_code_port import CodeExecutionPort
from .expert_base_aggregate import ExpertBaseOrchestratorAggregate
from .generation_expert_aggregate import GenerationExpertOrchestratorAggregate
from .import_export_protocol import ImportExportProtocol
from .inspection_scene_port import SceneInspectionPort
from .object_operate_protocol import ObjectOperateProtocol
from .provider_asset_port import AssetProviderPort
from .provider_generation_port import GenerationProviderPort
from .recording_telemetry_port import TelemetryRecordingPort
from .refinement_expert_aggregate import RefinementExpertOrchestratorAggregate
from .render_operate_protocol import RenderOperateProtocol

# ============== Protocols ==============
from .scene_operate_protocol import SceneOperateProtocol
from .search_expert_aggregate import SearchExpertOrchestratorAggregate
from .server_bootstrap_aggregate import ServerBootstrapManagerAggregate
from .setup_expert_aggregate import SetupExpertOrchestratorAggregate
from .system_prompt_aggregate import SystemPromptManagerAggregate
from .system_utils_aggregate import SystemUtilsCoordinatorAggregate
from .tool_hunyuan_port import HunyuanToolPort
from .tool_hyper3d_port import Hyper3dToolPort
from .workflow_agent_aggregate import WorkflowAgentOrchestratorAggregate
from .workflow_operate_protocol import WorkflowProtocol

__all__ = [
    # Aggregate — Structural
    "AgentBaseContainerAggregate",
    "AgentDiContainerAggregate",
    "AgentFactoryRegistryAggregate",
    "CoreAgentOrchestratorAggregate",
    "ExpertBaseOrchestratorAggregate",
    "GenerationExpertOrchestratorAggregate",
    "RefinementExpertOrchestratorAggregate",
    "SearchExpertOrchestratorAggregate",
    "ServerBootstrapManagerAggregate",
    "SetupExpertOrchestratorAggregate",
    "SystemPromptManagerAggregate",
    "SystemUtilsCoordinatorAggregate",
    "WorkflowAgentOrchestratorAggregate",
    # Protocols
    "SceneOperateProtocol",
    "ObjectOperateProtocol",
    "RenderOperateProtocol",
    "ImportExportProtocol",
    "AssetSearchProtocol",
    "GenerationProtocol",
    "WorkflowProtocol",
    "ExecuteActionProtocol",
    # Ports
    "CommandCatalogPort",
    "AssetProviderPort",
    "BlenderPort",
    "GenerationProviderPort",
    "BlenderConnectionPort",
    "CodeExecutionPort",
    "SceneInspectionPort",
    "ViewportCapturePort",
    "TelemetryRecordingPort",
    "PolyhavenApiPort",
    "SketchfabApiPort",
    "HunyuanToolPort",
    "Hyper3dToolPort",
    "ConfigPort",
    "ConfigValue",
    "BlenderConnectionFactoryPort",
]
