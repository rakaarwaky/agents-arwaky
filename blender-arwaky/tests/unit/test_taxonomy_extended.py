"""Tests tambahan untuk taxonomy layer — menutup gap 100% target.

Mencakup:
- base_provider_vo.py (ProviderVO, AssetSearchRequestVO, dsb.)
- blender_asset_vo.py (AssetMetadata, ImportedAsset, factories)
- blender_ops_vo.py (BlenderOpsRecord dan variants)
"""
import pytest
from taxonomy.base_provider_vo import (
    ProviderVO,
    AssetSearchRequestVO,
    AssetMetadataVO,
    AssetSearchResponseVO,
    AssetDownloadRequestVO,
    AssetDownloadResponseVO,
    GenerationStartRequestVO,
    GenerationStartResponseVO,
    GenerationStatusRequestVO,
    GenerationStatusResponseVO,
    ImportGeneratedAssetRequestVO,
    ImportGeneratedAssetResponseVO,
)
from taxonomy.blender_asset_vo import (
    AssetMetadata,
    ImportedAsset,
    ASSET_TYPE_HDRIS,
    ASSET_TYPE_TEXTURES,
    ASSET_TYPE_MODELS,
    PROVIDER_POLYHAVEN,
    PROVIDER_SKETCHFAB,
    create_asset_id,
    create_provider_name,
)
from taxonomy.blender_ops_vo import (
    BlenderOpsVO,
    CleanupSceneRequestVO,
    CleanupSceneResponseVO,
    SetupEnvironmentRequestVO,
    SetupEnvironmentResponseVO,
    GetSceneInfoRequestVO,
    GetSceneInfoResponseVO,
    CreatePrimitiveRequestVO,
    CreatePrimitiveResponseVO,
    SetMaterialRequestVO,
    RenderRequestVO,
    RenderResponseVO,
    PlaceAssetRequestVO,
    PlaceAssetResponseVO,
    GetObjectInfoRequestVO,
    SetObjectTransformRequestVO,
    DeleteObjectRequestVO,
    ApplyModifierRequestVO,
    ImportGlbRequestVO,
    ImportGlbResponseVO,
    ExportModelRequestVO,
    ExportModelResponseVO,
    GetScreenshotRequestVO,
    ScreenshotResponseVO,
)
from taxonomy.blender_spatial_vo import Vector3D
from taxonomy.core_types_vo import (
    AssetId, AssetName, AssetType, ProviderName,
    ThumbnailUrl, ObjectName, FilePath, SuccessFlag,
    ErrorMessage, JobId, JobState, Progress, SearchQuery,
    AssetTypeFilter, ResultLimit, AssetCount,
)


# ─── base_provider_vo.py ──────────────────────────────────────────

class TestProviderVO:
    def test_get_contract_name(self):
        assert ProviderVO.get_contract_name() == "ProviderVO"

    def test_to_request_dict_default(self):
        class ConcreteVO(ProviderVO):
            pass
        assert ConcreteVO().to_request_dict() == {}


class TestAssetSearchRequestVO:
    def test_valid_request(self):
        req = AssetSearchRequestVO(
            query=SearchQuery("forest"),
            asset_type=AssetTypeFilter("hdris"),
            limit=ResultLimit(20),
        )
        assert req.query == "forest"
        assert req.limit == 20

    def test_empty_query_raises(self):
        with pytest.raises(Exception):
            AssetSearchRequestVO(query=SearchQuery("   "))

    def test_whitespace_stripped(self):
        req = AssetSearchRequestVO(query=SearchQuery("  rock  "))
        assert req.query == "rock"

    def test_default_limit(self):
        req = AssetSearchRequestVO(query=SearchQuery("tree"))
        assert req.limit == 10

    def test_default_asset_type(self):
        req = AssetSearchRequestVO(query=SearchQuery("lake"))
        assert req.asset_type == "all"


class TestAssetMetadataVO:
    def test_create_metadata(self):
        meta = AssetMetadataVO(
            id=AssetId("asset-001"),
            name=AssetName("Forest HDRI"),
            type=AssetType("hdris"),
            provider=ProviderName("polyhaven"),
            thumbnail_url=ThumbnailUrl("https://example.com/thumb.jpg"),
        )
        assert meta.id == "asset-001"
        assert meta.name == "Forest HDRI"
        assert meta.thumbnail_url == "https://example.com/thumb.jpg"

    def test_thumbnail_optional(self):
        meta = AssetMetadataVO(
            id=AssetId("a"),
            name=AssetName("X"),
            type=AssetType("textures"),
            provider=ProviderName("polyhaven"),
        )
        assert meta.thumbnail_url is None


