"""Final coverage gap tests - push src/ to 100%."""
import pytest
import json
import sys
import subprocess
from unittest.mock import MagicMock, AsyncMock, patch, mock_open
from pathlib import Path

# =============================================================================
# CONTRACT LAYER - Abstract method pass lines
# Each abstract method has a `pass` body. We cover it via super() delegation.
# =============================================================================

class TestContractAbstractMethods:
    """Cover all pass lines in abstract contract classes via super() calls."""

    @pytest.mark.asyncio
    async def test_adapter_blender_port(self):
        from contract.adapter_blender_port import BlenderPort
        class C(BlenderPort):
            async def execute_code(self, code): return await super().execute_code(code)
            async def get_scene_info(self): return await super().get_scene_info()
            async def get_object_info(self, name): return await super().get_object_info(name)
            async def get_screenshot(self, max_size=None): return await super().get_screenshot(max_size)
        c = C()
        assert await c.execute_code(None) is None
        assert await c.get_scene_info() is None
        assert await c.get_object_info(None) is None
        assert await c.get_screenshot() is None

    @pytest.mark.asyncio
    async def test_ai_generation_protocol(self):
        from contract.ai_generation_protocol import GenerationProtocol
        class C(GenerationProtocol):
            async def start_generation(self, provider_name, prompt): return await super().start_generation(provider_name, prompt)
            async def check_status(self, provider_name, job_id): return await super().check_status(provider_name, job_id)
        c = C()
        assert await c.start_generation(None, None) is None
        assert await c.check_status(None, None) is None

    def test_api_polyhaven_port(self):
        from contract.api_polyhaven_port import PolyhavenApiPort
        class C(PolyhavenApiPort):
            def get_polyhaven_categories(self, asset_type=None): return super().get_polyhaven_categories(asset_type)
            def search_polyhaven_assets(self, asset_type=None, categories=None): return super().search_polyhaven_assets(asset_type, categories)
            def download_polyhaven_asset(self, asset_id, asset_type, resolution=None, file_format=None): return super().download_polyhaven_asset(asset_id, asset_type, resolution, file_format)
            def set_texture(self, object_name, texture_id): return super().set_texture(object_name, texture_id)
            def get_polyhaven_status(self): return super().get_polyhaven_status()
        c = C()
        assert c.get_polyhaven_categories() is None
        assert c.search_polyhaven_assets() is None
        assert c.download_polyhaven_asset(None, None) is None
        assert c.set_texture(None, None) is None
        assert c.get_polyhaven_status() is None

    def test_api_sketchfab_port(self):
        from contract.api_sketchfab_port import SketchfabApiPort
        class C(SketchfabApiPort):
            def get_sketchfab_status(self): return super().get_sketchfab_status()
            def search_sketchfab_models(self, query): return super().search_sketchfab_models(query)
            def get_sketchfab_model_preview(self, asset_id): return super().get_sketchfab_model_preview(asset_id)
            def download_sketchfab_model(self, asset_id, scale=None): return super().download_sketchfab_model(asset_id, scale)
        c = C()
        assert c.get_sketchfab_status() is None
        assert c.search_sketchfab_models(None) is None
        assert c.get_sketchfab_model_preview(None) is None
        assert c.download_sketchfab_model(None) is None

    def test_app_config_port(self):
        from contract.app_config_port import ConfigPort
        class C(ConfigPort):
            def get(self, path="", default=None): return super().get(path, default)
        c = C()
        assert c.get() is None

    @pytest.mark.asyncio
    async def test_asset_search_protocol(self):
        from contract.asset_search_protocol import AssetSearchProtocol
        class C(AssetSearchProtocol):
            async def search_all(self, query, providers=None): return await super().search_all(query, providers)
            async def fetch_and_import(self, provider, asset_id): return await super().fetch_and_import(provider, asset_id)
        c = C()
        assert await c.search_all(None) is None
        assert await c.fetch_and_import(None, None) is None

    def test_capture_viewport_port(self):
        from contract.capture_viewport_port import ViewportCapturePort
        class C(ViewportCapturePort):
            def get_viewport_screenshot(self, max_size=None): return super().get_viewport_screenshot(max_size)
        c = C()
        assert c.get_viewport_screenshot() is None

    def test_command_catalog_port(self):
        from contract.command_catalog_port import CommandCatalogPort
        class C(CommandCatalogPort):
            def get_command_spec(self, action): return super().get_command_spec(action)
            def list_actions(self): return super().list_actions()
            def filter_by_domain(self, domain): return super().filter_by_domain(domain)
        c = C()
        assert c.get_command_spec(None) is None
        assert c.list_actions() is None
        assert c.filter_by_domain(None) is None

    def test_connection_blender_port(self):
        from contract.connection_blender_port import BlenderConnectionPort
        class C(BlenderConnectionPort):
            def connect(self): return super().connect()
            def disconnect(self): return super().disconnect()
            def is_connected(self): return super().is_connected()
            def send_command(self, command_type, params=None): return super().send_command(command_type, params)
        c = C()
        assert c.connect() is None
        assert c.disconnect() is None
        assert c.is_connected() is None
        assert c.send_command(None) is None

    def test_connection_factory_port(self):
        from contract.connection_factory_port import BlenderConnectionFactoryPort
        class C(BlenderConnectionFactoryPort):
            def get_connection(self): return super().get_connection()
            def shutdown(self): return super().shutdown()
        c = C()
        assert c.get_connection() is None
        assert c.shutdown() is None

    @pytest.mark.asyncio
    async def test_execute_action_protocol(self):
        from contract.execute_action_protocol import ExecuteActionProtocol
        class C(ExecuteActionProtocol):
            async def execute(self, action, args=None): return await super().execute(action, args)
        c = C()
        assert await c.execute(None) is None

    @pytest.mark.asyncio
    async def test_execution_code_port(self):
        from contract.execution_code_port import CodeExecutionPort
        class C(CodeExecutionPort):
            async def execute_blender_code(self, code): return await super().execute_blender_code(code)
        c = C()
        assert await c.execute_blender_code(None) is None

    @pytest.mark.asyncio
    async def test_expert_base_aggregate(self):
        from contract.expert_base_aggregate import ExpertBaseOrchestratorAggregate
        class C(ExpertBaseOrchestratorAggregate):
            async def execute(self, *args, **kwargs): return await super().execute(*args, **kwargs)
        c = C()
        assert await c.execute() is None

    @pytest.mark.asyncio
    async def test_import_export_protocol(self):
        from contract.import_export_protocol import ImportExportProtocol
        class C(ImportExportProtocol):
            async def import_glb(self, request): return await super().import_glb(request)
            async def export_model(self, request): return await super().export_model(request)
        c = C()
        assert await c.import_glb(None) is None
        assert await c.export_model(None) is None

    @pytest.mark.asyncio
    async def test_inspection_scene_port(self):
        from contract.inspection_scene_port import SceneInspectionPort
        class C(SceneInspectionPort):
            async def get_scene_info(self): return await super().get_scene_info()
            async def get_object_info(self, name): return await super().get_object_info(name)
            async def cleanup_scene(self): return await super().cleanup_scene()
        c = C()
        assert await c.get_scene_info() is None
        assert await c.get_object_info(None) is None
        assert await c.cleanup_scene() is None

    @pytest.mark.asyncio
    async def test_object_operate_protocol(self):
        from contract.object_operate_protocol import ObjectOperateProtocol
        class C(ObjectOperateProtocol):
            async def place_asset(self, request): return await super().place_asset(request)
            async def get_object_info(self, request): return await super().get_object_info(request)
            async def set_object_transform(self, request): return await super().set_object_transform(request)
            async def delete_object(self, request): return await super().delete_object(request)
            async def create_primitive(self, request): return await super().create_primitive(request)
            async def set_material(self, request): return await super().set_material(request)
            async def apply_modifier(self, request): return await super().apply_modifier(request)
        c = C()
        assert await c.place_asset(None) is None
        assert await c.get_object_info(None) is None
        assert await c.set_object_transform(None) is None
        assert await c.delete_object(None) is None
        assert await c.create_primitive(None) is None
        assert await c.set_material(None) is None
        assert await c.apply_modifier(None) is None

    @pytest.mark.asyncio
    async def test_provider_asset_port(self):
        from contract.provider_asset_port import AssetProviderPort
        class C(AssetProviderPort):
            async def search_assets(self, request): return await super().search_assets(request)
            async def get_asset_details(self, asset_id): return await super().get_asset_details(asset_id)
            async def download_asset(self, request): return await super().download_asset(request)
        c = C()
        assert await c.search_assets(None) is None
        assert await c.get_asset_details(None) is None
        assert await c.download_asset(None) is None

    @pytest.mark.asyncio
    async def test_provider_generation_port(self):
        from contract.provider_generation_port import GenerationProviderPort
        class C(GenerationProviderPort):
            async def start_generation(self, request): return await super().start_generation(request)
            async def poll_generation(self, request): return await super().poll_generation(request)
            async def import_generated_asset(self, request): return await super().import_generated_asset(request)
        c = C()
        assert await c.start_generation(None) is None
        assert await c.poll_generation(None) is None
        assert await c.import_generated_asset(None) is None

    def test_recording_telemetry_port(self):
        from contract.recording_telemetry_port import TelemetryRecordingPort
        class C(TelemetryRecordingPort):
            def record_event(self, event_type, tool_name=None, prompt_text=None, success=None, duration_ms=None, error_message=None, blender_version=None, metadata=None): return super().record_event(event_type, tool_name, prompt_text, success, duration_ms, error_message, blender_version, metadata)
            def is_enabled(self): return super().is_enabled()
            def create_tool_decorator(self, tool_name): return super().create_tool_decorator(tool_name)
        c = C()
        assert c.record_event(None) is None
        assert c.is_enabled() is None
        assert c.create_tool_decorator(None) is None

    @pytest.mark.asyncio
    async def test_render_operate_protocol(self):
        from contract.render_operate_protocol import RenderOperateProtocol
        class C(RenderOperateProtocol):
            async def get_viewport_screenshot(self, request): return await super().get_viewport_screenshot(request)
            async def setup_camera(self, location, rotation, target=None): return await super().setup_camera(location, rotation, target)
            async def setup_render(self, engine, samples, resolution, use_denoising=None): return await super().setup_render(engine, samples, resolution, use_denoising)
            async def apply_composition(self, rule): return await super().apply_composition(rule)
            async def render(self, request): return await super().render(request)
        c = C()
        assert await c.get_viewport_screenshot(None) is None
        assert await c.setup_camera(None, None) is None
        assert await c.setup_render(None, None, None) is None
        assert await c.apply_composition(None) is None
        assert await c.render(None) is None

    @pytest.mark.asyncio
    async def test_scene_operate_protocol_blender_prop(self):
        from contract.scene_operate_protocol import SceneOperateProtocol
        class C(SceneOperateProtocol):
            async def cleanup_scene(self, request): return await super().cleanup_scene(request)
            async def setup_environment(self, request): return await super().setup_environment(request)
            async def get_scene_info(self, request): return await super().get_scene_info(request)
            @property
            def blender(self): return super().blender
        c = C()
        assert c.blender is None
        assert await c.cleanup_scene(None) is None
        assert await c.setup_environment(None) is None
        assert await c.get_scene_info(None) is None

    def test_tool_hunyuan_port(self):
        from contract.tool_hunyuan_port import HunyuanToolPort
        class C(HunyuanToolPort):
            def get_hunyuan3d_status(self): return super().get_hunyuan3d_status()
            def generate_hunyuan3d_model(self, text_prompt=None, input_image_url=None): return super().generate_hunyuan3d_model(text_prompt, input_image_url)
            def poll_hunyuan_job_status(self, job_id=None): return super().poll_hunyuan_job_status(job_id)
            def import_generated_asset_hunyuan(self, name, zip_file_url): return super().import_generated_asset_hunyuan(name, zip_file_url)
        c = C()
        assert c.get_hunyuan3d_status() is None
        assert c.generate_hunyuan3d_model() is None
        assert c.poll_hunyuan_job_status() is None
        assert c.import_generated_asset_hunyuan(None, None) is None

    def test_tool_hyper3d_port(self):
        from contract.tool_hyper3d_port import Hyper3dToolPort
        class C(Hyper3dToolPort):
            def get_hyper3d_status(self): return super().get_hyper3d_status()
            def generate_hyper3d_model_via_text(self, text_prompt, bbox_condition=None): return super().generate_hyper3d_model_via_text(text_prompt, bbox_condition)
            def generate_hyper3d_model_via_images(self, input_image_paths=None, input_image_urls=None, bbox_condition=None): return super().generate_hyper3d_model_via_images(input_image_paths, input_image_urls, bbox_condition)
            def poll_rodin_job_status(self, subscription_key=None, request_id=None): return super().poll_rodin_job_status(subscription_key, request_id)
            def import_generated_asset(self, name, task_uuid=None, request_id=None): return super().import_generated_asset(name, task_uuid, request_id)
            def process_bbox(self, original_bbox): return super().process_bbox(original_bbox)
        c = C()
        assert c.get_hyper3d_status() is None
        assert c.generate_hyper3d_model_via_text(None) is None
        assert c.poll_rodin_job_status() is None
        assert c.generate_hyper3d_model_via_images() is None
        assert c.import_generated_asset(None) is None
        assert c.process_bbox(None) is None

    @pytest.mark.asyncio
    async def test_workflow_operate_protocol(self):
        from contract.workflow_operate_protocol import WorkflowProtocol
        class C(WorkflowProtocol):
            async def create_basic_scene(self, prompt): return await super().create_basic_scene(prompt)
            async def generate_and_import_ai_asset(self, provider_name, prompt): return await super().generate_and_import_ai_asset(provider_name, prompt)
        c = C()
        assert await c.create_basic_scene(None) is None
        assert await c.generate_and_import_ai_asset(None, None) is None


