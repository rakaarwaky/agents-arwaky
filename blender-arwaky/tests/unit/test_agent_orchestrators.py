"""Unit tests for all agent orchestrators and expert agents."""
import pytest
from unittest.mock import MagicMock, AsyncMock, patch, mock_open
import os
import json

from taxonomy import (
    Prompt, JobId, ProviderName, ActionName, Details,
    DomainRef, FormatRef, SkillName, SectionRef,
    SearchQuery, AssetId, CoordinateList, RotationVector,
    RenderEngine, RenderSamples, RuleName, HdriId,
    BlenderVersion, ErrorMessage
)
from contract import (
    AgentDiContainerAggregate,
    ExpertBaseOrchestratorAggregate,
    SceneOperateProtocol,
    RenderOperateProtocol,
    GenerationProtocol,
    AssetSearchProtocol
)
from agent.core_agent_orchestrator import CoreAgentOrchestrator
from agent.expert_base_orchestrator import ExpertBaseOrchestrator
from agent.workflow_agent_orchestrator import WorkflowAgentOrchestrator
from agent.setup_expert_orchestrator import SetupExpertOrchestrator
from agent.generation_expert_orchestrator import GenerationExpertOrchestrator
from agent.search_expert_orchestrator import SearchExpertOrchestrator
from agent.refinement_expert_orchestrator import RefinementExpertOrchestrator
from agent.system_utils_coordinator import SystemUtilsCoordinator


class TestCoreAgentOrchestrator:
    """Tests for CoreAgentOrchestrator."""

    @pytest.fixture
    def mock_container(self):
        container = MagicMock(spec=AgentDiContainerAggregate)
        container.code_executor = MagicMock()
        container.action_execute_capability = MagicMock()
        container.command_catalog = MagicMock()
        container.generate_ai_capability = MagicMock()
        return container

    @pytest.mark.asyncio
    async def test_execute_code(self, mock_container):
        orchestrator = CoreAgentOrchestrator(mock_container)
        mock_container.code_executor.execute_blender_code = AsyncMock(return_value="executed_successfully")
        
        req = MagicMock()
        req.code = "print('hello')"
        res = await orchestrator.execute_code(req)
        assert res == {"success": True, "result": "executed_successfully"}
        mock_container.code_executor.execute_blender_code.assert_called_with("print('hello')")

    @pytest.mark.asyncio
    async def test_execute_action(self, mock_container):
        orchestrator = CoreAgentOrchestrator(mock_container)
        mock_container.action_execute_capability.execute = AsyncMock(return_value="done")
        
        res = await orchestrator.execute_action(ActionName("cleanup"), {"force": True})
        assert res == Prompt("done")
        mock_container.action_execute_capability.execute.assert_called_with(ActionName("cleanup"), {"force": True})

    def test_list_commands(self, mock_container):
        orchestrator = CoreAgentOrchestrator(mock_container)
        mock_catalog = mock_container.command_catalog
        mock_catalog.list_actions.return_value = ["clean", "render"]
        mock_catalog.get_command_spec.side_effect = lambda a: {"description": f"{a} desc", "domain": "scene"}
        
        # 1. Default (detailed format, all domains)
        res = orchestrator.list_commands()
        data = json.loads(str(res))
        assert "clean" in data
        assert data["clean"]["description"] == "clean desc"

        # 2. Filter by domain
        mock_catalog.filter_by_domain.return_value = {"clean": {"description": "clean desc", "domain": "scene"}}
        res = orchestrator.list_commands(domain=DomainRef("scene"))
        data = json.loads(str(res))
        assert "clean" in data
        mock_catalog.filter_by_domain.assert_called_with(DomainRef("scene"))

        # 3. Format: summary
        res = orchestrator.list_commands(format=FormatRef("summary"))
        data = json.loads(str(res))
        assert "clean" in data
        assert "description" in data["clean"]

    @pytest.mark.asyncio
    async def test_check_status(self, mock_container):
        orchestrator = CoreAgentOrchestrator(mock_container)
        mock_gen = mock_container.generate_ai_capability
        mock_status = MagicMock()
        mock_status.status = "COMPLETED"
        mock_gen.check_status = AsyncMock(return_value=mock_status)

        res = await orchestrator.check_status(ProviderName("hunyuan"), JobId("job_123"))
        data = json.loads(str(res))
        assert data["success"] is True
        assert data["status"] == "COMPLETED"
        mock_gen.check_status.assert_called_with(ProviderName("hunyuan"), JobId("job_123"))

    def test_health_check(self, mock_container):
        orchestrator = CoreAgentOrchestrator(mock_container)
        with patch("agent.system_utils_coordinator.health_check", return_value={"status": "healthy"}):
            res = orchestrator.health_check()
            data = json.loads(str(res))
            assert data["status"] == "healthy"

    def test_read_skill_context(self, mock_container):
        orchestrator = CoreAgentOrchestrator(mock_container)
        
        # SKILL.md not found path
        with patch("os.path.isfile", return_value=False):
            res = orchestrator.read_skill_context(SkillName("dummy"))
            assert "not found in project root" in str(res)

        # SKILL.md found and read section path
        with patch("os.path.isfile", return_value=True):
            dummy_content = "## section1\nThis is section 1 info.\n## section2\nThis is section 2 info."
            with patch("builtins.open", mock_open(read_data=dummy_content)):
                # Whole file
                res_all = orchestrator.read_skill_context(SkillName("dummy"))
                assert str(res_all) == dummy_content

                # specific section
                res_sec = orchestrator.read_skill_context(SkillName("dummy"), SectionRef("section1"))
                assert "This is section 1 info." in str(res_sec)
                assert "section2" not in str(res_sec)

                # section not found
                res_missing = orchestrator.read_skill_context(SkillName("dummy"), SectionRef("missing"))
                assert "Section 'missing' not found" in str(res_missing)


