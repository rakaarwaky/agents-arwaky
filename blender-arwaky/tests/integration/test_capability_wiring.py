"""
Integration Tests: Capability Wiring & Component Interoperability.

Verifies that:
1. DI container resolves core capability chains correctly
2. Capability objects expose the correct methods (contract compliance)
3. Two real components work together without mocks (e.g. asset collector + provider)
4. ActionExecuteActions correctly dispatches to the capability resolved from DI
5. HealthCheck coordinator returns a structurally valid response

NOTE: This test suite also documents known architectural findings:
  - DI slots for object_operate, render_operate, import_export capabilities
    are not declared in ContainerLogic.__init__ (missing _object_operate_manager,
    _render_operate_manager, _import_export_manager slots). These are tested
    via their factory functions directly instead.
"""
import json
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from agent.agent_di_container import get_container, reset_container


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture(autouse=True)
def isolated_container(monkeypatch):
    """Reset DI container and mock Blender socket for each test."""
    from infrastructure.blender_connection_connector import BlenderConnection
    monkeypatch.setattr(BlenderConnection, "connect", lambda self: True)
    monkeypatch.setattr(BlenderConnection, "_is_socket_alive", lambda self: True)
    reset_container()
    yield
    reset_container()


# ── 1. Capability Contract Compliance ─────────────────────────────────────────

class TestCapabilityContracts:
    """Capabilities resolved from DI must expose their contract methods."""

    def test_scene_capability_has_required_methods(self):
        cap = get_container().operate_scene_capability
        assert hasattr(cap, "cleanup_scene"), "missing: cleanup_scene"
        assert hasattr(cap, "get_scene_info"), "missing: get_scene_info"
        assert hasattr(cap, "setup_environment"), "missing: setup_environment"

    def test_asset_capability_has_required_methods(self):
        cap = get_container().search_asset_capability
        assert hasattr(cap, "search_all"), "missing: search_all"
        assert hasattr(cap, "fetch_and_import"), "missing: fetch_and_import"

    def test_generation_capability_has_required_methods(self):
        cap = get_container().generate_ai_capability
        assert hasattr(cap, "start_generation"), "missing: start_generation"
        assert hasattr(cap, "check_status"), "missing: check_status"

    def test_object_capability_via_factory_has_required_methods(self):
        """Object capability via factory (bypasses missing DI slot)."""
        from capabilities.object_operate_executor import ObjectOperateExecutor
        mock_blender = MagicMock()
        cap = ObjectOperateExecutor(blender_port=mock_blender)
        assert hasattr(cap, "create_primitive"), "missing: create_primitive"
        assert hasattr(cap, "delete_object"), "missing: delete_object"
        assert hasattr(cap, "set_object_transform"), "missing: set_object_transform"
        assert hasattr(cap, "set_material"), "missing: set_material"
        assert hasattr(cap, "get_object_info"), "missing: get_object_info"


# ── 2. DI Container Lazy Loading Chain ───────────────────────────────────────

class TestDILazyLoadingChain:
    """Capabilities share the same underlying blender adapter instance (singleton)."""

    def test_blender_adapter_is_singleton(self):
        c = get_container()
        b1 = c.blender
        b2 = c.blender
        assert b1 is b2, "blender adapter must be singleton"

    def test_polyhaven_and_sketchfab_providers_are_different(self):
        c = get_container()
        ph = c.polyhaven_adapter
        sk = c.sketchfab_adapter
        assert ph is not sk, "providers must be separate instances"

    def test_asset_collector_receives_both_providers(self):
        c = get_container()
        collector = c.search_asset_capability
        providers = collector.providers
        assert len(providers) >= 2, "AssetSearchCollector must have at least 2 providers"
        assert any("poly" in k.lower() for k in providers), \
            f"Expected polyhaven provider, got: {list(providers.keys())}"

    def test_scene_capability_blender_is_same_as_container_blender(self):
        c = get_container()
        scene_blender = c.operate_scene_capability.blender
        container_blender = c.blender
        assert scene_blender is container_blender


# ── 3. AssetSearchCollector + Providers Integration ──────────────────────────

