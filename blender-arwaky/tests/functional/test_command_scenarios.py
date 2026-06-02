"""
Functional (Scenario) Tests: End-to-End Command Flows.

These tests simulate realistic user-facing workflows within project boundaries.
No real Blender is required — the Blender socket is mocked at the lowest level
(BlenderConnection.send_command), but everything above it (DI container, 
capabilities, orchestrator, action dispatcher) runs with REAL implementations.

Scenarios covered:
1.  list_commands → returns parseable JSON catalog
2.  execute_command("get_scene_info") → full stack, returns scene data
3.  execute_command("create_primitive") → full stack, constructs correct Blender code
4.  execute_command("delete_object") → full stack, sends delete command
5.  execute_command("set_object_transform") → location/rotation/scale passed correctly
6.  execute_command("set_material") → material assignment code emitted
7.  execute_command("search_assets") → multi-provider search returns merged list
8.  execute_command("unknown_action") → graceful error, no crash
9.  health_check() → structured response regardless of Blender state
10. execute_command with exception in capability → error JSON returned, no crash
11. execute_command("cleanup_scene") → select-all-delete code emitted
12. execute_command("get_object_info") → delegates to object capability
"""
import json
import pytest
from unittest.mock import AsyncMock, MagicMock

from agent.agent_di_container import get_container, reset_container
from taxonomy.blender_object_entity import BlenderObject
from taxonomy.core_types_vo import ObjectType


# ── Helpers & Fixtures ────────────────────────────────────────────────────────

def _make_blender_response(result: dict) -> dict:
    """Simulate a successful Blender socket response."""
    return result


@pytest.fixture(autouse=True)
def clean_container():
    """Reset DI container before/after each test."""
    reset_container()
    yield
    reset_container()


@pytest.fixture
def mock_blender_send(monkeypatch):
    """
    Patch BlenderConnection.send_command to avoid real socket connections.
    Returns a MagicMock so tests can configure return_value per scenario.
    """
    from infrastructure.blender_connection_connector import BlenderConnection

    mock_send = MagicMock(return_value={"name": "Scene", "objects": [], "frame": 1})
    monkeypatch.setattr(BlenderConnection, "send_command", mock_send)
    monkeypatch.setattr(BlenderConnection, "connect", lambda self: True)
    monkeypatch.setattr(BlenderConnection, "_is_socket_alive", lambda self: True)
    return mock_send


@pytest.fixture
def orchestrator(mock_blender_send):
    """Build a real core agent orchestrator from the (mocked socket) DI container."""
    container = get_container()
    return container.core_agent_orchestrator


# ── Scenario 1: list_commands ─────────────────────────────────────────────────

class TestScenarioListCommands:
    """User asks: 'what commands are available?'"""

    def test_list_commands_returns_valid_json(self, orchestrator):
        result = orchestrator.list_commands()
        parsed = json.loads(str(result))
        assert isinstance(parsed, dict)
        assert len(parsed) > 0

    def test_list_commands_each_entry_has_description(self, orchestrator):
        result = orchestrator.list_commands()
        catalog = json.loads(str(result))
        for action, spec in catalog.items():
            assert "description" in spec, f"Missing description for: {action}"

    def test_list_commands_summary_format_is_compact(self, orchestrator):
        from taxonomy import FormatRef
        result = orchestrator.list_commands(format=FormatRef("summary"))
        catalog = json.loads(str(result))
        for action, spec in catalog.items():
            # Summary format should NOT have full parameter spec
            assert isinstance(spec, dict)
            assert "description" in spec

    def test_list_commands_filter_by_domain(self, orchestrator):
        from taxonomy import DomainRef
        result = orchestrator.list_commands(domain=DomainRef("tool_scene_ops"))
        catalog = json.loads(str(result))
        # All returned actions must belong to the requested domain
        for action, spec in catalog.items():
            assert spec.get("domain") == "tool_scene_ops", (
                f"'{action}' has domain '{spec.get('domain')}', expected 'tool_scene_ops'"
            )


# ── Scenario 2: get_scene_info full stack ─────────────────────────────────────

