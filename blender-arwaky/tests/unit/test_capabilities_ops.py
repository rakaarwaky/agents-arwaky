import pytest
from unittest.mock import MagicMock, patch, AsyncMock

from taxonomy import (
    Prompt, JobId, ProviderName, ProviderError, ErrorMessage,
    SearchQuery, AssetId, FilePath, ObjectName, BlenderMCPError,
    ImportGlbRequestVO, ExportModelRequestVO,
    PlaceAssetRequestVO, SetObjectTransformRequestVO, DeleteObjectRequestVO,
    CreatePrimitiveRequestVO, SetMaterialRequestVO, ApplyModifierRequestVO,
    GetScreenshotRequestVO, RenderRequestVO,
    CleanupSceneRequestVO, SetupEnvironmentRequestVO, GetSceneInfoRequestVO,
    ActionName, TagList, AssetType,
    StringList, Vector3D, PrimitiveType, CoordinateList,
    RotationVector, RenderEngine, RenderSamples, UseDenoising, RuleName,
    HdriId,
    GetObjectInfoRequestVO,
    AssetMetadataVO, AssetSearchResponseVO, SceneInfo, BlenderObjectList,
    AssetName, BlenderObject, ObjectType
)
from capabilities.ai_generate_generator import AiGenerateGenerator
from capabilities.asset_search_collector import AssetSearchCollector
from capabilities.import_export_executor import ImportExportExecutor
from capabilities.object_operate_executor import ObjectOperateExecutor
from capabilities.render_operate_executor import RenderOperateExecutor
from capabilities.scene_operate_executor import SceneOperateExecutor
from capabilities.workflow_orchestrate_executor import WorkflowExecutor
from capabilities.action_execute_actions import ActionExecuteActions


class TestAiGenerateGenerator:
    """Tests for AiGenerateGenerator."""

    @pytest.mark.asyncio
    async def test_start_generation_success(self):
        mock_provider = MagicMock()
        mock_provider.start_generation = AsyncMock(return_value=MagicMock(job_id=JobId("job_123")))
        generator = AiGenerateGenerator(providers={"hunyuan": mock_provider})

        res = await generator.start_generation(ProviderName("hunyuan"), Prompt("cat"))
        assert res == "job_123"
        mock_provider.start_generation.assert_called_once()

    @pytest.mark.asyncio
    async def test_start_generation_provider_not_found(self):
        generator = AiGenerateGenerator(providers={})
        with pytest.raises(ProviderError) as exc:
            await generator.start_generation(ProviderName("hunyuan"), Prompt("cat"))
        assert "not found" in str(exc.value)

    @pytest.mark.asyncio
    async def test_check_status_success(self):
        mock_provider = MagicMock()
        mock_response = MagicMock(status="COMPLETED", progress=1.0, error=None)
        mock_provider.poll_generation = AsyncMock(return_value=mock_response)
        generator = AiGenerateGenerator(providers={"hunyuan": mock_provider})

        res = await generator.check_status(ProviderName("hunyuan"), JobId("job_123"))
        assert res.status == "COMPLETED"
        assert res.progress == 1.0
        mock_provider.poll_generation.assert_called_once()

    @pytest.mark.asyncio
    async def test_check_status_provider_not_found(self):
        generator = AiGenerateGenerator(providers={})
        with pytest.raises(ProviderError) as exc:
            await generator.check_status(ProviderName("hunyuan"), JobId("job_123"))
        assert "not found" in str(exc.value)


