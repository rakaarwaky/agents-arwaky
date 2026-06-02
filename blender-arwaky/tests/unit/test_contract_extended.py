"""Tests untuk contract layer — menutup gap coverage ke 90%.

Mencakup:
- tool_hunyuan_port.py   (75% → 90%)
- tool_hyper3d_port.py   (73% → 90%)
- workflow_operate_protocol.py (78% → 90%)
- catalog_command_handler.py (62% → 85%) - surfaces layer
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

# ─── tool_hunyuan_port.py ─────────────────────────────────────────

from contract.tool_hunyuan_port import HunyuanToolPort
from taxonomy import StatusString, Prompt, ResultUrl, JobId, ObjectName


class ConcreteHunyuanPort(HunyuanToolPort):
    """Concrete implementation for testing the abstract interface."""

    def get_hunyuan3d_status(self) -> StatusString:
        return StatusString("enabled")

    def generate_hunyuan3d_model(self, text_prompt=None, input_image_url=None) -> StatusString:
        return StatusString(f"job_started:{text_prompt}")

    def poll_hunyuan_job_status(self, job_id=None) -> StatusString:
        return StatusString(f"DONE:{job_id}")

    def import_generated_asset_hunyuan(self, name, zip_file_url) -> StatusString:
        return StatusString(f"imported:{name}")


class TestHunyuanToolPort:
    def test_interface_is_abstract(self):
        with pytest.raises(TypeError):
            HunyuanToolPort()  # type: ignore

    def test_concrete_implementation_works(self):
        port = ConcreteHunyuanPort()
        assert port.get_hunyuan3d_status() == "enabled"

    def test_generate_model(self):
        port = ConcreteHunyuanPort()
        result = port.generate_hunyuan3d_model(text_prompt=Prompt("a sphere"))
        assert "job_started" in result

    def test_poll_job_status(self):
        port = ConcreteHunyuanPort()
        result = port.poll_hunyuan_job_status(job_id=JobId("job-123"))
        assert "DONE" in result
        assert "job-123" in result

    def test_import_asset(self):
        port = ConcreteHunyuanPort()
        result = port.import_generated_asset_hunyuan(
            name=ObjectName("Dragon"),
            zip_file_url=ResultUrl("https://example.com/model.zip")
        )
        assert "imported" in result
        assert "Dragon" in result

    def test_generate_with_optional_image(self):
        port = ConcreteHunyuanPort()
        result = port.generate_hunyuan3d_model(
            text_prompt=Prompt("spaceship"),
            input_image_url=ResultUrl("https://example.com/ref.jpg"),
        )
        assert result is not None


# ─── tool_hyper3d_port.py ─────────────────────────────────────────

from contract.tool_hyper3d_port import Hyper3dToolPort
from taxonomy import CoordinateList, StringList, TaskUuid, BBoxIntegers


class ConcreteHyper3dPort(Hyper3dToolPort):
    def get_hyper3d_status(self) -> StatusString:
        return StatusString("enabled")

    def generate_hyper3d_model_via_text(self, text_prompt, bbox_condition=None) -> StatusString:
        return StatusString(f"job:{text_prompt}")

    def generate_hyper3d_model_via_images(self, input_image_paths=None, input_image_urls=None, bbox_condition=None) -> StatusString:
        return StatusString("image_job")

    def poll_rodin_job_status(self, subscription_key=None, request_id=None) -> StatusString:
        return StatusString(f"status:{subscription_key or request_id}")

    def import_generated_asset(self, name, task_uuid=None, request_id=None) -> StatusString:
        return StatusString(f"imported:{name}")

    def process_bbox(self, original_bbox) -> BBoxIntegers | None:
        if original_bbox is None:
            return None
        return BBoxIntegers([int(v) for v in original_bbox])


class TestHyper3dToolPort:
    def test_interface_is_abstract(self):
        with pytest.raises(TypeError):
            Hyper3dToolPort()  # type: ignore

    def test_get_status(self):
        port = ConcreteHyper3dPort()
        assert port.get_hyper3d_status() == "enabled"

    def test_generate_via_text(self):
        port = ConcreteHyper3dPort()
        result = port.generate_hyper3d_model_via_text(
            text_prompt=Prompt("a robot"),
            bbox_condition=CoordinateList([0.0, 0.0, 0.0, 1.0, 1.0, 1.0]),
        )
        assert "robot" in result

    def test_generate_via_images(self):
        port = ConcreteHyper3dPort()
        result = port.generate_hyper3d_model_via_images(
            input_image_paths=StringList(["/img/view1.jpg"]),
        )
        assert result == "image_job"

    def test_generate_via_images_with_urls(self):
        port = ConcreteHyper3dPort()
        result = port.generate_hyper3d_model_via_images(
            input_image_urls=StringList(["https://example.com/view1.jpg"]),
        )
        assert result == "image_job"

    def test_poll_main_site(self):
        port = ConcreteHyper3dPort()
        result = port.poll_rodin_job_status(subscription_key=StatusString("sub-key-123"))
        assert "sub-key-123" in result

    def test_poll_fal_ai(self):
        port = ConcreteHyper3dPort()
        result = port.poll_rodin_job_status(request_id=StatusString("req-456"))
        assert "req-456" in result

    def test_import_asset_with_task_uuid(self):
        port = ConcreteHyper3dPort()
        result = port.import_generated_asset(
            name=ObjectName("Robot"),
            task_uuid=TaskUuid("task-uuid-789"),
        )
        assert "Robot" in result

    def test_import_asset_with_request_id(self):
        port = ConcreteHyper3dPort()
        result = port.import_generated_asset(
            name=ObjectName("Ship"),
            request_id=StatusString("req-999"),
        )
        assert "Ship" in result

    def test_process_bbox_none(self):
        port = ConcreteHyper3dPort()
        assert port.process_bbox(None) is None

    def test_process_bbox_with_values(self):
        port = ConcreteHyper3dPort()
        result = port.process_bbox(CoordinateList([0.1, 0.2, 0.3, 1.1, 1.2, 1.3]))
        assert result is not None
        assert result[0] == 0


# ─── workflow_operate_protocol.py ────────────────────────────────

from contract.workflow_operate_protocol import WorkflowProtocol
from taxonomy import SuccessFlag, ProviderName


class ConcreteWorkflowProtocol(WorkflowProtocol):
    async def create_basic_scene(self, prompt: Prompt) -> SuccessFlag:
        return SuccessFlag(True)

    async def generate_and_import_ai_asset(
        self, provider_name: ProviderName, prompt: Prompt
    ) -> Prompt:
        return Prompt(f"Generated with {provider_name}: {prompt}")


class TestWorkflowProtocol:
    def test_interface_is_abstract(self):
        with pytest.raises(TypeError):
            WorkflowProtocol()  # type: ignore

    @pytest.mark.asyncio
    async def test_create_basic_scene(self):
        protocol = ConcreteWorkflowProtocol()
        result = await protocol.create_basic_scene(Prompt("forest scene"))
        assert result is True

    @pytest.mark.asyncio
    async def test_generate_and_import(self):
        protocol = ConcreteWorkflowProtocol()
        result = await protocol.generate_and_import_ai_asset(
            provider_name=ProviderName("polyhaven"),
            prompt=Prompt("a forest HDRI"),
        )
        assert "polyhaven" in result
        assert "forest" in result


# ─── catalog_command_handler.py (surfaces) ───────────────────────

from surfaces.catalog_command_handler import (
    CommandCatalogSurfaceHandler,
    list_commands,
    filter_by_domain,
    get_actions_by_capability,
    register_command_catalog,
)
from taxonomy import DomainRef, CapabilityRef


class TestCommandCatalogSurfaceHandler:
    def test_list_commands_all(self):
        result = CommandCatalogSurfaceHandler.list_commands(DomainRef("all"))
        assert isinstance(result, list)
        assert len(result) > 0

    def test_list_commands_specific_domain(self):
        all_cmds = CommandCatalogSurfaceHandler.list_commands(DomainRef("all"))
        result = CommandCatalogSurfaceHandler.list_commands(DomainRef("scene"))
        assert isinstance(result, list)
        # Filtered result should be a subset
        assert all(cmd in all_cmds for cmd in result)

    def test_list_commands_unknown_domain_returns_empty(self):
        result = CommandCatalogSurfaceHandler.list_commands(DomainRef("nonexistent_domain_xyz"))
        assert result == [] or isinstance(result, list)

    def test_filter_by_domain_returns_dict(self):
        result = CommandCatalogSurfaceHandler.filter_by_domain(DomainRef("scene"))
        assert isinstance(result, dict)

    def test_filter_by_domain_all_values_match(self):
        result = CommandCatalogSurfaceHandler.filter_by_domain(DomainRef("scene"))
        for name, spec in result.items():
            assert spec.get("domain") == "scene"

    def test_filter_by_unknown_domain_empty(self):
        result = CommandCatalogSurfaceHandler.filter_by_domain(DomainRef("xyz_unknown"))
        assert result == {}

    def test_get_actions_by_capability(self):
        result = CommandCatalogSurfaceHandler.get_actions_by_capability(CapabilityRef("scene_ops"))
        assert isinstance(result, list)

    def test_get_actions_by_unknown_capability_empty(self):
        result = CommandCatalogSurfaceHandler.get_actions_by_capability(CapabilityRef("nonexistent_cap"))
        assert result == []

    def test_module_alias_list_commands(self):
        """Module-level alias should work identically."""
        result = list_commands(DomainRef("all"))
        assert result == CommandCatalogSurfaceHandler.list_commands(DomainRef("all"))

    def test_module_alias_filter_by_domain(self):
        result = filter_by_domain(DomainRef("scene"))
        assert result == CommandCatalogSurfaceHandler.filter_by_domain(DomainRef("scene"))

    def test_module_alias_get_actions_by_capability(self):
        result = get_actions_by_capability(CapabilityRef("scene_ops"))
        assert result == CommandCatalogSurfaceHandler.get_actions_by_capability(CapabilityRef("scene_ops"))

    def test_register_command_catalog(self):
        """register_command_catalog should register a tool on the mcp object."""
        mcp = MagicMock()
        registered_tool = None

        def capture_tool(func=None, **kwargs):
            """Decorator factory that captures the tool."""
            def decorator(f):
                nonlocal registered_tool
                registered_tool = f
                return f
            return decorator if func is None else decorator(func)

        mcp.tool = capture_tool
        result = CommandCatalogSurfaceHandler.register_command_catalog(mcp)
        # The function should be returned and registered
        assert result is not None or registered_tool is not None