class TestScenarioGetSceneInfo:
    """User asks: 'what objects are in the current scene?'"""

    @pytest.mark.asyncio
    async def test_execute_get_scene_info_returns_json_string(self, orchestrator, mock_blender_send):
        mock_blender_send.return_value = {
            "name": "MyScene",
            "object_count": 3,
            "objects": ["Cube", "Light", "Camera"],
            "frame_current": 1,
        }
        from taxonomy import ActionName
        result = await orchestrator.execute_action(ActionName("get_scene_info"))

        assert isinstance(str(result), str)
        parsed = json.loads(str(result))
        assert parsed is not None

    @pytest.mark.asyncio
    async def test_execute_get_scene_info_blender_was_called(self, orchestrator, mock_blender_send):
        mock_blender_send.return_value = {"objects": []}
        from taxonomy import ActionName, GetSceneInfoRequestVO
        await orchestrator.execute_action(ActionName("get_scene_info"), {"request": GetSceneInfoRequestVO()})
        # get_scene_info goes through the real DI container → must hit Blender
        assert mock_blender_send.called


# ── Scenario 3: create_primitive full stack ───────────────────────────────────

class TestScenarioCreatePrimitive:
    """User asks: 'create a sphere named MySphere at position (1, 2, 3)'
    
    NOTE: create_primitive uses ObjectOperateExecutor which is NOT wired via the
    normal DI container dispatch (missing DI slot). We test the capability
    directly to verify the code generation logic.
    """

    @pytest.mark.asyncio
    async def test_create_primitive_code_contains_sphere_op(self):
        """Direct capability test: sphere primitive generates correct bpy code."""
        from capabilities.object_operate_executor import ObjectOperateExecutor
        from taxonomy import CreatePrimitiveRequestVO, ObjectName, PrimitiveType

        mock_blender = MagicMock()
        mock_blender.execute_code = AsyncMock(return_value={})
        cap = ObjectOperateExecutor(blender_port=mock_blender)

        await cap.create_primitive(CreatePrimitiveRequestVO(
            primitive_type=PrimitiveType("sphere"),
            name=ObjectName("SphereObj"),
        ))

        sent_code = str(mock_blender.execute_code.call_args)
        assert "uv_sphere" in sent_code.lower() or "sphere" in sent_code.lower()

    @pytest.mark.asyncio
    async def test_create_primitive_result_is_success(self):
        """Direct capability test: result must indicate success."""
        from capabilities.object_operate_executor import ObjectOperateExecutor
        from taxonomy import CreatePrimitiveRequestVO, ObjectName, PrimitiveType, SuccessFlag

        mock_blender = MagicMock()
        mock_blender.execute_code = AsyncMock(return_value={})
        cap = ObjectOperateExecutor(blender_port=mock_blender)

        result = await cap.create_primitive(CreatePrimitiveRequestVO(
            primitive_type=PrimitiveType("cube"),
            name=ObjectName("MyCube"),
        ))

        assert result.success == SuccessFlag(True)
        assert str(result.object_name) == "MyCube"

    @pytest.mark.asyncio
    async def test_create_primitive_with_location(self):
        """Direct capability test: location is embedded in generated code."""
        from capabilities.object_operate_executor import ObjectOperateExecutor
        from taxonomy import CreatePrimitiveRequestVO, ObjectName, PrimitiveType, CoordinateList

        mock_blender = MagicMock()
        mock_blender.execute_code = AsyncMock(return_value={})
        cap = ObjectOperateExecutor(blender_port=mock_blender)

        await cap.create_primitive(CreatePrimitiveRequestVO(
            primitive_type=PrimitiveType("sphere"),
            name=ObjectName("LocSphere"),
            location=CoordinateList([5.0, 3.0, 1.0]),
        ))

        sent_code = str(mock_blender.execute_code.call_args)
        assert "5.0" in sent_code and "3.0" in sent_code


# ── Scenario 4: delete_object ─────────────────────────────────────────────────