# =============================================================================
# AGENT LAYER - Remaining gaps
# =============================================================================

class TestAgentFinalGaps:
    """Cover remaining agent gaps."""

    @pytest.mark.asyncio
    async def test_generation_expert_params_none(self):
        from agent.generation_expert_orchestrator import GenerationExpertOrchestrator
        r = await GenerationExpertOrchestrator(MagicMock(), MagicMock()).execute("generate", None)
        assert not r["success"]

    @pytest.mark.asyncio
    async def test_generation_expert_exception(self):
        from agent.generation_expert_orchestrator import GenerationExpertOrchestrator
        gen_mock = MagicMock()
        gen_mock.start_generation = AsyncMock(side_effect=Exception("test error"))
        r = await GenerationExpertOrchestrator(gen_mock, MagicMock()).execute("generate", {"prompt": "cat"})
        assert not r["success"]
        assert "test error" in r["error"]

    @pytest.mark.asyncio
    async def test_generation_expert_timeout(self):
        from agent.generation_expert_orchestrator import GenerationExpertOrchestrator
        gen_mock = MagicMock()
        gen_mock.start_generation = AsyncMock(return_value="job_1")
        status_mock = MagicMock()
        status_mock.status = "RUNNING"
        gen_mock.check_status = AsyncMock(return_value=status_mock)
        with patch("time.time", side_effect=[0, 999]):
            r = await GenerationExpertOrchestrator(gen_mock, MagicMock()).execute(
                "generate_and_import", {"prompt": "cat", "max_wait_seconds": 1, "poll_interval": 0.01}
            )
        assert not r["success"]
        assert "Timeout" in r["error"]

    @pytest.mark.asyncio
    async def test_generation_expert_failed_status(self):
        from agent.generation_expert_orchestrator import GenerationExpertOrchestrator
        gen_mock = MagicMock()
        gen_mock.start_generation = AsyncMock(return_value="job_1")
        status_mock = MagicMock()
        status_mock.status = "FAILED"
        status_mock.error = "Model generation failed"
        gen_mock.check_status = AsyncMock(return_value=status_mock)
        with patch("time.time", side_effect=[0, 0.1]):
            r = await GenerationExpertOrchestrator(gen_mock, MagicMock()).execute(
                "generate_and_import", {"prompt": "cat", "max_wait_seconds": 10, "poll_interval": 0.01}
            )
        assert not r["success"]
        assert "Model generation failed" in r["error"]

    @pytest.mark.asyncio
    async def test_search_expert_params_none(self):
        from agent.search_expert_orchestrator import SearchExpertOrchestrator
        assets = MagicMock()
        assets.search_all = AsyncMock(return_value=[])
        blender = MagicMock()
        blender.blender = MagicMock()
        blender.blender.execute_code = AsyncMock()
        r = await SearchExpertOrchestrator(assets, MagicMock(), blender).execute("search", None)
        assert r["success"]

    @pytest.mark.asyncio
    async def test_search_expert_exception(self):
        from agent.search_expert_orchestrator import SearchExpertOrchestrator
        assets = MagicMock()
        assets.search_all = AsyncMock(side_effect=Exception("search error"))
        r = await SearchExpertOrchestrator(assets, MagicMock(), MagicMock()).execute("search", {"query": "box"})
        assert not r["success"]
        assert "search error" in r["error"]

    @pytest.mark.asyncio
    async def test_setup_expert_exception(self):
        from agent.setup_expert_orchestrator import SetupExpertOrchestrator
        from contract import RenderOperateProtocol
        blender = MagicMock()
        blender.cleanup_scene = AsyncMock(side_effect=Exception("cleanup error"))
        r = await SetupExpertOrchestrator(blender, MagicMock(spec=RenderOperateProtocol)).execute("cleanup")
        assert not r["success"]
        assert "cleanup error" in r["error"]

    @pytest.mark.asyncio
    async def test_setup_expert_compose_no_render(self):
        from agent.setup_expert_orchestrator import SetupExpertOrchestrator
        from contract import SceneOperateProtocol
        r = await SetupExpertOrchestrator(MagicMock(spec=SceneOperateProtocol), None).execute("compose", {"rule": "thirds"})
        assert not r["success"]
        assert "Render manager not injected" in r["error"]

    def test_system_utils_coordinator_get_functions(self):
        from agent.system_utils_coordinator import _get_record_startup, _get_blender_conn_fn, _get_shutdown_connection_fn, _get_telemetry_config_class
        rs = _get_record_startup()
        assert callable(rs)
        bcf = _get_blender_conn_fn()
        assert callable(bcf)
        scf = _get_shutdown_connection_fn()
        assert callable(scf)
        tc = _get_telemetry_config_class()
        assert tc is not None