class TestAssetSearchCollector:
    """Tests for AssetSearchCollector."""

    @pytest.mark.asyncio
    async def test_search_all_success(self):
        mock_provider = MagicMock()
        mock_asset = AssetMetadataVO(
            id=AssetId("a1"),
            name=AssetName("A1"),
            type=AssetType("models"),
            provider=ProviderName("polyhaven"),
            thumbnail_url=None,
            tags=TagList(["tag"])
        )
        mock_response = AssetSearchResponseVO(assets=[mock_asset], provider=ProviderName("polyhaven"))
        mock_provider.search_assets = AsyncMock(return_value=mock_response)

        collector = AssetSearchCollector(providers={"polyhaven": mock_provider})
        res = await collector.search_all(SearchQuery("wood"))
        assert len(res) == 1
        assert res[0].name == "A1"

    @pytest.mark.asyncio
    async def test_search_all_provider_error(self):
        mock_provider = MagicMock()
        mock_provider.search_assets = AsyncMock(side_effect=ProviderError(ErrorMessage("API down")))

        collector = AssetSearchCollector(providers={"polyhaven": mock_provider})
        # Should catch and log error, returning empty list
        res = await collector.search_all(SearchQuery("wood"))
        assert len(res) == 0

    @pytest.mark.asyncio
    async def test_search_all_filtered_providers(self):
        mock_p1 = MagicMock()
        mock_p1.search_assets = AsyncMock(return_value=MagicMock(assets=[]))
        mock_p2 = MagicMock()
        mock_p2.search_assets = AsyncMock(return_value=MagicMock(assets=[]))
        collector = AssetSearchCollector(providers={"p1": mock_p1, "p2": mock_p2})

        await collector.search_all(SearchQuery("wood"), providers=StringList(["p1"]))
        mock_p1.search_assets.assert_called_once()
        mock_p2.search_assets.assert_not_called()

    @pytest.mark.asyncio
    async def test_fetch_and_import_success(self):
        mock_provider = MagicMock()
        mock_provider.download_asset = AsyncMock(return_value=MagicMock(file_path="/path/to/my_asset.glb"))

        collector = AssetSearchCollector(providers={"polyhaven": mock_provider})
        res = await collector.fetch_and_import(ProviderName("polyhaven"), AssetId("my_asset"))
        assert res.id == "my_asset"
        assert res.blender_id == "my_asset"

    @pytest.mark.asyncio
    async def test_fetch_and_import_provider_not_found(self):
        collector = AssetSearchCollector(providers={})
        with pytest.raises(ProviderError) as exc:
            await collector.fetch_and_import(ProviderName("polyhaven"), AssetId("my_asset"))
        assert "not found" in str(exc.value)

    @pytest.mark.asyncio
    async def test_fetch_and_import_empty_filepath(self):
        mock_provider = MagicMock()
        mock_provider.download_asset = AsyncMock(return_value=MagicMock(file_path=None))

        collector = AssetSearchCollector(providers={"polyhaven": mock_provider})
        with pytest.raises(ProviderError) as exc:
            await collector.fetch_and_import(ProviderName("polyhaven"), AssetId("my_asset"))
        assert "no file path" in str(exc.value)


class TestImportExportExecutor:
    """Tests for ImportExportExecutor."""

    @pytest.mark.asyncio
    async def test_import_glb_success(self):
        mock_blender = MagicMock()
        mock_blender.execute_code = AsyncMock(return_value=None)
        executor = ImportExportExecutor(mock_blender)

        res = await executor.import_glb(ImportGlbRequestVO(file_path=FilePath("/mock/file.glb"), object_name=ObjectName("MyGLB")))
        assert res.success is True
        assert res.object_name == "MyGLB"
        mock_blender.execute_code.assert_called_once()

    @pytest.mark.asyncio
    async def test_import_glb_exception(self):
        mock_blender = MagicMock()
        mock_blender.execute_code = AsyncMock(side_effect=Exception("Execute error"))
        executor = ImportExportExecutor(mock_blender)

        with pytest.raises(BlenderMCPError) as exc:
            await executor.import_glb(ImportGlbRequestVO(file_path=FilePath("/mock/file.glb")))
        assert "Import failed" in str(exc.value)

    @pytest.mark.asyncio
    async def test_export_model_success(self):
        mock_blender = MagicMock()
        mock_blender.execute_code = AsyncMock(return_value=None)
        executor = ImportExportExecutor(mock_blender)

        res = await executor.export_model(ExportModelRequestVO(file_path=FilePath("/mock/file.glb"), object_name=ObjectName("MyCube")))
        assert res.success is True
        assert res.object_name == "MyCube"
        mock_blender.execute_code.assert_called_once()

    @pytest.mark.asyncio
    async def test_export_model_exception(self):
        mock_blender = MagicMock()
        mock_blender.execute_code = AsyncMock(side_effect=Exception("Execute error"))
        executor = ImportExportExecutor(mock_blender)

        with pytest.raises(BlenderMCPError) as exc:
            await executor.export_model(ExportModelRequestVO(file_path=FilePath("/mock/file.glb"), object_name=ObjectName("MyCube")))
        assert "Export failed" in str(exc.value)