class TestScenarioDeleteObject:
    """User asks: 'delete the object named OldMesh'
    
    NOTE: Tested via direct capability (ObjectOperateExecutor) due to
    missing DI slot for object_operate_capability in dispatch stack.
    """

    @pytest.mark.asyncio
    async def test_delete_object_sends_correct_code(self):
        """Direct capability test: delete generates correct bpy.data.objects.remove code."""
        from capabilities.object_operate_executor import ObjectOperateExecutor
        from taxonomy import DeleteObjectRequestVO, ObjectName

        mock_blender = MagicMock()
        mock_blender.execute_code = AsyncMock(return_value={})
        cap = ObjectOperateExecutor(blender_port=mock_blender)

        await cap.delete_object(DeleteObjectRequestVO(object_name=ObjectName("OldMesh")))

        sent_code = str(mock_blender.execute_code.call_args)
        assert "OldMesh" in sent_code
        assert "remove" in sent_code.lower()


# ── Scenario 5: set_object_transform ──────────────────────────────────────────

class TestScenarioSetObjectTransform:
    """User asks: 'move Cube to (5, 0, 0) and rotate it'
    
    NOTE: Tested via direct capability (ObjectOperateExecutor) due to
    missing DI slot for object_operate_capability in dispatch stack.
    """

    @pytest.mark.asyncio
    async def test_set_transform_includes_location_in_code(self):
        """Direct capability test: location is embedded in generated bpy code."""
        from capabilities.object_operate_executor import ObjectOperateExecutor
        from taxonomy import SetObjectTransformRequestVO, ObjectName, CoordinateList

        mock_blender = MagicMock()
        mock_blender.execute_code = AsyncMock(return_value={})
        cap = ObjectOperateExecutor(blender_port=mock_blender)

        await cap.set_object_transform(SetObjectTransformRequestVO(
            object_name=ObjectName("Cube"),
            location=CoordinateList([5.0, 0.0, 0.0]),
        ))

        sent_code = str(mock_blender.execute_code.call_args)
        assert "Cube" in sent_code
        assert "5.0" in sent_code

    @pytest.mark.asyncio
    async def test_set_transform_partial_update_no_crash(self):
        """Only location — rotation/scale must be skipped without crash."""
        from capabilities.object_operate_executor import ObjectOperateExecutor
        from taxonomy import SetObjectTransformRequestVO, ObjectName, CoordinateList, SuccessFlag

        mock_blender = MagicMock()
        mock_blender.execute_code = AsyncMock(return_value={})
        cap = ObjectOperateExecutor(blender_port=mock_blender)

        result = await cap.set_object_transform(SetObjectTransformRequestVO(
            object_name=ObjectName("Cube"),
            location=CoordinateList([1.0, 0.0, 0.0]),
        ))
        assert result.success == SuccessFlag(True)


# ── Scenario 6: set_material ──────────────────────────────────────────────────

class TestScenarioSetMaterial:
    """User asks: 'apply a metal material to Sphere'
    
    NOTE: Tested via direct capability (ObjectOperateExecutor) due to
    missing DI slot for object_operate_capability in dispatch stack.
    """

    @pytest.mark.asyncio
    async def test_set_material_emits_material_code(self):
        """Direct capability test: material assignment generates correct bpy code."""
        from capabilities.object_operate_executor import ObjectOperateExecutor
        from taxonomy import SetMaterialRequestVO, ObjectName, MaterialName

        mock_blender = MagicMock()
        mock_blender.execute_code = AsyncMock(return_value={})
        cap = ObjectOperateExecutor(blender_port=mock_blender)

        await cap.set_material(SetMaterialRequestVO(
            object_name=ObjectName("Sphere"),
            material_name=MaterialName("Metal"),
        ))

        sent_code = str(mock_blender.execute_code.call_args)
        assert "Sphere" in sent_code
        assert "Metal" in sent_code
        assert "material" in sent_code.lower()


# ── Scenario 7: search_assets multi-provider ──────────────────────────────────