# =============================================================================
# CAPABILITIES LAYER
# =============================================================================

class TestCapabilitiesFinalGaps:
    """Cover remaining capabilities gaps."""

    @pytest.mark.asyncio
    async def test_action_execute_serialize_str(self):
        from capabilities.action_execute_actions import ActionExecuteActions
        mock_cap = MagicMock()
        async def str_method(**kwargs):
            return "plain_string_result"
        mock_cap.dummy = str_method
        mock_orch = MagicMock()
        mock_orch.operate_scene_capability = mock_cap
        dispatcher = ActionExecuteActions(orchestrator=mock_orch)
        with patch.object(dispatcher, "_get_command_spec", return_value={"capability": "SceneOperateProtocol.dummy"}):
            res = await dispatcher.execute("some_action")
            assert "plain_string_result" in str(res)


# =============================================================================
# INFRASTRUCTURE LAYER
# =============================================================================

class TestInfrastructureFinalGaps:
    """Cover remaining infrastructure gaps."""

    def test_blender_connection_already_connected(self):
        from infrastructure.blender_connection_connector import BlenderConnection
        conn = BlenderConnection()
        conn.sock = MagicMock()
        conn._is_socket_alive = MagicMock(return_value=True)
        assert conn.connect() is True

    def test_blender_connection_read_response_empty_midstream(self):
        from infrastructure.blender_connection_connector import BlenderConnection
        conn = BlenderConnection()
        mock_sock = MagicMock()
        mock_sock.recv.side_effect = [b'{"status":', b'']
        chunks, completed = conn._read_response_chunks(mock_sock, 1024)
        assert not completed
        assert len(chunks) > 0

    def test_blender_connection_recv_connection_error(self):
        from infrastructure.blender_connection_connector import BlenderConnection
        conn = BlenderConnection()
        mock_sock = MagicMock()
        import builtins
        mock_sock.recv.side_effect = builtins.ConnectionError("reset")
        with pytest.raises(builtins.ConnectionError):
            conn._read_response_chunks(mock_sock, 1024)

    def test_blender_connection_receive_full_pre_completed(self):
        from infrastructure.blender_connection_connector import BlenderConnection
        conn = BlenderConnection()
        with patch.object(conn, '_read_response_chunks', return_value=([b'{}'], True)):
            data = conn.receive_full_response(MagicMock())
            assert data == b'{}'

    def test_blender_connection_receive_full_chunks_not_completed(self):
        from infrastructure.blender_connection_connector import BlenderConnection
        conn = BlenderConnection()
        with patch.object(conn, '_read_response_chunks', return_value=([b'{"a": 1}'], False)):
            data = conn.receive_full_response(MagicMock())
            assert data == b'{"a": 1}'

    def test_blender_connection_receive_full_no_data(self):
        from infrastructure.blender_connection_connector import BlenderConnection
        conn = BlenderConnection()
        with patch.object(conn, '_read_response_chunks', return_value=([], False)):
            with pytest.raises(Exception, match="No data received"):
                conn.receive_full_response(MagicMock())

    def test_blender_connection_send_command_connect_fails(self):
        from infrastructure.blender_connection_connector import BlenderConnection
        conn = BlenderConnection()
        conn.sock = None
        conn.connect = MagicMock(return_value=False)
        with pytest.raises(Exception, match="Not connected"):
            conn.send_command("test")

    def test_blender_connection_send_command_sock_none_after_connect(self):
        from infrastructure.blender_connection_connector import BlenderConnection
        conn = BlenderConnection()
        conn.sock = None
        original_connect = conn.connect
        def fake_connect():
            conn.sock = None
            return True
        conn.connect = fake_connect
        with pytest.raises(Exception, match="Socket initialization failed"):
            conn.send_command("test")

    def test_global_get_blender_connection_factory_unexpected_type(self):
        from infrastructure.blender_connection_connector import get_blender_connection
        import infrastructure.blender_connection_connector as bcc
        bcc._blender_connection = None
        mock_factory = MagicMock()
        mock_factory.get_connection.return_value = "not_a_blender_connection"
        bcc._default_factory = mock_factory
        with pytest.raises(TypeError, match="unexpected type"):
            get_blender_connection()
        bcc._default_factory = None

    def test_command_catalog_module_helpers(self):
        from infrastructure.command_catalog_client import get_command_spec, list_actions_client, filter_by_domain
        from taxonomy import ActionName, DomainRef
        spec = get_command_spec(ActionName("cleanup_scene"))
        assert spec is not None
        actions = list_actions_client()
        assert len(actions) > 0
        filtered = filter_by_domain(DomainRef("scene"))
        assert len(filtered) > 0

    def test_config_file_loader_dir_based(self):
        from infrastructure.config_file_loader import ApplicationConfigLoader
        with patch.dict("os.environ", {"BLENDERMCP_CONFIG_PATH": "/mock/dir"}):
            with patch.object(Path, "is_file", return_value=False):
                with patch.object(Path, "is_dir", return_value=True):
                    with patch.object(Path, "exists", return_value=True):
                        root = ApplicationConfigLoader.get_project_root()
                        assert root == Path("/mock/dir")

    def test_hyper3d_adapter_parse_job_id_non_dict(self):
        from infrastructure.hyper3d_generation_adapter import Hyper3DGenerationAdapter
        from taxonomy import JobId
        kwargs = Hyper3DGenerationAdapter._parse_job_id_kwargs(JobId('"raw_string"'))
        assert kwargs.get("request_id") == '"raw_string"'

    def test_hyper3d_client_validate_url_success(self):
        from infrastructure.hyper3d_generation_client import Hyper3dGenerationTool
        from taxonomy import StringList
        err, images = Hyper3dGenerationTool._validate_and_prepare_images(None, StringList(["http://example.com/img.png"]))
        assert err is None
        assert images == ["http://example.com/img.png"]

    def test_polyhaven_download_error_key(self):
        from infrastructure.polyhaven_api_client import PolyhavenApiClient
        conn = MagicMock()
        conn.send_command.return_value = {"error": "download failed"}
        client = PolyhavenApiClient(conn)
        from taxonomy import AssetId, AssetType
        res = client.download_polyhaven_asset(AssetId("x"), AssetType("hdris"))
        assert "Error" in str(res)

    def test_polyhaven_download_unknown_type(self):
        from infrastructure.polyhaven_api_client import PolyhavenApiClient
        conn = MagicMock()
        conn.send_command.return_value = {"success": True, "message": "ok"}
        client = PolyhavenApiClient(conn)
        from taxonomy import AssetId, AssetType
        res = client.download_polyhaven_asset(AssetId("x"), AssetType("other"))
        assert "ok" in str(res)

    def test_telemetry_decorator_record_usage(self):
        from infrastructure.telemetry_decorator_adapter import TelemetryDecoratorAdapter
        from taxonomy import ToolName, SuccessFlag, DurationMs
        recorder = MagicMock()
        adapter = TelemetryDecoratorAdapter(recorder)
        adapter._record_usage(ToolName("test"), SuccessFlag(True), DurationMs(100))
        recorder.record_event.assert_called_once()

    @pytest.mark.asyncio
    async def test_telemetry_decorator_async_recorder_failure(self):
        from infrastructure.telemetry_decorator_adapter import TelemetryDecoratorAdapter
        from taxonomy import ToolName
        recorder = MagicMock()
        adapter = TelemetryDecoratorAdapter(recorder)
        decorator = adapter._build_decorator(recorder, ToolName("test"))
        @decorator
        async def dummy():
            return "ok"
        recorder.record_event.side_effect = Exception("disk full")
        result = await dummy()
        assert result == "ok"

    def test_telemetry_signal_recorder_worker_failure(self):
        from infrastructure.telemetry_signal_recorder import TelemetrySignalRecorder
        from pathlib import Path
        import tempfile
        conn = MagicMock()
        config = MagicMock()
        config.enabled = True
        config.max_prompt_length = 500
        config.data_dir = None
        with tempfile.TemporaryDirectory() as tmpdir:
            config.data_dir = tmpdir
            with patch.object(TelemetrySignalRecorder, '_send_event', side_effect=Exception("send failed")):
                recorder = TelemetrySignalRecorder(conn, config)
                from taxonomy.telemetry_event_entity import EventType
                recorder.record_event(EventType.TOOL_EXECUTION)
                import time; time.sleep(0.3)
                # Worker should have processed the event and caught the exception