class TestAssetSearchResponseVO:
    def test_create_response(self):
        resp = AssetSearchResponseVO(
            total=AssetCount(5),
            provider=ProviderName("polyhaven"),
        )
        assert resp.total == 5
        assert resp.assets == []

    def test_next_token_optional(self):
        resp = AssetSearchResponseVO(
            total=AssetCount(0),
            provider=ProviderName("sketchfab"),
        )
        assert resp.next_token is None


class TestAssetDownloadVOs:
    def test_download_request(self):
        req = AssetDownloadRequestVO(
            asset_id=AssetId("asset-x"),
            destination_path=FilePath("/tmp/asset.zip"),
        )
        assert req.asset_id == "asset-x"

    def test_download_response_success(self):
        resp = AssetDownloadResponseVO(
            success=SuccessFlag(True),
            file_path=FilePath("/tmp/asset.zip"),
        )
        assert resp.success is True
        assert resp.file_path == "/tmp/asset.zip"

    def test_download_response_failure(self):
        resp = AssetDownloadResponseVO(
            success=SuccessFlag(False),
            message=ErrorMessage("Download failed"),
        )
        assert resp.success is False
        assert "Download failed" in resp.message


class TestGenerationVOs:
    def test_generation_start_request(self):
        from taxonomy.core_types_vo import Prompt
        req = GenerationStartRequestVO(prompt=Prompt("a red dragon"))
        assert req.prompt == "a red dragon"

    def test_generation_start_response(self):
        resp = GenerationStartResponseVO(
            job_id=JobId("job-123"),
            status=JobState("PENDING"),
        )
        assert resp.job_id == "job-123"

    def test_generation_status_request(self):
        req = GenerationStatusRequestVO(job_id=JobId("job-456"))
        assert req.job_id == "job-456"

    def test_generation_status_response(self):
        resp = GenerationStatusResponseVO(
            job_id=JobId("job-789"),
            status=JobState("RUNNING"),
            progress=Progress(50.0),
        )
        assert resp.progress == 50.0
        assert resp.error is None

    def test_import_request(self):
        req = ImportGeneratedAssetRequestVO(
            asset_id=AssetId("gen-001"),
            object_name=ObjectName("Dragon"),
            location=Vector3D(0.0, 0.0, 0.0),
        )
        assert req.object_name == "Dragon"
        assert req.rotation is None

    def test_import_response(self):
        resp = ImportGeneratedAssetResponseVO(
            success=SuccessFlag(True),
            object_name=ObjectName("Dragon"),
            blender_id=ObjectName("Dragon.001"),
        )
        assert resp.success is True
        assert resp.message is None


# ─── blender_asset_vo.py ──────────────────────────────────────────

class TestBlenderAssetVO:
    def test_asset_type_constants(self):
        assert ASSET_TYPE_HDRIS == "hdris"
        assert ASSET_TYPE_TEXTURES == "textures"
        assert ASSET_TYPE_MODELS == "models"

    def test_provider_constants(self):
        assert "polyhaven" in PROVIDER_POLYHAVEN
        assert "sketchfab" in PROVIDER_SKETCHFAB

    def test_create_asset_id(self):
        aid = create_asset_id("forest_01")
        assert aid == "forest_01"

    def test_create_provider_name(self):
        p = create_provider_name("polyhaven")
        assert p == "polyhaven"

    def test_asset_metadata_dataclass(self):
        meta = AssetMetadata(
            id=AssetId("a001"),
            name=AssetName("Forest"),
            type=ASSET_TYPE_HDRIS,
            provider=PROVIDER_POLYHAVEN,
        )
        assert meta.id == "a001"
        assert meta.tags == []
        assert meta.thumbnail_url is None

    def test_asset_metadata_with_tags(self):
        from typing import cast
        from taxonomy.core_types_vo import TagList
        meta = AssetMetadata(
            id=AssetId("a002"),
            name=AssetName("Rock"),
            type=ASSET_TYPE_TEXTURES,
            provider=PROVIDER_POLYHAVEN,
            tags=cast(TagList, ["stone", "ground"]),
        )
        assert "stone" in meta.tags

    def test_imported_asset(self):
        asset = ImportedAsset(
            id=AssetId("imp-1"),
            name=ObjectName("DragonMesh"),
            blender_id=ObjectName("DragonMesh.001"),
        )
        assert asset.name == "DragonMesh"
        assert asset.blender_id == "DragonMesh.001"

    def test_asset_metadata_frozen(self):
        """AssetMetadata is a frozen dataclass — mutation should fail."""
        meta = AssetMetadata(
            id=AssetId("x"),
            name=AssetName("X"),
            type=ASSET_TYPE_MODELS,
            provider=PROVIDER_SKETCHFAB,
        )
        with pytest.raises((AttributeError, TypeError)):
            meta.id = AssetId("y")  # type: ignore


# ─── blender_ops_vo.py ────────────────────────────────────────────

