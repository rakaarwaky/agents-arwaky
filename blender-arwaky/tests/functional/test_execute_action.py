"""Tests for ExecuteActionCapability."""
import pytest
from unittest.mock import AsyncMock, MagicMock
from capabilities.action_execute_actions import ActionExecuteActions as ExecuteActionCapability


@pytest.fixture
def mock_orchestrator():
    """Create a mock orchestrator with known methods and DI properties."""
    orch = MagicMock()
    
    # Mock BlenderPort (blender)
    blender = MagicMock()
    blender.get_scene_info = AsyncMock(return_value={"name": "TestScene"})
    blender.get_object_info = AsyncMock(return_value={"name": "Cube"})
    blender.execute_code = AsyncMock(return_value="OK")
    orch.blender = blender
    
    # Mock capability executors
    scene_cap = MagicMock()
    scene_cap.get_scene_info = AsyncMock(return_value={"name": "TestScene"})
    orch.operate_scene_capability = scene_cap
    
    object_cap = MagicMock()
    object_cap.get_object_info = AsyncMock(return_value={"name": "Cube"})
    orch.object_operate_capability = object_cap
    
    # For backward compatibility in tests asserting on mock_orchestrator direct methods
    orch.get_scene_info = scene_cap.get_scene_info
    orch.get_object_info = object_cap.get_object_info
    orch.execute_blender_code = blender.execute_code
    
    return orch


@pytest.fixture
def capability(mock_orchestrator):
    """Create ExecuteActionCapability with mock orchestrator."""
    return ExecuteActionCapability(orchestrator=mock_orchestrator)


class TestExecuteActionCapability:
    """Tests for action execution dispatch."""

    @pytest.mark.asyncio
    async def test_execute_known_action(self, capability, mock_orchestrator):
        """Executing a known action must delegate to orchestrator."""
        result = await capability.execute("get_scene_info")
        mock_orchestrator.get_scene_info.assert_called_once()
        assert "TestScene" in result

    @pytest.mark.asyncio
    async def test_execute_unknown_action_returns_error(self, capability):
        """Executing an unknown action must return error message, not crash."""
        result = await capability.execute("nonexistent_action")
        assert "Error" in result
        assert "Unknown" in result

    @pytest.mark.asyncio
    async def test_execute_with_args(self, capability, mock_orchestrator):
        """Executing with args must pass them to the orchestrator method."""
        await capability.execute("get_object_info", {"name": "Cube"})
        mock_orchestrator.get_object_info.assert_called_once_with(name="Cube")

    @pytest.mark.asyncio
    async def test_execute_returns_json_string(self, capability):
        """Result must always be a JSON string."""
        result = await capability.execute("get_scene_info")
        assert isinstance(result, str)
        import json
        parsed = json.loads(result)
        assert isinstance(parsed, (dict, list))

    @pytest.mark.asyncio
    async def test_execute_handles_missing_args(self, capability):
        """Executing with None args must not crash."""
        result = await capability.execute("get_scene_info", None)
        assert "TestScene" in result