class TestObjectOperateExecutor:
    """Tests for ObjectOperateExecutor."""

    @pytest.fixture
    def mock_blender(self):
        m = MagicMock()
        m.execute_code = AsyncMock(return_value=None)
        return m

    @pytest.mark.asyncio
    async def test_place_asset_success(self, mock_blender):
        executor = ObjectOperateExecutor(mock_blender)

        # 1. With object name
        res = await executor.place_asset(PlaceAssetRequestVO(asset_id=AssetId("chair"), location=CoordinateList([1.0, 2.0, 3.0]), object_name=ObjectName("chair_mesh")))
        assert res.success is True
        assert res.object_name == "chair_mesh"

        # 2. Without object name
        res2 = await executor.place_asset(PlaceAssetRequestVO(asset_id=AssetId("chair"), location=CoordinateList([1.0, 2.0, 3.0])))
        assert res2.success is True
        assert res2.object_name == "chair"

    @pytest.mark.asyncio
    async def test_place_asset_exception(self, mock_blender):
        mock_blender.execute_code = AsyncMock(side_effect=Exception("Write error"))
        executor = ObjectOperateExecutor(mock_blender)

        with pytest.raises(BlenderMCPError) as exc:
            await executor.place_asset(PlaceAssetRequestVO(asset_id=AssetId("chair"), location=CoordinateList([1, 2, 3])))
        assert "Failed to place" in str(exc.value)

    @pytest.mark.asyncio
    async def test_get_object_info(self, mock_blender):
        mock_blender.get_object_info = AsyncMock(return_value=BlenderObject(
            name=ObjectName("Cube"),
            type=ObjectType("MESH"),
            location=Vector3D(0.0, 0.0, 0.0),
            rotation=Vector3D(0.0, 0.0, 0.0),
            scale=Vector3D(1.0, 1.0, 1.0)
        ))
        executor = ObjectOperateExecutor(mock_blender)

        res = await executor.get_object_info(GetObjectInfoRequestVO(object_name=ObjectName("Cube")))
        assert res.success is True
        mock_blender.get_object_info.assert_called_once_with(ObjectName("Cube"))

        # Exception
        mock_blender.get_object_info = AsyncMock(side_effect=Exception("Not found"))
        with pytest.raises(BlenderMCPError):
            await executor.get_object_info(GetObjectInfoRequestVO(object_name=ObjectName("Cube")))

    @pytest.mark.asyncio
    async def test_set_object_transform(self, mock_blender):
        executor = ObjectOperateExecutor(mock_blender)

        res = await executor.set_object_transform(SetObjectTransformRequestVO(
            object_name=ObjectName("Cube"),
            location=CoordinateList([1, 2, 3]),
            rotation=CoordinateList([0, 0, 90]),
            scale=CoordinateList([2, 2, 2])
        ))
        assert res.success is True

        # Exception
        mock_blender.execute_code = AsyncMock(side_effect=Exception())
        with pytest.raises(BlenderMCPError):
            await executor.set_object_transform(SetObjectTransformRequestVO(object_name=ObjectName("Cube")))

    @pytest.mark.asyncio
    async def test_delete_object(self, mock_blender):
        executor = ObjectOperateExecutor(mock_blender)

        res = await executor.delete_object(DeleteObjectRequestVO(object_name=ObjectName("Cube")))
        assert res.success is True

        # Exception
        mock_blender.execute_code = AsyncMock(side_effect=Exception())
        with pytest.raises(BlenderMCPError):
            await executor.delete_object(DeleteObjectRequestVO(object_name=ObjectName("Cube")))

    @pytest.mark.asyncio
    async def test_create_primitive(self, mock_blender):
        executor = ObjectOperateExecutor(mock_blender)

        # Cube with all params
        res = await executor.create_primitive(CreatePrimitiveRequestVO(
            primitive_type=PrimitiveType("cube"),
            location=CoordinateList([0, 0, 0]),
            scale=CoordinateList([1, 1, 1]),
            name=ObjectName("MyBox")
        ))
        assert res.success is True
        assert res.object_name == "MyBox"

        # Torus
        res2 = await executor.create_primitive(CreatePrimitiveRequestVO(
            primitive_type=PrimitiveType("torus")
        ))
        assert res2.success is True
        assert res2.object_name == "Primitive"

        # Exception
        mock_blender.execute_code = AsyncMock(side_effect=Exception())
        with pytest.raises(BlenderMCPError):
            await executor.create_primitive(CreatePrimitiveRequestVO(primitive_type=PrimitiveType("cube")))

    @pytest.mark.asyncio
    async def test_set_material(self, mock_blender):
        executor = ObjectOperateExecutor(mock_blender)

        res = await executor.set_material(SetMaterialRequestVO(object_name=ObjectName("Cube"), material_name="Gold"))
        assert res.success is True

        # Exception
        mock_blender.execute_code = AsyncMock(side_effect=Exception())
        with pytest.raises(BlenderMCPError):
            await executor.set_material(SetMaterialRequestVO(object_name=ObjectName("Cube"), material_name="Gold"))

    @pytest.mark.asyncio
    async def test_apply_modifier(self, mock_blender):
        executor = ObjectOperateExecutor(mock_blender)

        res = await executor.apply_modifier(ApplyModifierRequestVO(object_name=ObjectName("Cube"), modifier_name="Subsurf"))
        assert res.success is True

        # Exception
        mock_blender.execute_code = AsyncMock(side_effect=Exception())
        with pytest.raises(BlenderMCPError):
            await executor.apply_modifier(ApplyModifierRequestVO(object_name=ObjectName("Cube"), modifier_name="Subsurf"))