class TestScenarioSearchAssets:
    """User asks: 'find nature assets from all providers'"""

    @pytest.mark.asyncio
    async def test_search_assets_merges_results_from_providers(self, mock_blender_send):
        """Replace provider adapters with mocks, run real search_all logic."""
        from capabilities.asset_search_collector import AssetSearchCollector
        from taxonomy import (
            AssetSearchResponseVO, AssetMetadataVO,
            SearchQuery, AssetId, AssetName, ProviderName,
        )

        mock_poly = AsyncMock()
        mock_poly.search_assets = AsyncMock(
            return_value=AssetSearchResponseVO(
                assets=[
                    AssetMetadataVO(
                        id=AssetId("ph1"),
                        name=AssetName("Forest HDRI"),
                        type="hdri",
                        provider=ProviderName("polyhaven"),
                        thumbnail_url=None,
                        tags=[],
                    )
                ],
                provider=ProviderName("polyhaven"),
            )
        )
        mock_sketch = AsyncMock()
        mock_sketch.search_assets = AsyncMock(
            return_value=AssetSearchResponseVO(
                assets=[
                    AssetMetadataVO(
                        id=AssetId("sf1"),
                        name=AssetName("Tree Model"),
                        type="model",
                        provider=ProviderName("sketchfab"),
                        thumbnail_url=None,
                        tags=[],
                    )
                ],
                provider=ProviderName("sketchfab"),
            )
        )

        collector = AssetSearchCollector(providers={
            "polyhaven": mock_poly,
            "sketchfab": mock_sketch,
        })

        results = await collector.search_all(query=SearchQuery("nature"))

        assert len(results) == 2
        provider_names = [str(r.provider) for r in results]
        assert "polyhaven" in provider_names
        assert "sketchfab" in provider_names


# ── Scenario 8: Unknown action graceful error ─────────────────────────────────

class TestScenarioUnknownAction:
    """System must not crash on unknown actions — return clear error to user."""

    @pytest.mark.asyncio
    async def test_unknown_action_returns_error_json(self, orchestrator, mock_blender_send):
        from taxonomy import ActionName

        result = await orchestrator.execute_action(ActionName("totally_unknown_action_xyz"))

        result_str = str(result)
        assert "Error" in result_str or "error" in result_str
        assert "totally_unknown_action_xyz" in result_str

    @pytest.mark.asyncio
    async def test_unknown_action_does_not_call_blender(self, orchestrator, mock_blender_send):
        from taxonomy import ActionName

        await orchestrator.execute_action(ActionName("nonexistent"))
        mock_blender_send.assert_not_called()


# ── Scenario 9: health_check ──────────────────────────────────────────────────

class TestScenarioHealthCheck:
    """User/system checks if the MCP server and Blender connection are alive."""

    def test_health_check_via_orchestrator_returns_prompt(self, orchestrator, mock_blender_send):
        result = orchestrator.health_check()
        result_str = str(result)
        parsed = json.loads(result_str)

        assert "blender_connected" in parsed
        assert "status" in parsed
        assert parsed["status"] in ("healthy", "degraded", "initializing")

    def test_health_check_json_is_complete(self, orchestrator, mock_blender_send):
        result = orchestrator.health_check()
        parsed = json.loads(str(result))

        # These keys must always be present regardless of Blender state
        required_keys = {"blender_connected", "status"}
        for key in required_keys:
            assert key in parsed, f"Missing key in health check: {key}"


# ── Scenario 10: Capability exception → graceful error JSON ───────────────────

class TestScenarioCapabilityException:
    """When a capability raises internally, the response must be a JSON error."""

    @pytest.mark.asyncio
    async def test_blender_timeout_returns_error_json(self, orchestrator, mock_blender_send):
        mock_blender_send.side_effect = Exception("Timeout waiting for Blender response")
        from taxonomy import ActionName

        result = await orchestrator.execute_action(ActionName("get_scene_info"))
        result_str = str(result)

        # Must be parseable JSON
        parsed = json.loads(result_str)
        assert "error" in parsed or "success" in parsed

    @pytest.mark.asyncio
    async def test_blender_connection_error_returns_error_json(
        self, orchestrator, mock_blender_send
    ):
        mock_blender_send.side_effect = ConnectionError("Connection to Blender lost")
        from taxonomy import ActionName

        result = await orchestrator.execute_action(ActionName("cleanup_scene"))
        result_str = str(result)

        parsed = json.loads(result_str)
        assert parsed is not None


