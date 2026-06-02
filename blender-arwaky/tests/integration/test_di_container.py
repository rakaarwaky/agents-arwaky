"""Tests for DI container wiring."""
import pytest
from agent.agent_di_container import get_container, reset_container


@pytest.fixture(autouse=True)
def reset_di(monkeypatch):
    """Reset DI container before each test and mock Blender socket connection."""
    from infrastructure.blender_connection_connector import BlenderConnection
    monkeypatch.setattr(BlenderConnection, "connect", lambda self: True)
    monkeypatch.setattr(BlenderConnection, "_is_socket_alive", lambda self: True)
    reset_container()
    yield
    reset_container()


class TestDIContainer:
    """Tests that DI container resolves all capabilities."""

    def test_container_is_singleton(self):
        """get_container must return the same instance."""
        c1 = get_container()
        c2 = get_container()
        assert c1 is c2

    def test_reset_creates_new_instance(self):
        """reset_container must create a new instance on next get."""
        c1 = get_container()
        reset_container()
        c2 = get_container()
        assert c1 is not c2

    def test_container_resolves_operate_scene_capability(self):
        """DI container must resolve operate_scene_capability."""
        container = get_container()
        cap = container.operate_scene_capability
        assert cap is not None
        assert hasattr(cap, "cleanup_scene")
        assert hasattr(cap, "get_scene_info")

    def test_container_resolves_search_asset_capability(self):
        """DI container must resolve search_asset_capability."""
        container = get_container()
        cap = container.search_asset_capability
        assert cap is not None
        assert hasattr(cap, "search_all")

    def test_container_resolves_generate_ai_capability(self):
        """DI container must resolve generate_ai_capability."""
        container = get_container()
        cap = container.generate_ai_capability
        assert cap is not None
        assert hasattr(cap, "start_generation")
        assert hasattr(cap, "check_status")

    def test_container_resolves_execute_action_capability(self):
        """DI container must resolve execute_action_capability."""
        container = get_container()
        cap = container.action_execute_capability
        assert cap is not None
        assert hasattr(cap, "execute")

    def test_container_resolves_system_utils(self):
        """DI container must resolve system_utils."""
        container = get_container()
        utils = container.system_utils
        assert utils is not None