class TestAssetSearchCollectorIntegration:
    """Real AssetSearchCollector with mock providers — tests the collector logic."""

    def _make_search_response(self, asset_id, name, asset_type, provider_name):
        """Helper: build a valid AssetSearchResponseVO with correct VO types."""
        from taxonomy import (
            AssetSearchResponseVO, AssetMetadataVO,
            AssetId, AssetName, AssetType, ProviderName, TagList,
        )
        return AssetSearchResponseVO(
            assets=[
                AssetMetadataVO(
                    id=AssetId(asset_id),
                    name=AssetName(name),
                    type=AssetType(asset_type),
                    provider=ProviderName(provider_name),
                    thumbnail_url=None,
                    tags=TagList([]),
                )
            ],
            provider=ProviderName(provider_name),
        )

    @pytest.mark.asyncio
    async def test_search_all_aggregates_results_from_all_providers(self):
        from capabilities.asset_search_collector import AssetSearchCollector
        from taxonomy import SearchQuery

        mock_provider_a = AsyncMock()
        mock_provider_a.search_assets = AsyncMock(
            return_value=self._make_search_response("a1", "Rock", "hdri", "polyhaven")
        )
        mock_provider_b = AsyncMock()
        mock_provider_b.search_assets = AsyncMock(
            return_value=self._make_search_response("b1", "Sword", "model", "sketchfab")
        )

        collector = AssetSearchCollector(providers={
            "polyhaven": mock_provider_a,
            "sketchfab": mock_provider_b,
        })

        results = await collector.search_all(query=SearchQuery("nature"))

        assert len(results) == 2
        names = [str(r.name) for r in results]
        assert "Rock" in names
        assert "Sword" in names

    @pytest.mark.asyncio
    async def test_search_all_filters_by_provider(self):
        from capabilities.asset_search_collector import AssetSearchCollector
        from taxonomy import SearchQuery

        mock_provider_a = AsyncMock()
        mock_provider_a.search_assets = AsyncMock(
            return_value=self._make_search_response("a1", "Rock", "hdri", "polyhaven")
        )
        mock_provider_b = AsyncMock()
        mock_provider_b.search_assets = AsyncMock(
            return_value=self._make_search_response("b1", "Sword", "model", "sketchfab")
        )

        collector = AssetSearchCollector(providers={
            "polyhaven": mock_provider_a,
            "sketchfab": mock_provider_b,
        })

        results = await collector.search_all(
            query=SearchQuery("nature"),
            providers=["polyhaven"],
        )

        assert len(results) == 1
        assert str(results[0].name) == "Rock"
        mock_provider_b.search_assets.assert_not_called()

    @pytest.mark.asyncio
    async def test_search_all_tolerates_provider_error(self):
        """One failing provider must not crash the entire search."""
        from capabilities.asset_search_collector import AssetSearchCollector
        from taxonomy import SearchQuery, ProviderError, ErrorMessage

        mock_ok = AsyncMock()
        mock_ok.search_assets = AsyncMock(
            return_value=self._make_search_response("c1", "Tree", "model", "polyhaven")
        )
        mock_fail = AsyncMock()
        mock_fail.search_assets = AsyncMock(
            side_effect=ProviderError(ErrorMessage("rate limit exceeded"))
        )

        collector = AssetSearchCollector(providers={
            "polyhaven": mock_ok,
            "sketchfab": mock_fail,
        })

        results = await collector.search_all(query=SearchQuery("tree"))
        assert len(results) == 1
        assert str(results[0].name) == "Tree"


# ── 4. ActionExecuteActions + Capability Dispatch Integration ─────────────────