class TestExpertBaseOrchestrator:
    """Tests for ExpertBaseOrchestrator."""

    @pytest.mark.asyncio
    async def test_execute(self):
        orchestrator = ExpertBaseOrchestrator()
        res = await orchestrator.execute()
        assert res == {"success": True, "message": "Base expert execution"}


class TestWorkflowAgentOrchestrator:
    """Tests for WorkflowAgentOrchestrator."""

    @pytest.fixture
    def mock_experts(self):
        return {
            "scene": MagicMock(spec=ExpertBaseOrchestratorAggregate),
            "asset": MagicMock(spec=ExpertBaseOrchestratorAggregate),
            "generation": MagicMock(spec=ExpertBaseOrchestratorAggregate),
            "refinement": MagicMock(spec=ExpertBaseOrchestratorAggregate),
        }

    @pytest.mark.asyncio
    async def test_create_scene_from_prompt(self, mock_experts):
        orchestrator = WorkflowAgentOrchestrator(
            scene_expert=mock_experts["scene"],
            asset_expert=mock_experts["asset"],
            generation_expert=mock_experts["generation"],
            refinement_expert=mock_experts["refinement"]
        )

        mock_experts["scene"].execute = AsyncMock()
        mock_experts["scene"].execute.side_effect = [
            {"success": True}, # cleanup
            {"success": True}, # setup_environment
            {"success": True}, # setup_camera
            {"success": True}, # setup_render
            {"success": True, "objects": []}, # info
        ]
        mock_experts["asset"].execute.return_value = {"success": True, "assets": [{"id": "asset_1"}]}

        res = await orchestrator.create_scene_from_prompt("vintage room")
        assert res["success"] is True
        assert len(res["steps"]) == 5

    @pytest.mark.asyncio
    async def test_run_autonomous_refinement(self, mock_experts):
        orchestrator = WorkflowAgentOrchestrator(
            scene_expert=mock_experts["scene"],
            asset_expert=mock_experts["asset"],
            generation_expert=mock_experts["generation"],
            refinement_expert=mock_experts["refinement"]
        )
        mock_experts["refinement"].execute = AsyncMock(return_value={"success": True, "message": "refined"})
        res = await orchestrator.run_autonomous_refinement("perfect model")
        assert res == {"success": True, "message": "refined"}

    @pytest.mark.asyncio
    async def test_get_expert_status(self, mock_experts):
        orchestrator = WorkflowAgentOrchestrator(
            scene_expert=mock_experts["scene"],
            asset_expert=mock_experts["asset"],
            generation_expert=mock_experts["generation"],
            refinement_expert=mock_experts["refinement"]
        )
        status = await orchestrator.get_expert_status()
        assert status == {
            "tool_scene_ops": "initialized",
            "asset": "initialized",
            "generation": "initialized",
            "refinement": "initialized"
        }


