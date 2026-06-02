"""Unit tests for all surface handlers, entry points, and MCP tool adapters."""
import pytest
import asyncio
import sys
import json
import argparse
from unittest.mock import MagicMock, AsyncMock, patch
from contextlib import asynccontextmanager

from taxonomy import (
    Prompt, JobId, ProviderName, ActionName, Details,
    DomainRef, FormatRef, SkillName, SectionRef, ExitCode
)
from contract import AgentDiContainerAggregate
from surfaces.status_check_handler import StatusCheckHandler
from surfaces.server_instance_handler import ServerInstanceHandler
from surfaces.cli_command_handler import CliCommandHandler
from surfaces.health_check_handler import HealthCheckHandler
from surfaces.command_execute_handler import CommandExecuteHandler
from surfaces.commands_list_handler import CommandsListHandler
from surfaces.prompt_register_handler import PromptHandlerModule
from surfaces.skill_read_handler import SkillReadHandler
from surfaces.server_start_handler import ServerStartHandler


class TestStatusCheckHandler:
    """Tests for StatusCheckHandler."""

    @pytest.mark.asyncio
    async def test_status_check_resolution(self):
        mock_mcp = MagicMock()
        mock_tool_decorator = MagicMock()
        mock_mcp.tool.return_value = mock_tool_decorator
        
        # 1. Register tool
        StatusCheckHandler.register_check_status(mock_mcp)
        mock_mcp.tool.assert_called_once()
        
        # Extract the registered tool function
        check_status_fn = mock_tool_decorator.call_args[0][0]
        
        # 2. Test status execution paths with mock DI container
        mock_container = MagicMock(spec=AgentDiContainerAggregate)
        mock_container.core_agent_orchestrator = MagicMock()
        mock_container.core_agent_orchestrator.check_status = AsyncMock(return_value=Prompt("status_ok"))
        
        with patch("agent.agent_di_container.get_container", return_value=mock_container):
            # A. Auto provider (contains hunyuan)
            res = await check_status_fn(JobId("job-hunyuan-123"), ProviderName("auto"))
            assert res == Prompt("status_ok")
            mock_container.core_agent_orchestrator.check_status.assert_called_with(
                ProviderName("hunyuan"), JobId("job-hunyuan-123")
            )
            
            # B. Auto provider (default to hyper3d)
            res2 = await check_status_fn(JobId("job-other-123"), ProviderName("auto"))
            assert res2 == Prompt("status_ok")
            mock_container.core_agent_orchestrator.check_status.assert_called_with(
                ProviderName("hyper3d"), JobId("job-other-123")
            )
            
            # C. Explicit provider
            res3 = await check_status_fn(JobId("job-123"), ProviderName("rodin"))
            assert res3 == Prompt("status_ok")
            mock_container.core_agent_orchestrator.check_status.assert_called_with(
                ProviderName("rodin"), JobId("job-123")
            )


class TestServerInstanceHandler:
    """Tests for ServerInstanceHandler."""

    @pytest.mark.asyncio
    async def test_server_lifespan(self):
        mock_server = MagicMock()
        
        # Setup mocks for system utils
        with patch("surfaces.server_instance_handler.record_startup") as mock_record_startup, \
             patch("surfaces.server_instance_handler.get_blender_connection", return_value="mock_conn") as mock_get_conn, \
             patch("surfaces.server_instance_handler.shutdown_connection") as mock_shutdown_conn:
            
            # Enter the context manager
            async with ServerInstanceHandler.server_lifespan(mock_server) as startup_data:
                assert startup_data["blender_connected"] is True
                mock_record_startup.assert_called_once()
                mock_get_conn.assert_called_once()
                
            mock_shutdown_conn.assert_called_once()

    @pytest.mark.asyncio
    async def test_server_lifespan_blender_fails(self):
        mock_server = MagicMock()
        
        with patch("surfaces.server_instance_handler.record_startup") as mock_record_startup, \
             patch("surfaces.server_instance_handler.get_blender_connection", side_effect=Exception("Connection failed")), \
             patch("surfaces.server_instance_handler.shutdown_connection") as mock_shutdown_conn:
            
            async with ServerInstanceHandler.server_lifespan(mock_server) as startup_data:
                assert startup_data["blender_connected"] is False
                
            mock_shutdown_conn.assert_called_once()

    def test_get_mcp_instance(self):
        # We reset singleton for testing
        with patch("surfaces.server_instance_handler._mcp_instance", None), \
             patch("surfaces.server_instance_handler.FastMCP") as mock_fastmcp_class, \
             patch("surfaces.tool_registry_handler.register_tools") as mock_reg_tools, \
             patch("surfaces.prompt_register_handler.register_prompts") as mock_reg_prompts:
            
            mock_mcp = MagicMock()
            mock_fastmcp_class.return_value = mock_mcp
            
            res = ServerInstanceHandler.get_mcp_instance()
            assert res == mock_mcp
            mock_fastmcp_class.assert_called_once()
            mock_reg_tools.assert_called_once_with(mock_mcp)
            mock_reg_prompts.assert_called_once_with(mock_mcp)