class TestRenderOperateExecutor:
    """Tests for RenderOperateExecutor."""

    @pytest.fixture
    def mock_blender(self):
        m = MagicMock()
        m.execute_code = AsyncMock(return_value=None)
        return m

    @pytest.mark.asyncio
    async def test_get_viewport_screenshot(self, mock_blender):
        mock_blender.get_screenshot = AsyncMock(return_value=b"bytes")
        executor = RenderOperateExecutor(mock_blender)

        res = await executor.get_viewport_screenshot(GetScreenshotRequestVO(max_size=300))
        assert res.success is True
        assert res.image_data == b"bytes"

        # Exception
        mock_blender.get_screenshot = AsyncMock(side_effect=Exception())
        with pytest.raises(BlenderMCPError):
            await executor.get_viewport_screenshot(GetScreenshotRequestVO(max_size=300))

    @pytest.mark.asyncio
    async def test_setup_camera(self, mock_blender):
        executor = RenderOperateExecutor(mock_blender)

        res = await executor.setup_camera(CoordinateList([1, 2, 3]), RotationVector([0, 0, 0]), CoordinateList([0, 0, 0]))
        assert "successful" in str(res)

        # Exception
        mock_blender.execute_code = AsyncMock(side_effect=Exception())
        with pytest.raises(BlenderMCPError):
            await executor.setup_camera(CoordinateList([1, 2, 3]), RotationVector([0, 0, 0]))

    @pytest.mark.asyncio
    async def test_setup_render(self, mock_blender):
        executor = RenderOperateExecutor(mock_blender)

        res = await executor.setup_render(RenderEngine("CYCLES"), RenderSamples(64), CoordinateList([1920, 1080]), UseDenoising(True))
        assert "configured" in str(res)

        # Exception
        mock_blender.execute_code = AsyncMock(side_effect=Exception())
        with pytest.raises(BlenderMCPError):
            await executor.setup_render()

    @pytest.mark.asyncio
    async def test_apply_composition(self, mock_blender):
        executor = RenderOperateExecutor(mock_blender)

        res = await executor.apply_composition(RuleName("thirds"))
        assert "applied" in str(res)

        res2 = await executor.apply_composition(RuleName("golden"))
        assert "applied" in str(res2)

        # Exception
        mock_blender.execute_code = AsyncMock(side_effect=Exception())
        with pytest.raises(BlenderMCPError):
            await executor.apply_composition(RuleName("thirds"))

    @pytest.mark.asyncio
    async def test_render(self, mock_blender):
        executor = RenderOperateExecutor(mock_blender)

        res = await executor.render(RenderRequestVO(output_path="/tmp/render.png"))
        assert res.success is True

        # Exception
        mock_blender.execute_code = AsyncMock(side_effect=Exception())
        with pytest.raises(BlenderMCPError):
            await executor.render(RenderRequestVO(output_path="/tmp/render.png"))