class TestBlenderOpsVO:
    """Tests for BlenderOpsVO and concrete VO DTOs."""

    def test_get_contract_name(self):
        assert BlenderOpsVO.get_contract_name() == "BlenderOpsVO"

    def test_to_request_dict_default(self):
        class ConcreteOps(BlenderOpsVO):
            pass
        assert ConcreteOps().to_request_dict() == {}

    def test_cleanup_scene_request_default_mode(self):
        req = CleanupSceneRequestVO()
        assert req.mode == "all"

    def test_cleanup_scene_request_invalid_mode(self):
        with pytest.raises(Exception):
            CleanupSceneRequestVO(mode="invalid")  # type: ignore

    def test_cleanup_scene_request_valid_modes(self):
        for mode in ["all", "objects", "meshes"]:
            req = CleanupSceneRequestVO(mode=mode)  # type: ignore
            assert req.mode == mode

    def test_cleanup_scene_response(self):
        from taxonomy.core_types_vo import ObjectCount
        resp = CleanupSceneResponseVO(
            success=SuccessFlag(True),
            objects_removed=ObjectCount(5),
            message="Cleaned",
        )
        assert resp.objects_removed == 5
        assert resp.success is True

    def test_setup_environment_request(self):
        from taxonomy.core_types_vo import HdriId, LightStrength
        req = SetupEnvironmentRequestVO(
            hdri_id=HdriId("forest_01"),
            strength=LightStrength(2.0),
        )
        assert req.hdri_id == "forest_01"
        assert req.strength == 2.0

    def test_get_scene_info_request(self):
        req = GetSceneInfoRequestVO()
        assert req is not None

    def test_get_scene_info_response(self):
        resp = GetSceneInfoResponseVO(
            success=SuccessFlag(True),
            scene_info=None,
        )
        assert resp.success is True

    def test_create_primitive_request(self):
        from taxonomy.core_types_vo import PrimitiveType, CoordinateList
        req = CreatePrimitiveRequestVO(
            primitive_type=PrimitiveType("SPHERE"),
            location=CoordinateList([0.0, 0.0, 0.0]),
            name=ObjectName("MySphere"),
        )
        assert req.primitive_type == "SPHERE"
        assert req.name == "MySphere"

    def test_create_primitive_response(self):
        from taxonomy.core_types_vo import PrimitiveType
        resp = CreatePrimitiveResponseVO(
            success=SuccessFlag(True),
            object_name=ObjectName("Sphere"),
            primitive_type=PrimitiveType("SPHERE"),
        )
        assert resp.success is True

    def test_set_material_request(self):
        from taxonomy.core_types_vo import MaterialName
        req = SetMaterialRequestVO(
            object_name=ObjectName("Cube"),
            material_name=MaterialName("Metal"),
        )
        assert req.material_name == "Metal"

    def test_render_request(self):
        from taxonomy.core_types_vo import ResolutionX, ResolutionY
        req = RenderRequestVO(
            output_path=FilePath("/tmp/render.png"),
            resolution_x=ResolutionX(1280),
            resolution_y=ResolutionY(720),
        )
        assert req.resolution_x == 1280
        assert req.resolution_y == 720

    def test_render_response(self):
        resp = RenderResponseVO(
            success=SuccessFlag(True),
            image_path=FilePath("/tmp/render.png"),
            render_time=2.5,
        )
        assert resp.render_time == 2.5

    def test_place_asset_request(self):
        from taxonomy.core_types_vo import CoordinateList
        req = PlaceAssetRequestVO(
            asset_id=AssetId("asset-001"),
            location=CoordinateList([1.0, 2.0, 3.0]),
        )
        assert req.asset_id == "asset-001"

    def test_place_asset_invalid_location(self):
        from taxonomy.core_types_vo import CoordinateList
        with pytest.raises(Exception):
            PlaceAssetRequestVO(
                asset_id=AssetId("asset-001"),
                location=CoordinateList([1.0, 2.0]),  # only 2 elements
            )

    def test_get_object_info_request(self):
        req = GetObjectInfoRequestVO(object_name=ObjectName("Cube"))
        assert req.object_name == "Cube"

    def test_set_object_transform_request(self):
        from taxonomy.core_types_vo import CoordinateList
        req = SetObjectTransformRequestVO(
            object_name=ObjectName("Cube"),
            location=CoordinateList([1.0, 2.0, 3.0]),
        )
        assert req.object_name == "Cube"

    def test_delete_object_request(self):
        req = DeleteObjectRequestVO(object_name=ObjectName("Cube"))
        assert req.object_name == "Cube"

    def test_apply_modifier_request(self):
        from taxonomy.core_types_vo import ModifierName
        req = ApplyModifierRequestVO(
            object_name=ObjectName("Cube"),
            modifier_name=ModifierName("Subdivision"),
        )
        assert req.modifier_name == "Subdivision"

    def test_import_glb_request(self):
        req = ImportGlbRequestVO(
            file_path=FilePath("/tmp/model.glb"),
            object_name=ObjectName("ImportedModel"),
        )
        assert req.file_path == "/tmp/model.glb"

    def test_import_glb_response(self):
        resp = ImportGlbResponseVO(
            success=SuccessFlag(True),
            object_name=ObjectName("Model"),
            file_path=FilePath("/tmp/model.glb"),
        )
        assert resp.success is True

    def test_export_model_request(self):
        from taxonomy.core_types_vo import ExportFormat
        req = ExportModelRequestVO(
            object_name=ObjectName("Cube"),
            file_path=FilePath("/tmp/export.glb"),
            export_format=ExportFormat("glb"),
        )
        assert req.export_format == "glb"

    def test_export_model_response(self):
        resp = ExportModelResponseVO(
            success=SuccessFlag(True),
            file_path=FilePath("/tmp/export.glb"),
            object_name=ObjectName("Cube"),
            message="Exported successfully",
        )
        assert resp.success is True
        assert resp.object_name == "Cube"

    def test_setup_environment_response(self):
        resp = SetupEnvironmentResponseVO(
            success=SuccessFlag(True),
            hdri_path=FilePath("/tmp/env.hdr"),
            message="Environment setup successful",
        )
        assert resp.success is True
        assert resp.hdri_path == "/tmp/env.hdr"

    def test_screenshot_request_and_response(self):
        from taxonomy.core_types_vo import MaxSize, ImageFormat, ResolutionX, ResolutionY
        req = GetScreenshotRequestVO(
            max_size=MaxSize(1024),
            format=ImageFormat("jpeg"),
        )
        assert req.max_size == 1024
        assert req.format == "jpeg"

        resp = ScreenshotResponseVO(
            success=SuccessFlag(True),
            image_data=b"raw_bytes_here",
            format=ImageFormat("jpeg"),
            width=ResolutionX(1024),
            height=ResolutionY(768),
        )
        assert resp.success is True
        assert resp.image_data == b"raw_bytes_here"

    def test_place_asset_request_with_invalid_scale_and_rotation(self):
        from taxonomy.core_types_vo import CoordinateList
        with pytest.raises(Exception):
            PlaceAssetRequestVO(
                asset_id=AssetId("asset-1"),
                location=CoordinateList([0.0, 0.0, 0.0]),
                scale=CoordinateList([1.0, 1.0]),  # only 2 elements
            )
        
        with pytest.raises(Exception):
            PlaceAssetRequestVO(
                asset_id=AssetId("asset-1"),
                location=CoordinateList([0.0, 0.0, 0.0]),
                rotation=CoordinateList([0.0]),  # only 1 element
            )