class TestCliCommandHandler:
    """Tests for CliCommandHandler."""

    def test_get_container_fails_if_none(self):
        with patch("agent.agent_di_container.get_container", return_value=None):
            with pytest.raises(RuntimeError) as exc:
                CliCommandHandler._get_container()
            assert "DI container not initialized" in str(exc.value)

    def test_get_orchestrator(self):
        mock_container = MagicMock()
        mock_container.core_agent_orchestrator = "mock_orchestrator"
        
        with patch.object(CliCommandHandler, "_get_container", return_value=mock_container):
            with patch.object(CliCommandHandler, "_orchestrator", None):
                res = CliCommandHandler.get_orchestrator()
                assert res == "mock_orchestrator"
                assert CliCommandHandler._orchestrator == "mock_orchestrator"

    def test_build_action_map(self):
        mock_container = MagicMock()
        mock_container.core_agent_orchestrator = MagicMock()
        mock_container.core_agent_orchestrator.execute_action = AsyncMock(return_value=Prompt("action_done"))
        
        with patch.object(CliCommandHandler, "_get_container", return_value=mock_container):
            with patch("taxonomy.blender_command_vo.CommandCatalog.COMMAND_CATALOG", {"cleanup": {}}):
                action_map = CliCommandHandler.build_action_map()
                assert "cleanup" in action_map
                
                # Execute the wrapped action
                res = asyncio.run(action_map["cleanup"](force=True))
                assert res == Prompt("action_done")
                mock_container.core_agent_orchestrator.execute_action.assert_called_with(
                    ActionName("cleanup"), {"force": True}
                )

    def test_main_cli_dispatch_success(self):
        mock_args = MagicMock()
        mock_args.action = "cleanup"
        mock_args.args = '{"force": true}'
        mock_args.json_output = False
        mock_args.log_level = "WARNING"
        
        with patch("argparse.ArgumentParser.parse_args", return_value=mock_args), \
             patch.object(CliCommandHandler, "build_action_map", return_value={"cleanup": AsyncMock(return_value="executed")}), \
             patch("sys.stdout.isatty", return_value=True):
            
            res = CliCommandHandler.main()
            assert res == ExitCode(0)

    def test_main_cli_json_decode_fails(self):
        mock_args = MagicMock()
        mock_args.action = "cleanup"
        mock_args.args = '{invalid_json}'
        mock_args.log_level = "WARNING"
        
        with patch("argparse.ArgumentParser.parse_args", return_value=mock_args):
            res = CliCommandHandler.main()
            assert res == ExitCode(1)


class TestHealthCheckHandler:
    """Tests for HealthCheckHandler."""

    @pytest.mark.asyncio
    async def test_health_check(self):
        mock_mcp = MagicMock()
        mock_tool_decorator = MagicMock()
        mock_mcp.tool.return_value = mock_tool_decorator
        
        HealthCheckHandler.register_health_check(mock_mcp)
        mock_mcp.tool.assert_called_once()
        
        health_fn = mock_tool_decorator.call_args[0][0]
        
        mock_container = MagicMock()
        mock_container.core_agent_orchestrator = MagicMock()
        mock_container.core_agent_orchestrator.health_check.return_value = Prompt("healthy")
        
        with patch("agent.agent_di_container.get_container", return_value=mock_container):
            res = await health_fn()
            assert res == Prompt("healthy")