class TestSetupExpertOrchestrator:
    """Tests for SetupExpertOrchestrator."""

    @pytest.fixture
    def mock_blender(self):
        return MagicMock(spec=SceneOperateProtocol)

    @pytest.fixture
    def mock_render(self):
        return MagicMock(spec=RenderOperateProtocol)

    @pytest.mark.asyncio
    async def test_execute_actions(self, mock_blender, mock_render):
        orchestrator = SetupExpertOrchestrator(mock_blender, mock_render)

        # 1. cleanup
        mock_blender.cleanup_scene = AsyncMock()
        res = await orchestrator.execute("cleanup")
        assert res["success"] is True
        mock_blender.cleanup_scene.assert_called_once()

        # 2. info
        mock_blender.get_scene_info = AsyncMock(return_value={"objects": []})
        res = await orchestrator.execute("info")
        assert res == {"success": True, "tool_scene_ops": {"objects": []}}
        mock_blender.get_scene_info.assert_called_once()

        # 3. setup_camera
        mock_render.setup_camera = AsyncMock()
        res = await orchestrator.execute("setup_camera", {"location": [1.0, 2.0, 3.0], "rotation": [0.0, 0.0, 0.0]})
        assert res["success"] is True
        mock_render.setup_camera.assert_called_once()

        # 4. setup_render
        mock_render.setup_render = AsyncMock()
        res = await orchestrator.execute("setup_render", {"engine": "CYCLES", "samples": 64})
        assert res["success"] is True
        mock_render.setup_render.assert_called_once()

        # 5. compose
        mock_render.apply_composition = AsyncMock()
        res = await orchestrator.execute("compose", {"rule": "golden"})
        assert res["success"] is True
        mock_render.apply_composition.assert_called_with(RuleName("golden"))

        # 6. setup_environment
        mock_blender.setup_environment = AsyncMock()
        res = await orchestrator.execute("setup_environment", {"hdri_name": "sky"})
        assert res["success"] is True
        mock_blender.setup_environment.assert_called_once()

        # 7. Unknown action
        res = await orchestrator.execute("unknown")
        assert res["success"] is False
        assert "Unknown action" in res["error"]

    @pytest.mark.asyncio
    async def test_render_not_injected(self, mock_blender):
        orchestrator = SetupExpertOrchestrator(mock_blender, None)
        res = await orchestrator.execute("setup_camera")
        assert res["success"] is False
        assert "Render manager not injected" in res["error"]


class TestGenerationExpertOrchestrator:
    """Tests for GenerationExpertOrchestrator."""

    @pytest.fixture
    def mock_gen(self):
        return MagicMock(spec=GenerationProtocol)

    @pytest.fixture
    def mock_blender(self):
        return MagicMock(spec=SceneOperateProtocol)

    @pytest.mark.asyncio
    async def test_execute_actions(self, mock_gen, mock_blender):
        orchestrator = GenerationExpertOrchestrator(mock_gen, mock_blender)

        # 1. generate
        mock_gen.start_generation = AsyncMock(return_value="job_abc")
        res = await orchestrator.execute("generate", {"prompt": "cat"})
        assert res["success"] is True
        assert res["job_id"] == "job_abc"

        # 2. poll
        mock_status = MagicMock()
        mock_status.status = "COMPLETED"
        mock_status.result_url = "http://my_asset.glb"
        mock_gen.check_status = AsyncMock(return_value=mock_status)
        res = await orchestrator.execute("poll", {"provider": "hyper3d", "job_id": "job_abc"})
        assert res["success"] is True
        assert res["status"] == "COMPLETED"
        assert res["result_url"] == "http://my_asset.glb"

        # 3. generate_and_import success
        mock_gen.start_generation = AsyncMock(return_value="job_xyz")
        res = await orchestrator.execute("generate_and_import", {"prompt": "dog", "max_wait_seconds": 5, "poll_interval": 0.01})
        assert res["success"] is True
        assert res["job_id"] == "job_xyz"