class TestSceneOperateExecutor:
    """Tests for SceneOperateExecutor."""

    @pytest.fixture
    def mock_blender(self):
        m = MagicMock()
        m.execute_code = AsyncMock(return_value=None)
        return m

    @pytest.mark.asyncio
    async def test_cleanup_scene(self, mock_blender):
        executor = SceneOperateExecutor(mock_blender)

        res = await executor.cleanup_scene(CleanupSceneRequestVO())
        assert res.success is True

        # Failed status returned
        mock_blender.execute_code = AsyncMock(side_effect=Exception("Write error"))
        res2 = await executor.cleanup_scene(CleanupSceneRequestVO())
        assert res2.success is False
        assert "Write error" in res2.message

    @pytest.mark.asyncio
    async def test_setup_environment(self, mock_blender):
        executor = SceneOperateExecutor(mock_blender)

        res = await executor.setup_environment(SetupEnvironmentRequestVO(hdri_id=HdriId("studio")))
        assert res.success is True

        # Exception path
        mock_blender.execute_code = AsyncMock(side_effect=Exception("HDRI error"))
        res2 = await executor.setup_environment(SetupEnvironmentRequestVO(hdri_id=HdriId("studio")))
        assert res2.success is False
        assert "HDRI error" in res2.message

    @pytest.mark.asyncio
    async def test_get_scene_info(self, mock_blender):
        mock_blender.get_scene_info = AsyncMock(return_value=SceneInfo(objects=BlenderObjectList([])))
        executor = SceneOperateExecutor(mock_blender)

        res = await executor.get_scene_info(GetSceneInfoRequestVO())
        assert res.success is True

        # Exception path
        mock_blender.get_scene_info = AsyncMock(side_effect=Exception("Socket crash"))
        with pytest.raises(BlenderMCPError):
            await executor.get_scene_info(GetSceneInfoRequestVO())


class TestWorkflowExecutor:
    """Tests for WorkflowExecutor."""

    @pytest.fixture
    def mock_scene(self):
        m = MagicMock()
        m.cleanup_scene = AsyncMock()
        m.setup_environment = AsyncMock()
        m.blender = MagicMock()
        m.blender.execute_code = AsyncMock()
        return m

    @pytest.fixture
    def mock_search(self):
        m = MagicMock()
        m.search_all = AsyncMock()
        return m

    @pytest.fixture
    def mock_generation(self):
        m = MagicMock()
        m.start_generation = AsyncMock()
        m.check_status = AsyncMock()
        return m

    @pytest.mark.asyncio
    async def test_create_basic_scene_success(self, mock_scene, mock_search):
        executor = WorkflowExecutor(mock_scene, mock_search)

        mock_search.search_all.return_value = [MagicMock(name="Chair")]
        res = await executor.create_basic_scene(Prompt("cozy chair"))
        assert res is True
        mock_scene.cleanup_scene.assert_called_once()
        mock_scene.blender.execute_code.assert_called_once()
        mock_scene.setup_environment.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_basic_scene_no_assets(self, mock_scene, mock_search):
        executor = WorkflowExecutor(mock_scene, mock_search)

        mock_search.search_all.return_value = []
        res = await executor.create_basic_scene(Prompt("cozy chair"))
        assert res is False

    @pytest.mark.asyncio
    async def test_create_basic_scene_exception(self, mock_scene, mock_search):
        executor = WorkflowExecutor(mock_scene, mock_search)

        mock_scene.cleanup_scene = AsyncMock(side_effect=BlenderMCPError(ErrorMessage("Blender crash")))
        res = await executor.create_basic_scene(Prompt("cozy chair"))
        assert res is False

    @pytest.mark.asyncio
    async def test_generate_and_import_ai_asset_no_generation(self, mock_scene, mock_search):
        # Injected generation logic is None
        executor = WorkflowExecutor(mock_scene, mock_search, None)
        res = await executor.generate_and_import_ai_asset(ProviderName("hunyuan"), Prompt("sword"))
        assert "not configured" in str(res)

    @pytest.mark.asyncio
    async def test_generate_and_import_ai_asset_success(self, mock_scene, mock_search, mock_generation):
        executor = WorkflowExecutor(mock_scene, mock_search, mock_generation)

        mock_generation.start_generation.return_value = JobId("job_1")
        # Check status returns DONE
        mock_generation.check_status.return_value = MagicMock(status="DONE")

        res = await executor.generate_and_import_ai_asset(ProviderName("hunyuan"), Prompt("sword"))
        assert "generated and imported successfully" in str(res)

    @pytest.mark.asyncio
    async def test_generate_and_import_ai_asset_failure_status(self, mock_scene, mock_search, mock_generation):
        executor = WorkflowExecutor(mock_scene, mock_search, mock_generation)

        mock_generation.start_generation.return_value = JobId("job_1")
        # Check status returns FAILED
        mock_generation.check_status.return_value = MagicMock(status="FAILED")

        res = await executor.generate_and_import_ai_asset(ProviderName("hunyuan"), Prompt("sword"))
        assert "Generation failed" in str(res)

    @pytest.mark.asyncio
    async def test_generate_and_import_ai_asset_timeout(self, mock_scene, mock_search, mock_generation):
        executor = WorkflowExecutor(mock_scene, mock_search, mock_generation)

        mock_generation.start_generation.return_value = JobId("job_1")
        # Always RUNNING
        mock_generation.check_status.return_value = MagicMock(status="RUNNING")

        # Mock sleep to avoid waiting 150 seconds
        async def dummy_sleep(delay):
            pass

        with patch("asyncio.sleep", dummy_sleep):
            res = await executor.generate_and_import_ai_asset(ProviderName("hunyuan"), Prompt("sword"))
            assert "timed out" in str(res)

    @pytest.mark.asyncio
    async def test_generate_and_import_ai_asset_exceptions(self, mock_scene, mock_search, mock_generation):
        executor = WorkflowExecutor(mock_scene, mock_search, mock_generation)

        # 1. ProviderError
        mock_generation.start_generation = AsyncMock(side_effect=ProviderError(ErrorMessage("API full")))
        res = await executor.generate_and_import_ai_asset(ProviderName("hunyuan"), Prompt("sword"))
        assert "API full" in str(res)

        # 2. BlenderMCPError during import
        mock_generation.start_generation = AsyncMock(return_value=JobId("job_1"))
        mock_generation.check_status.return_value = MagicMock(status="DONE")
        mock_scene.blender.execute_code = AsyncMock(side_effect=BlenderMCPError(ErrorMessage("Import failed")))
        res2 = await executor.generate_and_import_ai_asset(ProviderName("hunyuan"), Prompt("sword"))
        assert "Import failed" in str(res2)

        # 3. Generic Exception
        mock_generation.start_generation = AsyncMock(side_effect=Exception("System error"))
        res3 = await executor.generate_and_import_ai_asset(ProviderName("hunyuan"), Prompt("sword"))
        assert "Workflow failed" in str(res3)


