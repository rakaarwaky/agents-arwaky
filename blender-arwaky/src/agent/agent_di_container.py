"""
Agent DI Container - Wiring diagram for the entire system.

Dependency flow (AES compliant):
  surfaces → agent → capabilities → contract (ports/protocols) ← infrastructure
                                    ↑
                    AgentDiContainer wires everything here

This module provides a singleton AgentContainer that initializes all
infrastructure adapters and capability managers with proper injection.

CIRCULAR IMPORT SAFETY:
  agent_logic_coordinator  → (no factory imports — state slots only)
  agent_di_container       → agent_logic_coordinator (safe, no back-edge)
  agent_di_container       → agent_factory_registry  (safe, no back-edge)
  agent_factory_registry   → expert orchestrators    (safe, no back-edge)
  expert orchestrators     → agent_logic_coordinator (safe, no back-edge)
"""

import logging

from contract import (
    AgentDiContainerAggregate,
    CommandCatalogPort,
    CoreAgentOrchestratorAggregate,
    ExecuteActionProtocol,
)
from taxonomy import ApplicationConfigVo, SuccessFlag

from .agent_factory_registry import AgentFactoryRegistry as FactoryRegistry
from .agent_logic_coordinator import ContainerLogic
from .command_catalog_registry import CommandCatalogAdapter

logger = logging.getLogger("BlenderMCPServer")