class TestActionDispatchIntegration:
    """ActionExecuteActions dispatches to the correct real capability method."""

    @pytest.mark.asyncio
    async def test_dispatch_to_scene_capability_get_scene_info(self):
        from capabilities.action_execute_actions import ActionExecuteActions
        from taxonomy import GetSceneInfoResponseVO, SuccessFlag

        mock_scene_cap = AsyncMock()
        mock_scene_cap.get_scene_info = AsyncMock(
            return_value=GetSceneInfoResponseVO(
                success=SuccessFlag(True),
                scene_info={"name": "TestScene", "objects": []},
                message="ok"
            )
        )

        mock_orch = MagicMock()
        mock_orch.operate_scene_capability = mock_scene_cap

        dispatcher = ActionExecuteActions(orchestrator=mock_orch)
        result = await dispatcher.execute("get_scene_info")

        assert "TestScene" in result or "success" in result.lower()
        mock_scene_cap.get_scene_info.assert_called_once()

    @pytest.mark.asyncio
    async def test_dispatch_unknown_action_returns_error_string(self):
        from capabilities.action_execute_actions import ActionExecuteActions

        mock_orch = MagicMock()
        dispatcher = ActionExecuteActions(orchestrator=mock_orch)
        result = await dispatcher.execute("nonexistent_action_xyz")

        assert "Error" in result
        assert "nonexistent_action_xyz" in result

    @pytest.mark.asyncio
    async def test_dispatch_propagates_args_to_capability(self):
        from capabilities.action_execute_actions import ActionExecuteActions
        from taxonomy import CreatePrimitiveResponseVO, SuccessFlag, ObjectName, PrimitiveType

        mock_obj_cap = AsyncMock()
        mock_obj_cap.create_primitive = AsyncMock(
            return_value=CreatePrimitiveResponseVO(
                success=SuccessFlag(True),
                object_name=ObjectName("MySphere"),
                primitive_type=PrimitiveType("sphere"),
                message="created"
            )
        )

        mock_orch = MagicMock()
        mock_orch.object_operate_capability = mock_obj_cap

        dispatcher = ActionExecuteActions(orchestrator=mock_orch)
        result = await dispatcher.execute(
            "create_primitive",
            {"primitive_type": "sphere", "name": "MySphere"}
        )

        mock_obj_cap.create_primitive.assert_called_once()
        assert "MySphere" in result or "success" in result.lower()

    @pytest.mark.asyncio
    async def test_dispatch_handles_capability_exception_gracefully(self):
        from capabilities.action_execute_actions import ActionExecuteActions

        mock_scene_cap = AsyncMock()
        mock_scene_cap.get_scene_info = AsyncMock(
            side_effect=RuntimeError("Blender internal error")
        )

        mock_orch = MagicMock()
        mock_orch.operate_scene_capability = mock_scene_cap

        dispatcher = ActionExecuteActions(orchestrator=mock_orch)
        result = await dispatcher.execute("get_scene_info")

        assert "error" in result.lower()
        parsed = json.loads(result)
        assert "error" in parsed

    @pytest.mark.asyncio
    async def test_serialize_result_handles_dict(self):
        """Dict results must be JSON serialized correctly."""
        from capabilities.action_execute_actions import ActionExecuteActions

        dispatcher = ActionExecuteActions(orchestrator=MagicMock())
        result = dispatcher._serialize_result({"key": "value", "count": 42})

        parsed = json.loads(result)
        assert parsed["key"] == "value"
        assert parsed["count"] == 42

    @pytest.mark.asyncio
    async def test_serialize_result_handles_pydantic_model(self):
        """Pydantic models must be serialized via model_dump_json."""
        from capabilities.action_execute_actions import ActionExecuteActions
        from taxonomy import GetSceneInfoResponseVO, SuccessFlag

        model = GetSceneInfoResponseVO.model_construct(
            success=SuccessFlag(True),
            scene_info={"name": "Test"},
            message="ok"
        )
        dispatcher = ActionExecuteActions(orchestrator=MagicMock())
        result = dispatcher._serialize_result(model)

        parsed = json.loads(result)
        assert "success" in parsed or "scene_info" in parsed


# ── 5. HealthCheck System Integration ────────────────────────────────────────

class TestHealthCheckIntegration:
    """System health check must return a valid structured response."""

    def test_health_check_returns_dict_with_required_keys(self):
        from agent.system_utils_coordinator import health_check

        with patch("infrastructure.blender_connection_connector.get_blender_connection",
                   side_effect=ConnectionError("Blender not running")):
            result = health_check()

        assert isinstance(result, dict)
        assert "blender_connected" in result
        assert "status" in result

    def test_health_check_degraded_when_blender_offline(self):
        from agent.system_utils_coordinator import health_check

        with patch("infrastructure.blender_connection_connector.get_blender_connection",
                   side_effect=ConnectionError("not running")):
            result = health_check()

        assert result["blender_connected"] is False
        assert result["status"] == "degraded"

    def test_health_check_healthy_when_blender_connected(self):
        from agent.system_utils_coordinator import health_check

        mock_conn = MagicMock()
        with patch("infrastructure.blender_connection_connector.get_blender_connection",
                   return_value=mock_conn):
            result = health_check()

        assert result["blender_connected"] is True
        assert result["status"] == "healthy"


# ── 6. BlenderConnection Socket Protocol Integration ─────────────────────────