# ── Scenario 11: cleanup_scene ────────────────────────────────────────────────

class TestScenarioCleanupScene:
    """User asks: 'clear all objects from the scene'"""

    @pytest.mark.asyncio
    async def test_cleanup_scene_sends_select_all_and_delete(self):
        """Direct capability test: cleanup generates bpy select-all + delete code."""
        from capabilities.scene_operate_executor import SceneOperateExecutor
        from taxonomy import CleanupSceneRequestVO

        mock_blender = MagicMock()
        mock_blender.execute_code = AsyncMock(return_value={})
        cap = SceneOperateExecutor(blender_port=mock_blender)

        await cap.cleanup_scene(CleanupSceneRequestVO())

        sent_code = str(mock_blender.execute_code.call_args)
        assert "select_all" in sent_code.lower() or "SELECT" in sent_code
        assert "delete" in sent_code.lower() or "DELETE" in sent_code

    @pytest.mark.asyncio
    async def test_cleanup_scene_result_indicates_success(self):
        """Direct capability test: cleanup returns success response."""
        from capabilities.scene_operate_executor import SceneOperateExecutor
        from taxonomy import CleanupSceneRequestVO, SuccessFlag

        mock_blender = MagicMock()
        mock_blender.execute_code = AsyncMock(return_value={})
        cap = SceneOperateExecutor(blender_port=mock_blender)

        result = await cap.cleanup_scene(CleanupSceneRequestVO())

        assert result.success == SuccessFlag(True)
        assert "cleaned" in result.message.lower() or "success" in result.message.lower()


# ── Scenario 12: get_object_info ──────────────────────────────────────────────

class TestScenarioGetObjectInfo:
    """User asks: 'what are the properties of Cube?'
    
    NOTE: Tested via direct capability (ObjectOperateExecutor) due to
    missing DI slot for object_operate_capability in dispatch stack.
    """

    @pytest.mark.asyncio
    async def test_get_object_info_queries_blender_with_name(self):
        """Direct capability test: queries Blender with the object name."""
        from capabilities.object_operate_executor import ObjectOperateExecutor
        from taxonomy import GetObjectInfoRequestVO, ObjectName

        mock_blender = MagicMock()
        from taxonomy.blender_spatial_vo import Vector3D
        mock_blender.get_object_info = AsyncMock(return_value=BlenderObject(
            name=ObjectName("Cube"), type=ObjectType("MESH"),
            location=Vector3D(0, 0, 0), rotation=Vector3D(0, 0, 0), scale=Vector3D(1, 1, 1),
        ))
        cap = ObjectOperateExecutor(blender_port=mock_blender)

        await cap.get_object_info(GetObjectInfoRequestVO(object_name=ObjectName("Cube")))

        # Blender get_object_info must be called with the object name
        mock_blender.get_object_info.assert_called_once()
        call_arg = str(mock_blender.get_object_info.call_args)
        assert "Cube" in call_arg

    @pytest.mark.asyncio
    async def test_get_object_info_result_contains_object_data(self):
        """Direct capability test: result contains object info from Blender."""
        from capabilities.object_operate_executor import ObjectOperateExecutor
        from taxonomy import GetObjectInfoRequestVO, ObjectName, SuccessFlag

        mock_blender = MagicMock()
        from taxonomy.blender_spatial_vo import Vector3D
        mock_blender.get_object_info = AsyncMock(return_value=BlenderObject(
            name=ObjectName("Cube"), type=ObjectType("MESH"),
            location=Vector3D(0, 0, 0), rotation=Vector3D(0, 0, 0), scale=Vector3D(1, 1, 1),
        ))
        cap = ObjectOperateExecutor(blender_port=mock_blender)

        result = await cap.get_object_info(GetObjectInfoRequestVO(object_name=ObjectName("Cube")))

        assert result.success == SuccessFlag(True)
        assert result.object_info.name == "Cube"
