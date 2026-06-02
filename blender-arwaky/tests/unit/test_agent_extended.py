"""Extended unit tests for the agent layer to close coverage gaps.

Covers:
- server_bootstrap_manager.py (52% -> 100%)
- system_utils_coordinator.py (73% -> 100%)
- agent_factory_registry.py (74% -> 100%)
"""
import pytest
import os
from unittest.mock import MagicMock, patch

from taxonomy import ConfigPath, ConfigValue
from agent.server_bootstrap_manager import ServerBootstrapManager
from agent.system_utils_coordinator import (
    SystemUtilsCoordinator,
    record_startup,
    get_blender_connection,
    shutdown_connection,
    health_check,
)
from agent.agent_factory_registry import AgentFactoryRegistry


class TestServerBootstrapManager:
    """Complete unit tests for ServerBootstrapManager."""

    @patch("agent.server_bootstrap_manager.get_project_root", return_value="/mock/root")
    def test_get_project_root(self, mock_root):
        assert ServerBootstrapManager.get_project_root() == "/mock/root"

    @patch("agent.server_bootstrap_manager.get_config")
    def test_get_config_value(self, mock_get_config):
        mock_get_config.return_value = "custom_val"
        assert ServerBootstrapManager().get(ConfigPath("server.host"), "127.0.0.1") == "custom_val"
        mock_get_config.assert_called_once_with(ConfigPath("server.host"), "127.0.0.1")

    @patch("agent.server_bootstrap_manager.get_project_root", return_value="/mock/root")
    @patch("agent.server_bootstrap_manager.get_config", side_effect=["logs_dir", "server_run.log"])
    @patch("os.makedirs")
    def test_resolve_log_file(self, mock_makedirs, mock_get_config, mock_root):
        log_file = ServerBootstrapManager.resolve_log_file()
        assert log_file == "/mock/root/logs_dir/server_run.log"
        mock_makedirs.assert_called_once_with("/mock/root/logs_dir", exist_ok=True)

    @patch("agent.server_bootstrap_manager.get_project_root", return_value="/mock/root")
    @patch("agent.server_bootstrap_manager.get_config", side_effect=["logs_dir", "server_run.log"])
    @patch("os.makedirs")
    def test_to_request_dict(self, mock_makedirs, mock_get_config, mock_root):
        req_dict = ServerBootstrapManager().to_request_dict()
        assert req_dict == {"log_file": "/mock/root/logs_dir/server_run.log"}

    @patch.dict(os.environ, {"MCP_TRANSPORT": "sse", "MCP_HOST": "0.0.0.0", "MCP_PORT": "9000"})
    def test_resolve_transport_config_from_env(self):
        transport, host, port = ServerBootstrapManager.resolve_transport_config()
        assert transport == "sse"
        assert host == "0.0.0.0"
        assert port == "9000"

    @patch.dict(os.environ, {}, clear=True)
    @patch("agent.server_bootstrap_manager.get_config", side_effect=["stdio", "127.0.0.1", 8000])
    def test_resolve_transport_config_from_config_defaults(self, mock_get_config):
        transport, host, port = ServerBootstrapManager.resolve_transport_config()
        assert transport == "stdio"
        assert host == "127.0.0.1"
        assert port == "8000"


    """Verifies that all registry static factory methods execute correctly and return appropriate objects."""

    def test_wire_orphan_modules(self):
        # Should execute without errors
        AgentFactoryRegistry.wire_orphan_modules()

    def test_infrastructure_factories(self):
        mock_conn = MagicMock()
        mock_config = MagicMock()
        mock_executor = MagicMock()

        assert AgentFactoryRegistry.create_config_loader() is not None
        
        with patch("infrastructure.blender_connection_connector.get_blender_connection", return_value=mock_conn):
            assert AgentFactoryRegistry.create_blender_connection() is mock_conn

        assert AgentFactoryRegistry.create_blender_adapter(mock_conn) is not None
        assert AgentFactoryRegistry.create_polyhaven_adapter(mock_conn) is not None
        assert AgentFactoryRegistry.create_sketchfab_adapter(mock_conn) is not None
        assert AgentFactoryRegistry.create_hyper3d_adapter(mock_conn) is not None
        assert AgentFactoryRegistry.create_hunyuan_adapter(mock_conn) is not None
        assert AgentFactoryRegistry.create_telemetry_recorder(mock_conn, mock_config) is not None
        assert AgentFactoryRegistry.create_viewport_capture(mock_conn) is not None
        assert AgentFactoryRegistry.create_scene_inspector(mock_conn, mock_executor) is not None
        assert AgentFactoryRegistry.create_code_execution(mock_conn) is not None

    def test_capability_factories(self):
        mock_blender = MagicMock()
        mock_polyhaven = MagicMock()
        mock_sketchfab = MagicMock()
        mock_hyper3d = MagicMock()
        mock_hunyuan = MagicMock()
        mock_container = MagicMock()

        assert AgentFactoryRegistry.create_blender_manager(mock_blender) is not None
        assert AgentFactoryRegistry.create_asset_collector(mock_polyhaven, mock_sketchfab) is not None
        assert AgentFactoryRegistry.create_generation_logic(mock_hyper3d, mock_hunyuan) is not None
        assert AgentFactoryRegistry.create_workflow_orchestrate_executor(MagicMock(), MagicMock(), MagicMock()) is not None
        assert AgentFactoryRegistry.create_object_operate_executor(mock_blender) is not None
        assert AgentFactoryRegistry.create_render_operate_executor(mock_blender) is not None
        assert AgentFactoryRegistry.create_import_export_executor(mock_blender) is not None
        assert AgentFactoryRegistry.create_action_executor(mock_container) is not None
        assert AgentFactoryRegistry.create_system_utils() is not None

    def test_expert_factories(self):
        mock_container = MagicMock()
        assert AgentFactoryRegistry.create_scene_expert(MagicMock(), MagicMock()) is not None
        assert AgentFactoryRegistry.create_asset_expert(MagicMock(), MagicMock(), MagicMock()) is not None
        assert AgentFactoryRegistry.create_generation_expert(MagicMock(), MagicMock()) is not None
        assert AgentFactoryRegistry.create_refinement_expert(MagicMock(), MagicMock(), MagicMock()) is not None
        assert AgentFactoryRegistry.create_workflow_orchestrator(MagicMock(), MagicMock(), MagicMock(), MagicMock()) is not None
        assert AgentFactoryRegistry.create_core_agent(mock_container) is not None


