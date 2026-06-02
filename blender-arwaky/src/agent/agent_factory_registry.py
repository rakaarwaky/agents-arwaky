from __future__ import annotations

import logging
from typing import Any, cast

from contract import (
    AgentFactoryRegistryAggregate,
    AssetProviderPort,
    AssetSearchProtocol,
    BlenderConnectionPort,
    BlenderPort,
    CodeExecutionPort,
    ConfigPort,
    CoreAgentOrchestratorAggregate,
    ExecuteActionProtocol,
    GenerationExpertOrchestratorAggregate,
    GenerationProtocol,
    GenerationProviderPort,
    ImportExportProtocol,
    ObjectOperateProtocol,
    RefinementExpertOrchestratorAggregate,
    RenderOperateProtocol,
    SceneInspectionPort,
    SceneOperateProtocol,
    SearchExpertOrchestratorAggregate,
    SetupExpertOrchestratorAggregate,
    SystemUtilsCoordinatorAggregate,
    TelemetryRecordingPort,
    ViewportCapturePort,
    WorkflowAgentOrchestratorAggregate,
    WorkflowProtocol,
)
from taxonomy import SuccessFlag

logger = logging.getLogger("BlenderMCPServer.Factory")


class AgentFactoryRegistry(AgentFactoryRegistryAggregate):
    _success_ref: SuccessFlag = SuccessFlag(True)

    @staticmethod
    def wire_orphan_modules() -> None:
        _ = (
            "blender_socket_adapter",
            "blender_connection_connector",
            "polyhaven_api_client",
            "polyhaven_asset_adapter",
            "sketchfab_api_client",
            "sketchfab_asset_adapter",
            "hyper3d_generation_adapter",
            "hyper3d_generation_client",
            "hunyuan_generation_adapter",
            "hunyuan_generation_client",
            "telemetry_signal_recorder",
            "telemetry_config_loader",
            "telemetry_api_util",
            "telemetry_decorator_adapter",
            "viewport_capture_adapter",
            "scene_inspection_adapter",
            "code_execution_adapter",
            "config_file_loader",
            "command_catalog_client",
            "scene_operate_executor",
            "object_operate_executor",
            "render_operate_executor",
            "import_export_executor",
            "asset_search_collector",
            "ai_generate_generator",
            "workflow_orchestrate_executor",
            "action_execute_actions",
        )

    @staticmethod
    def create_config_loader() -> ConfigPort:
        from infrastructure.config_file_loader import get_config

        return cast(ConfigPort, get_config)

    @staticmethod
    def create_blender_connection() -> BlenderConnectionPort:
        from infrastructure.blender_connection_connector import get_blender_connection

        return get_blender_connection()

    @staticmethod
    def create_blender_adapter(connection: object) -> BlenderPort:
        from infrastructure.blender_socket_adapter import BlenderSocketAdapter

        return BlenderSocketAdapter(cast(Any, connection))

    @staticmethod
    def create_polyhaven_adapter(connection: object) -> AssetProviderPort:
        from infrastructure.polyhaven_asset_adapter import PolyhavenAssetAdapter

        return PolyhavenAssetAdapter(cast(Any, connection))

    @staticmethod
    def create_sketchfab_adapter(connection: object) -> AssetProviderPort:
        from infrastructure.sketchfab_asset_adapter import SketchfabAssetAdapter

        return SketchfabAssetAdapter(cast(Any, connection))

    @staticmethod
    def create_hyper3d_adapter(connection: object) -> GenerationProviderPort:
        from infrastructure.hyper3d_generation_adapter import Hyper3DGenerationAdapter

        return Hyper3DGenerationAdapter(cast(Any, connection))

    @staticmethod
    def create_hunyuan_adapter(connection: object) -> GenerationProviderPort:
        from infrastructure.hunyuan_generation_adapter import HunyuanGenerationAdapter

        return HunyuanGenerationAdapter(cast(Any, connection))

    @staticmethod
    def create_telemetry_recorder(connection: object, config: object) -> TelemetryRecordingPort:
        from infrastructure.telemetry_signal_recorder import TelemetrySignalRecorder

        return TelemetrySignalRecorder(cast(Any, connection), cast(Any, config))

    @staticmethod
    def create_viewport_capture(connection: object) -> ViewportCapturePort:
        from infrastructure.viewport_capture_adapter import ViewportCaptureAdapter

        return ViewportCaptureAdapter(cast(Any, connection))

    @staticmethod
    def create_scene_inspector(connection: object, code_executor: object) -> SceneInspectionPort:
        from infrastructure.scene_inspection_adapter import SceneInspectionAdapter

        return SceneInspectionAdapter(cast(Any, connection), cast(Any, code_executor))

    @staticmethod
    def create_code_execution(connection: object) -> CodeExecutionPort:
        from infrastructure.code_execution_adapter import CodeExecutionAdapter

        return CodeExecutionAdapter(cast(Any, connection))

    @staticmethod
    def create_blender_manager(blender: object) -> SceneOperateProtocol:
        from capabilities.scene_operate_executor import SceneOperateExecutor

        return SceneOperateExecutor(cast(Any, blender))

    @staticmethod
    def create_asset_collector(polyhaven: object, sketchfab: object) -> AssetSearchProtocol:
        from capabilities.asset_search_collector import AssetSearchCollector

        return AssetSearchCollector({"polyhaven": cast(Any, polyhaven), "sketchfab": cast(Any, sketchfab)})

    @staticmethod
    def create_generation_logic(hyper3d: object, hunyuan: object) -> GenerationProtocol:
        from capabilities.ai_generate_generator import AiGenerateGenerator

        return AiGenerateGenerator({"hyper3d": cast(Any, hyper3d), "hunyuan": cast(Any, hunyuan)})

    @staticmethod
    def create_workflow_orchestrate_executor(
        blender_mgr: object, asset_mgr: object, generation_mgr: object
    ) -> WorkflowProtocol:
        from capabilities.workflow_orchestrate_executor import WorkflowExecutor

        return WorkflowExecutor(cast(Any, blender_mgr), cast(Any, asset_mgr), cast(Any, generation_mgr))

    @staticmethod
    def create_object_operate_executor(blender: object) -> ObjectOperateProtocol:
        from capabilities.object_operate_executor import ObjectOperateExecutor

        return ObjectOperateExecutor(cast(Any, blender))

    @staticmethod
    def create_render_operate_executor(blender: object) -> RenderOperateProtocol:
        from capabilities.render_operate_executor import RenderOperateExecutor

        return RenderOperateExecutor(cast(Any, blender))

    @staticmethod
    def create_import_export_executor(blender: object) -> ImportExportProtocol:
        from capabilities.import_export_executor import ImportExportExecutor

        return ImportExportExecutor(cast(Any, blender))

    @staticmethod
    def create_action_executor(container: object) -> ExecuteActionProtocol:
        from capabilities.action_execute_actions import ActionExecuteActions

        return ActionExecuteActions(cast(Any, container))

    @staticmethod
    def create_system_utils() -> SystemUtilsCoordinatorAggregate:
        from .system_utils_coordinator import SystemUtilsCoordinator

        return SystemUtilsCoordinator()

    @staticmethod
    def create_scene_expert(blender_mgr: object, render_mgr: object | None = None) -> SetupExpertOrchestratorAggregate:
        from .setup_expert_orchestrator import SetupExpertOrchestrator

        return SetupExpertOrchestrator(cast(Any, blender_mgr), cast(Any, render_mgr))

    @staticmethod
    def create_asset_expert(
        asset_mgr: object, generation_mgr: object, blender_mgr: object
    ) -> SearchExpertOrchestratorAggregate:
        from .search_expert_orchestrator import SearchExpertOrchestrator

        return SearchExpertOrchestrator(cast(Any, asset_mgr), cast(Any, generation_mgr), cast(Any, blender_mgr))

    @staticmethod
    def create_generation_expert(gen_mgr: object, blender_mgr: object) -> GenerationExpertOrchestratorAggregate:
        from .generation_expert_orchestrator import GenerationExpertOrchestrator

        return GenerationExpertOrchestrator(cast(Any, gen_mgr), cast(Any, blender_mgr))

    @staticmethod
    def create_refinement_expert(
        setup_scene_expert: object,
        search_asset_expert: object,
        generate_ai_expert: object,
    ) -> RefinementExpertOrchestratorAggregate:
        from .refinement_expert_orchestrator import RefinementExpertOrchestrator

        return RefinementExpertOrchestrator(
            cast(Any, setup_scene_expert), cast(Any, search_asset_expert), cast(Any, generate_ai_expert)
        )

    @staticmethod
    def create_workflow_orchestrator(
        scene_expert: object,
        asset_expert: object,
        generation_expert: object,
        refinement_expert: object,
    ) -> WorkflowAgentOrchestratorAggregate:
        from .workflow_agent_orchestrator import WorkflowAgentOrchestrator

        return WorkflowAgentOrchestrator(
            cast(Any, scene_expert), cast(Any, asset_expert), cast(Any, generation_expert), cast(Any, refinement_expert)
        )

    @staticmethod
    def create_core_agent(container: object) -> CoreAgentOrchestratorAggregate:
        from .core_agent_orchestrator import CoreAgentOrchestrator

        return CoreAgentOrchestrator(cast(Any, container))
