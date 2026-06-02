"""Tests for contract layer — BlenderPort abstract interface and protocols."""
import pytest
from contract import BlenderPort
from contract.adapter_blender_port import BlenderPort as BlenderPortDirect
from contract import (
    SceneOperateProtocol,
    ObjectOperateProtocol,
    RenderOperateProtocol,
    ImportExportProtocol,
)


class TestBlenderPortInterface:
    """BlenderPort must define all expected abstract methods."""

    REQUIRED_METHODS = {"execute_code", "get_scene_info", "get_object_info", "get_screenshot"}

    def test_blender_port_has_required_methods(self):
        """BlenderPort must define all 4 abstract methods."""
        # Only collect methods actually defined on the class (not inherited from object)
        abstract_methods = set()
        for name in dir(BlenderPort):
            if not name.startswith('_') and callable(getattr(BlenderPort, name, None)):
                abstract_methods.add(name)
        for method in self.REQUIRED_METHODS:
            assert method in abstract_methods, (
                f"BlenderPort missing abstract method: {method}"
            )

    def test_blender_port_cannot_be_instantiated(self):
        """BlenderPort should not be directly instantiable (abstract)."""
        with pytest.raises(TypeError):
            BlenderPort()  # type: ignore


class TestSceneOperateProtocol:
    """SceneOperateProtocol must define all expected methods."""

    REQUIRED_METHODS = {"cleanup_scene", "setup_environment", "get_scene_info"}

    def test_protocol_has_required_methods(self):
        """SceneOperateProtocol must define all scene operations."""
        protocol_methods = set()
        for name in dir(SceneOperateProtocol):
            if not name.startswith('_'):
                protocol_methods.add(name)
        for method in self.REQUIRED_METHODS:
            assert method in protocol_methods, (
                f"SceneOperateProtocol missing method: {method}"
            )


class TestObjectOperateProtocol:
    """ObjectOperateProtocol must define all expected methods."""

    REQUIRED_METHODS = {
        "place_asset", "get_object_info", "set_object_transform",
        "delete_object", "create_primitive", "set_material", "apply_modifier",
    }

    def test_protocol_has_required_methods(self):
        """ObjectOperateProtocol must define all object operations."""
        protocol_methods = set()
        for name in dir(ObjectOperateProtocol):
            if not name.startswith('_'):
                protocol_methods.add(name)
        for method in self.REQUIRED_METHODS:
            assert method in protocol_methods, (
                f"ObjectOperateProtocol missing method: {method}"
            )


class TestBlenderPortDirect:
    """Direct import from adapter_blender_port must work."""

    def test_class_is_same(self):
        """Barrel export and direct import should reference same class."""
        assert BlenderPort is BlenderPortDirect