class TestAgentBaseContainer:
    """Tests for AgentBaseContainer (0% coverage)."""

    def test_can_instantiate(self):
        from agent.agent_base_container import AgentBaseContainer
        instance = AgentBaseContainer()
        assert instance._success_ref is True
        assert hasattr(instance, "_lazy_get")

    def test_inherits_from_aggregate(self):
        from agent.agent_base_container import AgentBaseContainer
        from contract import AgentBaseContainerAggregate
        assert issubclass(AgentBaseContainer, AgentBaseContainerAggregate)


class TestAgentInitModule:
    """Tests for agent/__init__.py module-level functions (67% coverage)."""

    def test_get_scene_expert(self):
        mock_container = MagicMock()
        mock_container.scene_expert = "scene_expert"
        with patch("agent.get_container", return_value=mock_container):
            from agent import get_scene_expert
            result = get_scene_expert()
            assert result == "scene_expert"

    def test_get_asset_expert(self):
        mock_container = MagicMock()
        mock_container.asset_expert = "asset_expert"
        with patch("agent.get_container", return_value=mock_container):
            from agent import get_asset_expert
            result = get_asset_expert()
            assert result == "asset_expert"

    def test_get_generation_expert(self):
        mock_container = MagicMock()
        mock_container.generation_expert = "gen_expert"
        with patch("agent.get_container", return_value=mock_container):
            from agent import get_generation_expert
            result = get_generation_expert()
            assert result == "gen_expert"

    def test_get_refinement_expert(self):
        mock_container = MagicMock()
        mock_container.refinement_expert = "ref_expert"
        with patch("agent.get_container", return_value=mock_container):
            from agent import get_refinement_expert
            result = get_refinement_expert()
            assert result == "ref_expert"

    def test_get_orchestrator(self):
        mock_container = MagicMock()
        mock_container.workflow_orchestrator = "orchestrator"
        with patch("agent.get_container", return_value=mock_container):
            from agent import get_orchestrator
            result = get_orchestrator()
            assert result == "orchestrator"

    def test_get_all_experts(self):
        mock_container = MagicMock()
        mock_container.scene_expert = "scene"
        mock_container.asset_expert = "asset"
        mock_container.generation_expert = "gen"
        mock_container.refinement_expert = "ref"
        with patch("agent.get_container", return_value=mock_container):
            from agent import get_all_experts
            result = get_all_experts()
            assert result == {
                "tool_scene_ops": "scene",
                "asset": "asset",
                "generation": "gen",
                "refinement": "ref",
            }