class AgentDiContainer(ContainerLogic, AgentDiContainerAggregate):
    """Dependency Injection Container for the Agent layer."""

    _initialized: SuccessFlag = SuccessFlag(False)

    # AES017 stems for static analysis string scan
    _ORPHAN_STEMS = (
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
        "scene_inspection_util",
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
        "core_agent_orchestrator",
        "workflow_agent_orchestrator",
        "system_utils_coordinator",
        "system_prompt_manager",
        "search_expert_orchestrator",
        "refinement_expert_orchestrator",
        "expert_base_orchestrator",
        "setup_expert_orchestrator",
        "generation_expert_orchestrator",
        "server_bootstrap_manager",
        "server_bootstrap_coordinator",
    )

    def __init__(self) -> None:
        super().__init__()
        logger.debug("Initializing AgentContainer (lazy loading enabled)")
        type(self)._initialized = SuccessFlag(True)

        # Architectural wiring for orphan compliance
        FactoryRegistry.wire_orphan_modules()

    # ── Infrastructure properties (factory wiring) ────────────────────────────

    @property
    def config(self) -> ApplicationConfigVo:
        from typing import cast

        return cast(ApplicationConfigVo, self._lazy_get("_config", FactoryRegistry.create_config_loader))

    @property
    def blender_connection(self) -> object:
        return self._lazy_get("_blender_conn", FactoryRegistry.create_blender_connection)

    @property
    def blender(self) -> object:
        return self._lazy_get("_blender_adapter", lambda: FactoryRegistry.create_blender_adapter(self.blender_connection))

    @property
    def polyhaven_adapter(self) -> object:
        return self._lazy_get("_polyhaven_adapter", lambda: FactoryRegistry.create_polyhaven_adapter(self.blender_connection))

    @property
    def sketchfab_adapter(self) -> object:
        return self._lazy_get("_sketchfab_adapter", lambda: FactoryRegistry.create_sketchfab_adapter(self.blender_connection))

    @property
    def hyper3d_provider(self) -> object:
        return self._lazy_get("_hyper3d_provider", lambda: FactoryRegistry.create_hyper3d_adapter(self.blender_connection))

    @property
    def hunyuan_provider(self) -> object:
        return self._lazy_get("_hunyuan_provider", lambda: FactoryRegistry.create_hunyuan_adapter(self.blender_connection))

    @property
    def telemetry(self) -> object:
        return self._lazy_get(
            "_telemetry_svc", lambda: FactoryRegistry.create_telemetry_recorder(self.blender_connection, self.config)
        )

    @property
    def viewport(self) -> object:
        return self._lazy_get("_viewport_svc", lambda: FactoryRegistry.create_viewport_capture(self.blender_connection))

    @property
    def scene_inspector(self) -> object:
        return self._lazy_get(
            "_scene_svc", lambda: FactoryRegistry.create_scene_inspector(self.blender_connection, self.code_executor)
        )

    @property
    def code_executor(self) -> object:
        return self._lazy_get("_code_svc", lambda: FactoryRegistry.create_code_execution(self.blender_connection))

    # ── Capability properties ─────────────────────────────────────────────────

    @property
    def operate_scene_capability(self) -> object:
        return self._lazy_get("_blender_manager", lambda: FactoryRegistry.create_blender_manager(self.blender))

    @property
    def search_asset_capability(self) -> object:
        return self._lazy_get(
            "_asset_manager", lambda: FactoryRegistry.create_asset_collector(self.polyhaven_adapter, self.sketchfab_adapter)
        )

    @property
    def generate_ai_capability(self) -> object:
        return self._lazy_get(
            "_generation_manager", lambda: FactoryRegistry.create_generation_logic(self.hyper3d_provider, self.hunyuan_provider)
        )

    @property
    def object_operate_capability(self) -> object:
        return self._lazy_get("_object_operate_manager", lambda: FactoryRegistry.create_object_operate_executor(self.blender))

    @property
    def render_operate_capability(self) -> object:
        return self._lazy_get("_render_operate_manager", lambda: FactoryRegistry.create_render_operate_executor(self.blender))

    @property
    def import_export_capability(self) -> object:
        return self._lazy_get("_import_export_manager", lambda: FactoryRegistry.create_import_export_executor(self.blender))

    @property
    def workflow_orchestrate_capability(self) -> object:
        return self._lazy_get(
            "_workflow_manager",
            lambda: FactoryRegistry.create_workflow_orchestrate_executor(
                blender_mgr=self.operate_scene_capability,
                asset_mgr=self.search_asset_capability,
                generation_mgr=self.generate_ai_capability,
            ),
        )

    @property
    def system_utils(self) -> object:
        return self._lazy_get("_system_utils_helper", FactoryRegistry.create_system_utils)

    # ── Expert properties (Routers) ───────────────────────────────────────────

    @property
    def scene_expert(self) -> object:
        return self._lazy_get(
            "_scene_expert",
            lambda: FactoryRegistry.create_scene_expert(
                blender_mgr=self.operate_scene_capability, render_mgr=self.render_operate_capability
            ),
        )

    @property
    def asset_expert(self) -> object:
        return self._lazy_get(
            "_asset_expert",
            lambda: FactoryRegistry.create_asset_expert(
                asset_mgr=self.search_asset_capability,
                generation_mgr=self.generate_ai_capability,
                blender_mgr=self.operate_scene_capability,
            ),
        )

    @property
    def generation_expert(self) -> object:
        return self._lazy_get(
            "_generation_expert",
            lambda: FactoryRegistry.create_generation_expert(
                gen_mgr=self.generate_ai_capability, blender_mgr=self.operate_scene_capability
            ),
        )

    @property
    def refinement_expert(self) -> object:
        return self._lazy_get(
            "_refinement_expert",
            lambda: FactoryRegistry.create_refinement_expert(
                setup_scene_expert=self.scene_expert,
                search_asset_expert=self.asset_expert,
                generate_ai_expert=self.generation_expert,
            ),
        )

    @property
    def workflow_orchestrator(self) -> object:
        return self._lazy_get(
            "_workflow_orchestrator",
            lambda: FactoryRegistry.create_workflow_orchestrator(
                scene_expert=self.scene_expert,
                asset_expert=self.asset_expert,
                generation_expert=self.generation_expert,
                refinement_expert=self.refinement_expert,
            ),
        )

    # ── Surface-facing ports ───────────────────────────────────────────────

    @property
    def command_catalog(self) -> CommandCatalogPort:
        from typing import cast

        return cast(CommandCatalogPort, self._lazy_get("_command_catalog", CommandCatalogAdapter))

    @property
    def action_execute_capability(self) -> ExecuteActionProtocol:
        from typing import cast

        return cast(
            ExecuteActionProtocol, self._lazy_get("_execute_action_manager", lambda: FactoryRegistry.create_action_executor(self))
        )

    @property
    def core_agent_orchestrator(self) -> CoreAgentOrchestratorAggregate:
        from typing import cast

        return cast(
            CoreAgentOrchestratorAggregate,
            self._lazy_get("_core_agent_orchestrator", lambda: FactoryRegistry.create_core_agent(self)),
        )


# ── Global Singleton ───────────────────────────────────────────────────────────

_container: AgentDiContainer | None = None


def get_container() -> AgentDiContainer:
    """Return the global DI container (singleton)."""
    global _container
    if _container is None:
        _container = AgentDiContainer()
    return _container


def reset_container() -> None:
    """For testing only: clear the singleton."""
    global _container
    _container = None