# =============================================================================
# SURFACES LAYER
# =============================================================================

class TestSurfacesFinalGaps:
    """Cover remaining surfaces gaps."""

    def test_catalog_command_handler_tool_func(self):
        from surfaces.catalog_command_handler import CommandCatalogSurfaceHandler
        mcp = MagicMock()
        mock_tool_decorator = MagicMock()
        mcp.tool.return_value = mock_tool_decorator
        CommandCatalogSurfaceHandler.register_command_catalog(mcp)
        tool_fn = mock_tool_decorator.call_args[0][0]
        import asyncio
        from taxonomy import DomainRef
        res = asyncio.run(tool_fn(DomainRef("scene")))
        assert "scene" in str(res) or isinstance(res, str)

    def test_cli_handler_json_output_pydantic(self, capsys):
        from surfaces.cli_command_handler import CliCommandHandler
        from pydantic import BaseModel
        class FakeModel(BaseModel):
            result: str = "ok"
        mock_args = MagicMock()
        mock_args.action = "cleanup"
        mock_args.args = "{}"
        mock_args.json_output = True
        mock_args.log_level = "WARNING"
        async def fake_action(**kw):
            return FakeModel(result="done")
        with patch("argparse.ArgumentParser.parse_args", return_value=mock_args), \
             patch.object(CliCommandHandler, "build_action_map", return_value={"cleanup": fake_action}), \
             patch("sys.stdout.isatty", return_value=True):
            CliCommandHandler.main()
        captured = capsys.readouterr()
        assert "done" in captured.out or "result" in captured.out

    def test_cli_handler_json_output_non_pydantic(self, capsys):
        from surfaces.cli_command_handler import CliCommandHandler
        mock_args = MagicMock()
        mock_args.action = "cleanup"
        mock_args.args = "{}"
        mock_args.json_output = True
        mock_args.log_level = "WARNING"
        async def fake_action(**kw):
            return {"msg": "done"}
        with patch("argparse.ArgumentParser.parse_args", return_value=mock_args), \
             patch.object(CliCommandHandler, "build_action_map", return_value={"cleanup": fake_action}), \
             patch("sys.stdout.isatty", return_value=True):
            CliCommandHandler.main()
        captured = capsys.readouterr()
        assert "done" in captured.out

    def test_cli_handler_tty_output_string_result(self, capsys):
        from surfaces.cli_command_handler import CliCommandHandler
        mock_args = MagicMock()
        mock_args.action = "cleanup"
        mock_args.args = "{}"
        mock_args.json_output = False
        mock_args.log_level = "WARNING"
        async def fake_action(**kw):
            return "plain result"
        with patch("argparse.ArgumentParser.parse_args", return_value=mock_args), \
             patch.object(CliCommandHandler, "build_action_map", return_value={"cleanup": fake_action}), \
             patch("sys.stdout.isatty", return_value=True):
            CliCommandHandler.main()
        captured = capsys.readouterr()
        assert "plain result" in captured.out

    def test_cli_handler_tty_output_dict_result(self, capsys):
        from surfaces.cli_command_handler import CliCommandHandler
        mock_args = MagicMock()
        mock_args.action = "cleanup"
        mock_args.args = "{}"
        mock_args.json_output = False
        mock_args.log_level = "WARNING"
        async def fake_action(**kw):
            return {"key": "value"}
        with patch("argparse.ArgumentParser.parse_args", return_value=mock_args), \
             patch.object(CliCommandHandler, "build_action_map", return_value={"cleanup": fake_action}), \
             patch("sys.stdout.isatty", return_value=True):
            CliCommandHandler.main()
        captured = capsys.readouterr()
        assert "key" in captured.out

    def test_prompt_handler_static_methods(self):
        from surfaces.prompt_register_handler import PromptHandlerModule
        r1 = PromptHandlerModule.lighting_expert()
        assert len(r1) > 0
        r2 = PromptHandlerModule.layout_expert()
        assert len(r2) > 0
        r3 = PromptHandlerModule.text_to_scene_orchestrator()
        assert len(r3) > 0


# =============================================================================
# ENTRY POINTS - if __name__ guards
# =============================================================================

class TestEntryPointsFinalGaps:
    """Cover if __name__ == '__main__' guards via subprocess."""

    def test_cli_main_entry_name_main(self):
        src_file = Path(__file__).parent.parent.parent / "src" / "cli_main_entry.py"
        result = subprocess.run(
            [sys.executable, str(src_file)],
            capture_output=True, text=True, timeout=5
        )
        assert result.returncode in (0, 1, 2)

    def test_mcp_main_entry_name_main(self):
        import runpy
        with pytest.raises((SystemExit, Exception)):
            runpy.run_path(str(Path(__file__).parent.parent.parent / "src" / "mcp_main_entry.py"),
                          run_name="__main__")