class TestActionExecuteActions:
    """Tests for ActionExecuteActions capability dispatcher."""

    @pytest.mark.asyncio
    async def test_execute_unknown_action(self):
        dispatcher = ActionExecuteActions(orchestrator=MagicMock())
        res = await dispatcher.execute(ActionName("unknown_action_99"))
        assert "Unknown action" in str(res)

    @pytest.mark.asyncio
    async def test_execute_invalid_capability_format(self):
        dispatcher = ActionExecuteActions(orchestrator=MagicMock())
        with patch.object(dispatcher, "_get_command_spec", return_value={"capability": "InvalidFormatNoDot"}):
            res = await dispatcher.execute(ActionName("some_action"))
            assert "Invalid capability format" in str(res)

    @pytest.mark.asyncio
    async def test_execute_resolve_capability_error(self):
        dispatcher = ActionExecuteActions(orchestrator=MagicMock())
        with patch.object(dispatcher, "_get_command_spec", return_value={"capability": "BlenderPort.execute_code"}):
            with patch.object(dispatcher, "_resolve_capability", side_effect=Exception("DI resolution failed")):
                res = await dispatcher.execute(ActionName("some_action"))
                assert "DI resolution failed" in str(res)

    @pytest.mark.asyncio
    async def test_execute_no_capability_matched(self):
        dispatcher = ActionExecuteActions(orchestrator=MagicMock())
        with patch.object(dispatcher, "_get_command_spec", return_value={"capability": "NonexistentProtocol.method"}):
            res = await dispatcher.execute(ActionName("some_action"))
            assert "No capability matched" in str(res)

    @pytest.mark.asyncio
    async def test_execute_method_not_found(self):
        mock_orchestrator = MagicMock()
        mock_orchestrator.blender = MagicMock(spec=[])  # no methods
        dispatcher = ActionExecuteActions(orchestrator=mock_orchestrator)
        with patch.object(dispatcher, "_get_command_spec", return_value={"capability": "BlenderPort.nonexistent_method"}):
            res = await dispatcher.execute(ActionName("some_action"))
            assert "has no method" in str(res)

    @pytest.mark.asyncio
    async def test_execute_method_success_and_exception(self):
        mock_cap = MagicMock()
        async def dummy_method(**kwargs):
            if "fail" in kwargs:
                raise Exception("method exception")
            mock_res = MagicMock()
            mock_res.model_dump_json.return_value = '{"success": true}'
            return mock_res

        mock_cap.dummy = dummy_method

        mock_orchestrator = MagicMock()
        mock_orchestrator.operate_scene_capability = mock_cap

        dispatcher = ActionExecuteActions(orchestrator=mock_orchestrator)

        # 1. Success with Pydantic dump
        with patch.object(dispatcher, "_get_command_spec", return_value={"capability": "SceneOperateProtocol.dummy"}):
            res = await dispatcher.execute(ActionName("some_action"), args={"param": 1})
            assert "success" in str(res)

        # 2. Success with dict dump
        async def dict_method(**kwargs):
            return {"data": 123}
        mock_cap.dummy = dict_method
        with patch.object(dispatcher, "_get_command_spec", return_value={"capability": "SceneOperateProtocol.dummy"}):
            res2 = await dispatcher.execute(ActionName("some_action"))
            assert "123" in str(res2)

        # 3. Method exception
        async def fail_method(**kwargs):
            raise Exception("method failure")
        mock_cap.dummy = fail_method
        with patch.object(dispatcher, "_get_command_spec", return_value={"capability": "SceneOperateProtocol.dummy"}):
            res3 = await dispatcher.execute(ActionName("some_action"))
            assert "method failure" in str(res3)

    def test_resolve_all_capabilities(self):
        mock_orch = MagicMock()
        dispatcher = ActionExecuteActions(orchestrator=mock_orch)

        assert dispatcher._resolve_capability("BlenderPort") is mock_orch.blender
        assert dispatcher._resolve_capability("SceneOperateProtocol") is mock_orch.operate_scene_capability
        assert dispatcher._resolve_capability("AssetSearchProtocol") is mock_orch.search_asset_capability
        assert dispatcher._resolve_capability("AssetProviderPort") is mock_orch.search_asset_capability
        assert dispatcher._resolve_capability("GenerationProviderPort") is mock_orch.generate_ai_capability
        assert dispatcher._resolve_capability("ObjectOperateProtocol") is mock_orch.object_operate_capability
        assert dispatcher._resolve_capability("RenderOperateProtocol") is mock_orch.render_operate_capability
        assert dispatcher._resolve_capability("ImportExportProtocol") is mock_orch.import_export_capability
        assert dispatcher._resolve_capability("UnknownProtocol") is None

    @pytest.mark.asyncio
    async def test_execute_empty_action_name(self):
        dispatcher = ActionExecuteActions(orchestrator=MagicMock())
        res = await dispatcher.execute(ActionName(""))
        assert "cannot be empty" in str(res)

    @pytest.mark.asyncio
    async def test_execute_action_name_too_long(self):
        dispatcher = ActionExecuteActions(orchestrator=MagicMock())
        long_name = "a" * 101
        res = await dispatcher.execute(ActionName(long_name))
        assert "exceeds" in str(res)

    @pytest.mark.asyncio
    async def test_execute_action_name_invalid_format(self):
        dispatcher = ActionExecuteActions(orchestrator=MagicMock())
        res = await dispatcher.execute(ActionName("UPPERCASE_BAD"))
        assert "Invalid action name" in str(res)

    @pytest.mark.asyncio
    async def test_execute_non_dict_args(self):
        dispatcher = ActionExecuteActions(orchestrator=MagicMock())
        res = await dispatcher.execute(ActionName("get_scene_info"), args="not_a_dict")
        assert "must be a dictionary" in str(res)

    def test_serialize_result_plain_string(self):
        dispatcher = ActionExecuteActions(orchestrator=MagicMock())
        result = dispatcher._serialize_result("plain_string_result")
        assert result == "plain_string_result"

    def test_sanitize_args_strips_and_truncates(self):
        dispatcher = ActionExecuteActions(orchestrator=MagicMock())
        long_val = "x" * 60000
        args = {"key1": "  hello  ", "key2": long_val}
        sanitized = dispatcher._sanitize_args(args)
        assert sanitized["key1"] == "hello"
        assert len(sanitized["key2"]) == 50000