class TestCommandExecuteHandler:
    """Tests for CommandExecuteHandler."""

    @pytest.mark.asyncio
    async def test_execute_command(self):
        mock_mcp = MagicMock()
        mock_tool_decorator = MagicMock()
        mock_mcp.tool.return_value = mock_tool_decorator
        
        CommandExecuteHandler.register_execute_command(mock_mcp)
        mock_mcp.tool.assert_called_once()
        
        exec_fn = mock_tool_decorator.call_args[0][0]
        
        # 1. Success execution
        mock_container = MagicMock()
        mock_container.core_agent_orchestrator = MagicMock()
        mock_container.core_agent_orchestrator.execute_action = AsyncMock(return_value=Prompt("action_ok"))
        
        with patch("agent.agent_di_container.get_container", return_value=mock_container):
            res = await exec_fn(ActionName("cleanup"), {"force": True})
            assert res == Prompt("action_ok")
            
        # 2. Success with no args (args=None branch)
        with patch("agent.agent_di_container.get_container", return_value=mock_container):
            res_no_args = await exec_fn(ActionName("cleanup"))
            assert res_no_args == Prompt("action_ok")

        # 3. Failure/exception execution
        mock_container.core_agent_orchestrator.execute_action = AsyncMock(side_effect=Exception("blender crash"))
        with patch("agent.agent_di_container.get_container", return_value=mock_container):
            res2 = await exec_fn(ActionName("cleanup"), {"force": True})
            assert "blender crash" in str(res2)


class TestCommandsListHandler:
    """Tests for CommandsListHandler."""

    @pytest.mark.asyncio
    async def test_list_commands(self):
        mock_mcp = MagicMock()
        mock_tool_decorator = MagicMock()
        mock_mcp.tool.return_value = mock_tool_decorator
        
        CommandsListHandler.register_list_commands(mock_mcp)
        mock_mcp.tool.assert_called_once()
        
        list_fn = mock_tool_decorator.call_args[0][0]
        
        mock_container = MagicMock()
        mock_container.core_agent_orchestrator = MagicMock()
        mock_container.core_agent_orchestrator.list_commands.return_value = Prompt("list_ok")
        
        with patch("agent.agent_di_container.get_container", return_value=mock_container):
            res = list_fn(DomainRef("scene"), FormatRef("summary"))
            assert res == Prompt("list_ok")
            mock_container.core_agent_orchestrator.list_commands.assert_called_with(
                DomainRef("scene"), FormatRef("summary")
            )


class TestPromptHandlerModule:
    """Tests for PromptHandlerModule."""

    def test_asset_creation_strategy(self):
        res = PromptHandlerModule.asset_creation_strategy()
        assert len(res) == 1
        assert "Content" in str(res[0]) or "content" in res[0]

    def test_register_prompts(self):
        mock_mcp = MagicMock()
        PromptHandlerModule.register_prompts(mock_mcp)
        assert mock_mcp.prompt.call_count == 4
        
        # Test prompt execution wrapper values
        with patch("surfaces.prompt_register_handler.get_lighting_expert_prompt", return_value="lighting_text"), \
             patch("surfaces.prompt_register_handler.get_layout_expert_prompt", return_value="layout_text"), \
             patch("surfaces.prompt_register_handler.get_text_to_scene_orchestrator_prompt", return_value="workflow_text"):
            
            # Retrieve decoratee prompts
            lighting_decorator_fn = mock_mcp.prompt.call_args_list[1][1]["name"]
            assert lighting_decorator_fn == "lighting_expert"