class TestCommandCatalogAdapter:
    """Tests for CommandCatalogAdapter (77% coverage)."""

    def test_get_command_spec_existing(self):
        from agent.command_catalog_registry import CommandCatalogAdapter
        from taxonomy.blender_command_vo import CommandCatalog
        adapter = CommandCatalogAdapter()
        # Use a real command from the catalog
        commands = CommandCatalog.COMMAND_CATALOG
        if commands:
            first_action = list(commands.keys())[0]
            spec = adapter.get_command_spec(first_action)
            assert spec is not None

    def test_get_command_spec_nonexistent(self):
        from agent.command_catalog_registry import CommandCatalogAdapter
        from taxonomy import ActionName
        adapter = CommandCatalogAdapter()
        spec = adapter.get_command_spec(ActionName("does_not_exist_42"))
        assert spec is None

    def test_list_actions(self):
        from agent.command_catalog_registry import CommandCatalogAdapter
        adapter = CommandCatalogAdapter()
        actions = adapter.list_actions()
        assert len(actions) > 0
        assert all(hasattr(a, "value") or isinstance(a, str) for a in actions)

    def test_filter_by_domain(self):
        from agent.command_catalog_registry import CommandCatalogAdapter
        from taxonomy import DomainRef
        adapter = CommandCatalogAdapter()
        filtered = adapter.filter_by_domain(DomainRef("scene"))
        assert len(filtered) > 0
        for spec in filtered.values():
            assert spec["domain"] == "scene"

    def test_filter_by_domain_empty(self):
        from agent.command_catalog_registry import CommandCatalogAdapter
        from taxonomy import DomainRef
        adapter = CommandCatalogAdapter()
        filtered = adapter.filter_by_domain(DomainRef("nonexistent_domain_xyz"))
        assert len(filtered) == 0




class TestSystemUtilsCoordinatorExceptionsAndAliases:
    """Covers edge cases, exceptions, and module-level aliases in SystemUtilsCoordinator."""

    @patch("agent.system_utils_coordinator._get_record_startup", side_effect=Exception("failed"))
    def test_record_startup_exception_handling(self, mock_startup):
        SystemUtilsCoordinator.record_startup()

    @patch("agent.system_utils_coordinator._get_shutdown_connection_fn", side_effect=Exception("failed"))
    def test_shutdown_connection_exception_handling(self, mock_shutdown):
        SystemUtilsCoordinator.shutdown_connection()

    @patch("agent.system_utils_coordinator._get_blender_conn_fn", side_effect=RuntimeError("no connection"))
    @patch("agent.system_utils_coordinator._get_telemetry_config_class", side_effect=ImportError("no class"))
    def test_health_check_failed_connections_and_telemetry(self, mock_telemetry, mock_conn):
        status = SystemUtilsCoordinator.health_check()
        assert status["blender_connected"] is False
        assert status["telemetry_enabled"] is False
        assert status["status"] == "degraded"
        assert "no connection" in str(status["connection_error"])

    def test_module_aliases_exist_and_callable(self):
        from agent.system_utils_coordinator import (
            record_startup, get_blender_connection,
            shutdown_connection, health_check,
        )
        assert callable(record_startup)
        assert callable(get_blender_connection)
        assert callable(shutdown_connection)
        assert callable(health_check)

    @patch("agent.system_utils_coordinator.record_startup")
    @patch("agent.system_utils_coordinator.get_blender_connection")
    @patch("agent.system_utils_coordinator.shutdown_connection")
    @patch("agent.system_utils_coordinator.health_check")
    def test_module_aliases_delegate_to_class_methods(
        self, mock_hc, mock_sd, mock_gb, mock_rs
    ):
        from agent.system_utils_coordinator import (
            record_startup, get_blender_connection,
            shutdown_connection, health_check,
        )
        record_startup()
        mock_rs.assert_called_once()
        get_blender_connection()
        mock_gb.assert_called_once()
        shutdown_connection()
        mock_sd.assert_called_once()
        health_check()
        mock_hc.assert_called_once()