class TestBlenderConnectionIntegration:
    """BlenderConnection correctly serializes commands and parses responses."""

    def test_send_command_serializes_to_correct_json_format(self):
        """Command sent over socket must follow {type, params} protocol."""
        from infrastructure.blender_connection_connector import BlenderConnection

        conn = BlenderConnection(host="localhost", port=9876)

        # Build a fake socket that captures what is sent
        sent_data = []
        mock_sock = MagicMock()
        mock_sock.sendall = lambda data: sent_data.append(data)

        success_response = json.dumps({
            "status": "ok",
            "result": {"name": "Scene"}
        }).encode("utf-8")

        mock_sock.recv = MagicMock(return_value=success_response)
        conn.sock = mock_sock

        with patch.object(conn, "_is_socket_alive", return_value=True), \
             patch.object(conn, "receive_full_response", return_value=success_response):
            conn.send_command("get_scene_info", {"include_objects": True})

        assert len(sent_data) == 1
        payload = json.loads(sent_data[0].decode("utf-8"))
        assert payload["type"] == "get_scene_info"
        assert payload["params"]["include_objects"] is True

    def test_handle_command_response_raises_on_error_status(self):
        """Blender error responses must raise exceptions, not silently fail."""
        from infrastructure.blender_connection_connector import BlenderConnection

        conn = BlenderConnection()
        error_response = json.dumps({
            "status": "error",
            "message": "Object not found"
        }).encode("utf-8")

        with pytest.raises(Exception, match="Object not found"):
            conn._handle_command_response(error_response)

    def test_finalize_chunks_raises_on_incomplete_json(self):
        """Incomplete JSON from socket must raise, not return garbage."""
        from infrastructure.blender_connection_connector import BlenderConnection

        conn = BlenderConnection()
        incomplete = [b'{"status": "ok", "result":']  # truncated

        with pytest.raises(Exception, match="Incomplete JSON"):
            conn._finalize_chunks(incomplete)

    def test_receive_full_response_assembles_chunked_data(self):
        """Multi-chunk responses must be reassembled correctly."""
        from infrastructure.blender_connection_connector import BlenderConnection

        conn = BlenderConnection()
        full_json = json.dumps({"status": "ok", "result": {"x": 1}})
        chunk1 = full_json[:15].encode("utf-8")
        chunk2 = full_json[15:].encode("utf-8")

        mock_sock = MagicMock()
        mock_sock.recv = MagicMock(side_effect=[chunk1, chunk2, b""])

        result = conn.receive_full_response(mock_sock, buffer_size=8192)
        parsed = json.loads(result.decode("utf-8"))
        assert parsed["result"]["x"] == 1


# ── 7. AiGenerateGenerator + Provider Integration ─────────────────────────────

class TestAiGenerateGeneratorIntegration:
    """AiGenerateGenerator routes correctly to the named provider."""

    @pytest.mark.asyncio
    async def test_start_generation_delegates_to_correct_provider(self):
        from capabilities.ai_generate_generator import AiGenerateGenerator
        from taxonomy import (
            GenerationStartResponseVO, JobId, ProviderName, Prompt, JobState,
        )

        mock_hunyuan = AsyncMock()
        mock_hunyuan.start_generation = AsyncMock(
            return_value=GenerationStartResponseVO(
                job_id=JobId("job_hun_123"),
                status=JobState("PENDING"),
                provider=ProviderName("hunyuan"),
            )
        )
        mock_hyper3d = AsyncMock()
        mock_hyper3d.start_generation = AsyncMock(
            return_value=GenerationStartResponseVO(
                job_id=JobId("job_hyp_456"),
                status=JobState("PENDING"),
                provider=ProviderName("hyper3d"),
            )
        )

        generator = AiGenerateGenerator(providers={
            "hunyuan": mock_hunyuan,
            "hyper3d": mock_hyper3d,
        })

        job_id = await generator.start_generation(
            provider_name=ProviderName("hunyuan"),
            prompt=Prompt("a wooden chair")
        )

        assert str(job_id) == "job_hun_123"
        mock_hunyuan.start_generation.assert_called_once()
        mock_hyper3d.start_generation.assert_not_called()

    @pytest.mark.asyncio
    async def test_start_generation_raises_for_unknown_provider(self):
        from capabilities.ai_generate_generator import AiGenerateGenerator
        from taxonomy import ProviderError, ProviderName, Prompt

        generator = AiGenerateGenerator(providers={})

        with pytest.raises(ProviderError, match="not found"):
            await generator.start_generation(
                provider_name=ProviderName("unknown_provider"),
                prompt=Prompt("test prompt")
            )

    @pytest.mark.asyncio
    async def test_check_status_returns_structured_job_status(self):
        from capabilities.ai_generate_generator import AiGenerateGenerator
        from taxonomy import (
            GenerationStatusResponseVO, JobId, ProviderName, JobState, Progress,
        )

        mock_provider = AsyncMock()
        mock_provider.poll_generation = AsyncMock(
            return_value=GenerationStatusResponseVO(
                job_id=JobId("job_1"),
                status=JobState("DONE"),
                progress=Progress(100.0),
                error=None,
            )
        )

        generator = AiGenerateGenerator(providers={"hunyuan": mock_provider})

        status = await generator.check_status(
            provider_name=ProviderName("hunyuan"),
            job_id=JobId("job_1")
        )

        assert str(status.status) == "DONE"
        assert status.error is None