class TestSkillReadHandler:
    """Tests for SkillReadHandler."""

    @pytest.mark.asyncio
    async def test_read_skill_context(self):
        mock_mcp = MagicMock()
        mock_tool_decorator = MagicMock()
        mock_mcp.tool.return_value = mock_tool_decorator
        
        SkillReadHandler.register_read_skill_context(mock_mcp)
        mock_mcp.tool.assert_called_once()
        
        read_fn = mock_tool_decorator.call_args[0][0]
        
        mock_container = MagicMock()
        mock_container.core_agent_orchestrator = MagicMock()
        mock_container.core_agent_orchestrator.read_skill_context.return_value = Prompt("skill_ok")
        
        with patch("agent.agent_di_container.get_container", return_value=mock_container):
            res = read_fn(SkillName("dummy"), SectionRef("architectures"))
            assert res == Prompt("skill_ok")
            mock_container.core_agent_orchestrator.read_skill_context.assert_called_with(
                SkillName("dummy"), SectionRef("architectures")
            )


class TestServerStartHandler:
    """Tests for ServerStartHandler."""

    def test_setup_logging(self):
        with patch("agent.server_bootstrap_manager.ServerBootstrapManager.resolve_log_file", return_value="/tmp/test.log"), \
             patch("logging.basicConfig") as mock_basic_config:
            ServerStartHandler._setup_logging()
            mock_basic_config.assert_called_once()

    def test_main_sse_transport(self):
        mock_mcp = MagicMock()
        mock_mcp.settings = MagicMock()
        
        with patch("surfaces.server_start_handler.ServerStartHandler._setup_logging") as mock_setup_log, \
             patch("surfaces.server_instance_handler.ServerInstanceHandler.get_mcp_instance", return_value=mock_mcp) as mock_get_mcp, \
             patch("agent.server_bootstrap_manager.ServerBootstrapManager.resolve_transport_config", return_value=("sse", "127.0.0.1", "8000")):
            
            ServerStartHandler.main()
            mock_setup_log.assert_called_once()
            mock_get_mcp.assert_called_once()
            mock_mcp.run.assert_called_with(transport="sse")
            assert mock_mcp.settings.host == "127.0.0.1"
            assert mock_mcp.settings.port == 8000

    def test_main_stdio_transport(self):
        mock_mcp = MagicMock()
        mock_mcp.settings = MagicMock()
        
        with patch("surfaces.server_start_handler.ServerStartHandler._setup_logging") as mock_setup_log, \
             patch("surfaces.server_instance_handler.ServerInstanceHandler.get_mcp_instance", return_value=mock_mcp) as mock_get_mcp, \
             patch("agent.server_bootstrap_manager.ServerBootstrapManager.resolve_transport_config", return_value=("stdio", "", "")):
            
            ServerStartHandler.main()
            mock_setup_log.assert_called_once()
            mock_get_mcp.assert_called_once()
            mock_mcp.run.assert_called_once_with()


class TestCliCommandHandlerExtended:
    """Extended tests for CliCommandHandler to close remaining coverage gaps."""

    def test_get_container_returns_when_not_none(self):
        """_get_container should return container when get_container() is not None."""
        mock_container = MagicMock()
        with patch("agent.agent_di_container.get_container", return_value=mock_container):
            container = CliCommandHandler._get_container()
            assert container is mock_container

    def test_main_action_not_found(self):
        """main() should return ExitCode(1) when action not in action map (lines 129-130)."""
        mock_args = MagicMock()
        mock_args.action = "nonexistent_action"
        mock_args.args = "{}"
        mock_args.log_level = "WARNING"
        mock_args.json_output = False

        with patch("argparse.ArgumentParser.parse_args", return_value=mock_args), \
             patch.object(CliCommandHandler, "build_action_map", return_value={"cleanup": MagicMock()}), \
             patch("sys.stdout.isatty", return_value=True):

            res = CliCommandHandler.main()
            assert res == ExitCode(1)

    def test_main_action_exception(self):
        """main() should return ExitCode(1) when action execution raises (lines 136-139)."""
        mock_args = MagicMock()
        mock_args.action = "cleanup"
        mock_args.args = "{}"
        mock_args.log_level = "WARNING"
        mock_args.json_output = False

        async def failing_action(**kwargs):
            raise RuntimeError("Blender crashed")

        with patch("argparse.ArgumentParser.parse_args", return_value=mock_args), \
             patch.object(CliCommandHandler, "build_action_map", return_value={"cleanup": failing_action}), \
             patch("sys.stdout.isatty", return_value=True):

            res = CliCommandHandler.main()
            assert res == ExitCode(1)