class TestSearchExpertOrchestrator:
    """Tests for SearchExpertOrchestrator."""

    @pytest.fixture
    def mock_assets(self):
        return MagicMock(spec=AssetSearchProtocol)

    @pytest.fixture
    def mock_gen(self):
        return MagicMock(spec=GenerationProtocol)

    @pytest.fixture
    def mock_blender(self):
        return MagicMock(spec=SceneOperateProtocol)

    @pytest.mark.asyncio
    async def test_execute_actions(self, mock_assets, mock_gen, mock_blender):
        orchestrator = SearchExpertOrchestrator(mock_assets, mock_gen, mock_blender)

        # 1. search
        asset_mock = MagicMock()
        asset_mock.id = AssetId("asset_id")
        asset_mock.name = "box"
        asset_mock.provider = "polyhaven"
        asset_mock.type = "model"
        asset_mock.thumbnail_url = "thumb"
        mock_assets.search_all = AsyncMock(return_value=[asset_mock])
        res = await orchestrator.execute("search", {"query": "box", "providers": ["polyhaven"]})
        assert res["success"] is True
        assert res["count"] == 1

        # 2. import
        imported_mock = MagicMock()
        imported_mock.id = AssetId("asset_id")
        imported_mock.name = "box"
        imported_mock.blender_id = "box_blender"
        mock_assets.fetch_and_import = AsyncMock(return_value=imported_mock)
        res = await orchestrator.execute("import", {"provider": "polyhaven", "asset_id": "asset_id"})
        assert res["success"] is True
        assert res["asset"]["blender_id"] == "box_blender"

        # 3. place
        mock_blender.blender = MagicMock()
        mock_blender.blender.execute_code = AsyncMock(return_value="done")
        res = await orchestrator.execute("place", {"asset_id": "asset_id", "location": [0.0, 1.0, 2.0]})
        assert res["success"] is True

        # 4. generate_if_missing (found path)
        res = await orchestrator.execute("generate_if_missing", {"query": "box"})
        assert res["success"] is True
        assert res["action"] == "search_found"

        # 5. generate_if_missing (not found -> generate path)
        mock_assets.search_all = AsyncMock(return_value=[])
        mock_gen.start_generation = AsyncMock(return_value="job_id")
        res = await orchestrator.execute("generate_if_missing", {"query": "alien", "ai_provider": "hunyuan"})
        assert res["success"] is True
        assert res["action"] == "generation_started"
        assert res["job_id"] == "job_id"


class TestRefinementExpertOrchestrator:
    """Tests for RefinementExpertOrchestrator."""

    @pytest.fixture
    def mock_scene(self):
        return MagicMock(spec=ExpertBaseOrchestratorAggregate)

    @pytest.fixture
    def mock_asset(self):
        return MagicMock(spec=ExpertBaseOrchestratorAggregate)

    @pytest.fixture
    def mock_gen(self):
        return MagicMock(spec=ExpertBaseOrchestratorAggregate)

    @pytest.mark.asyncio
    async def test_execute_actions(self, mock_scene, mock_asset, mock_gen):
        orchestrator = RefinementExpertOrchestrator(mock_scene, mock_asset, mock_gen)

        # 1. analyze_gaps
        mock_scene.execute = AsyncMock(return_value={"tool_scene_ops": {"objects": [{"name": "Cube"}]}})
        res = await orchestrator.execute("analyze_gaps")
        assert res["success"] is True
        assert res["analysis"]["object_count"] == 1

        # 2. refine_loop (with convergence object_count >= 2)
        mock_scene.execute = AsyncMock()
        mock_scene.execute.side_effect = [
            {"tool_scene_ops": {"objects": [{"name": "Cube"}, {"name": "Sphere"}]}}, # info
            {"success": True}, # setup_environment
            {"success": True}, # setup_camera
        ]
        res = await orchestrator.execute("refine_loop", {"objective": "perfect lighting", "max_iterations": 2})
        assert res["success"] is True
        assert res["iterations"] == 1


class TestSystemUtilsCoordinator:
    """Tests for SystemUtilsCoordinator."""

    def test_record_startup(self):
        with patch("agent.system_utils_coordinator._get_record_startup") as mock_get:
            mock_fn = MagicMock()
            mock_get.return_value = mock_fn
            SystemUtilsCoordinator.record_startup()
            mock_fn.assert_called_once()

    def test_get_blender_connection(self):
        with patch("agent.system_utils_coordinator._get_blender_conn_fn") as mock_get:
            mock_fn = MagicMock()
            mock_fn.return_value = "conn"
            mock_get.return_value = mock_fn
            res = SystemUtilsCoordinator.get_blender_connection()
            assert res == "conn"

    def test_shutdown_connection(self):
        with patch("agent.system_utils_coordinator._get_shutdown_connection_fn") as mock_get:
            mock_fn = MagicMock()
            mock_get.return_value = mock_fn
            SystemUtilsCoordinator.shutdown_connection()
            mock_fn.assert_called_once()

    def test_health_check(self):
        with patch("agent.system_utils_coordinator._get_blender_conn_fn") as mock_conn_fn:
            mock_conn_fn.return_value = MagicMock()
            
            with patch("agent.system_utils_coordinator._get_telemetry_config_class") as mock_cfg_cls:
                mock_cfg = MagicMock()
                mock_cfg.enabled = True
                mock_cfg_cls.return_value = MagicMock(return_value=mock_cfg)

                health = SystemUtilsCoordinator.health_check()
                assert health["blender_connected"] is True
                assert health["telemetry_enabled"] is True
                assert health["status"] == "healthy"