class TestSceneAggregateExtended:
    """Extra test cases for SceneAggregate to close taxonomy gaps."""

    def test_update_object_with_same_name_and_invalid_attribute(self):
        from taxonomy.blender_scene_entity import SceneAggregate
        from taxonomy.blender_object_entity import BlenderObject, OBJECT_TYPE_MESH
        from taxonomy.blender_spatial_vo import Vector3D
        
        scene = SceneAggregate()
        obj = BlenderObject(
            name=ObjectName("O1"),
            type=OBJECT_TYPE_MESH,
            location=Vector3D(0, 0, 0),
            rotation=Vector3D(0, 0, 0),
            scale=Vector3D(1, 1, 1),
        )
        scene.add_object(obj)

        # 1. Update with the same name (should succeed, not throw duplicate name error)
        updated_obj = scene.update_object(obj.id, name="O1")
        assert updated_obj.name == "O1"

        # 2. Update with invalid attribute that the object does not have
        # (should run successfully but NOT set the attribute on the object)
        scene.update_object(obj.id, nonexistent_attr="boom")
        assert not hasattr(obj, "nonexistent_attr")

    def test_place_asset_request_coordinate_validator_manual_trigger(self):
        from taxonomy.blender_ops_vo import PlaceAssetRequestVO
        from unittest.mock import MagicMock
        mock_info = MagicMock()
        mock_info.field_name = "scale"
        with pytest.raises(ValueError) as exc_info:
            PlaceAssetRequestVO.validate_coord([1.0, 2.0], mock_info)
        assert "must have exactly 3 elements" in str(exc_info.value)

    def test_find_object_not_found_throws_validation_error(self):
        from taxonomy.blender_scene_entity import SceneAggregate, SceneValidationError
        from uuid import uuid4
        scene = SceneAggregate()
        with pytest.raises(SceneValidationError) as exc_info:
            scene.get_object(uuid4())
        assert "not found in scene" in str(exc_info.value)