class TestServerInstanceHandlerExtended:
    """Extended tests for ServerInstanceHandler to close remaining coverage gaps."""

    @pytest.mark.asyncio
    async def test_server_lifespan_blender_returns_none(self):
        """When get_blender_connection returns falsy value (lines 67-68)."""
        mock_server = MagicMock()

        with patch("surfaces.server_instance_handler.record_startup") as mock_record, \
             patch("surfaces.server_instance_handler.get_blender_connection", return_value=None), \
             patch("surfaces.server_instance_handler.shutdown_connection") as mock_shutdown:

            async with ServerInstanceHandler.server_lifespan(mock_server) as startup_data:
                assert startup_data["blender_connected"] is False

            mock_shutdown.assert_called_once()

    @pytest.mark.asyncio
    async def test_server_lifespan_startup_exception(self):
        """When an exception occurs during startup (lines 76-78)."""
        mock_server = MagicMock()

        with patch("surfaces.server_instance_handler.record_startup", side_effect=RuntimeError("Critical failure")), \
             patch("surfaces.server_instance_handler.shutdown_connection"):

            async with ServerInstanceHandler.server_lifespan(mock_server) as startup_data:
                assert startup_data["blender_connected"] is False
                assert "startup_error" in startup_data

    @pytest.mark.asyncio
    async def test_server_lifespan_shutdown_error(self):
        """When shutdown_connection raises (lines 83-84)."""
        mock_server = MagicMock()

        with patch("surfaces.server_instance_handler.record_startup"), \
             patch("surfaces.server_instance_handler.get_blender_connection", return_value="mock_conn"), \
             patch("surfaces.server_instance_handler.shutdown_connection", side_effect=Exception("Shutdown failed")):

            async with ServerInstanceHandler.server_lifespan(mock_server) as startup_data:
                assert startup_data["blender_connected"] is True

    def test_get_mcp_instance_already_initialized(self):
        """When _mcp_instance is already set, return cached (line 100)."""
        mock_mcp = MagicMock()
        with patch("surfaces.server_instance_handler._mcp_instance", mock_mcp):
            res = ServerInstanceHandler.get_mcp_instance()
            assert res is mock_mcp


class TestCatalogCommandHandler:
    """Tests for CatalogCommandHandler to cover missing lines."""

    def test_list_commands_with_domain(self):
        """list_commands with domain filter should return filtered results (lines 63-64)."""
        from surfaces.catalog_command_handler import CommandCatalogSurfaceHandler
        from taxonomy import DomainRef

        result = CommandCatalogSurfaceHandler.list_commands(DomainRef("scene"))
        assert len(result) > 0
        assert isinstance(result, list)

    def test_list_commands_without_domain(self):
        """list_commands without domain should return all commands."""
        from surfaces.catalog_command_handler import CommandCatalogSurfaceHandler

        result = CommandCatalogSurfaceHandler.list_commands()
        assert len(result) > 0


class TestSystemPromptManager:
    """Tests for SystemPromptManager prompt string functions."""

    def test_get_lighting_expert_prompt(self):
        from agent.system_prompt_manager import SystemPromptManager
        result = SystemPromptManager.get_lighting_expert_prompt()
        assert isinstance(result, str)
        assert len(result) > 10

    def test_get_layout_expert_prompt(self):
        from agent.system_prompt_manager import SystemPromptManager
        result = SystemPromptManager.get_layout_expert_prompt()
        assert isinstance(result, str)
        assert len(result) > 10

    def test_get_text_to_scene_orchestrator_prompt(self):
        from agent.system_prompt_manager import SystemPromptManager
        result = SystemPromptManager.get_text_to_scene_orchestrator_prompt()
        assert isinstance(result, str)
        assert len(result) > 10
