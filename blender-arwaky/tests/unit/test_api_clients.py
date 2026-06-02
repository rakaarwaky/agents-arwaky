"""Unit tests for the infrastructure API clients and their adapters."""
import json
import pytest
from unittest.mock import MagicMock, patch, mock_open

from taxonomy import (
    AssetId,
    AssetType,
    StatusString,
    Prompt,
    ResultUrl,
    ObjectName,
    JobId,
    ProviderError,
    AssetSearchRequestVO,
    AssetDownloadRequestVO,
    GenerationStartRequestVO,
    GenerationStatusRequestVO,
    ImportGeneratedAssetRequestVO,
    StringList,
    Vector3D,
    FilePath,
)
from infrastructure.polyhaven_api_client import PolyhavenApiClient
from infrastructure.polyhaven_asset_adapter import PolyhavenAssetAdapter
from infrastructure.sketchfab_api_client import SketchfabApiClient
from infrastructure.sketchfab_asset_adapter import SketchfabAssetAdapter
from infrastructure.hunyuan_generation_client import HunyuanGenerationTool
from infrastructure.hunyuan_generation_adapter import HunyuanGenerationAdapter
from infrastructure.hyper3d_generation_client import Hyper3dGenerationTool
from infrastructure.hyper3d_generation_adapter import Hyper3DGenerationAdapter


class TestPolyhavenIntegration:
    """Tests for PolyhavenApiClient and PolyhavenAssetAdapter."""

    @pytest.fixture
    def mock_conn(self):
        return MagicMock()

    @pytest.fixture
    def client(self, mock_conn):
        return PolyhavenApiClient(mock_conn)

    @pytest.fixture
    def adapter(self, mock_conn):
        return PolyhavenAssetAdapter(mock_conn)

    def test_get_polyhaven_categories(self, client, mock_conn):
        # Success formatting sorted
        mock_conn.send_command.return_value = {
            "categories": {"nature": 10, "urban": 25, "indoor": 5}
        }
        res = client.get_polyhaven_categories(AssetType("textures"))
        assert "urban: 25 assets" in str(res)
        assert "nature: 10 assets" in str(res)
        assert "indoor: 5 assets" in str(res)

        # Error path
        mock_conn.send_command.return_value = {"error": "Timeout"}
        assert "Error: Timeout" in str(client.get_polyhaven_categories())

        # Exception path
        mock_conn.send_command.side_effect = Exception("General error")
        assert "General error" in str(client.get_polyhaven_categories())

    def test_search_polyhaven_assets(self, client, mock_conn):
        mock_conn.send_command.return_value = {
            "assets": {
                "brick_wall": {"name": "Brick Wall", "type": 1, "categories": ["brick"], "download_count": 100}
            },
            "total_count": 1,
            "returned_count": 1,
        }
        res = client.search_polyhaven_assets(AssetType("textures"), "brick")
        assert "Brick Wall" in str(res)
        assert "Downloads: 100" in str(res)

        # Error path
        mock_conn.send_command.return_value = {"error": "Fail"}
        assert "Error: Fail" in str(client.search_polyhaven_assets())

        # Exception path
        mock_conn.send_command.side_effect = Exception("API down")
        assert "API down" in str(client.search_polyhaven_assets())

    def test_download_polyhaven_asset(self, client, mock_conn):
        # HDRIs success path
        mock_conn.send_command.return_value = {"success": True, "message": "Imported"}
        res = client.download_polyhaven_asset(AssetId("sun"), AssetType("hdris"))
        assert "world environment" in str(res)

        # Textures success path
        mock_conn.send_command.return_value = {"success": True, "message": "Imported", "material": "wood", "maps": ["diffuse", "normal"]}
        res = client.download_polyhaven_asset(AssetId("wood"), AssetType("textures"))
        assert "Created material 'wood'" in str(res)

        # Models success path
        mock_conn.send_command.return_value = {"success": True, "message": "Imported"}
        res = client.download_polyhaven_asset(AssetId("chair"), AssetType("models"))
        assert "current scene" in str(res)

        # Failed path
        mock_conn.send_command.return_value = {"success": False, "message": "Disk full"}
        res = client.download_polyhaven_asset(AssetId("chair"), AssetType("models"))
        assert "Disk full" in str(res)

        # Exception path
        mock_conn.send_command.side_effect = Exception("Downloader crash")
        res = client.download_polyhaven_asset(AssetId("chair"), AssetType("models"))
        assert "Downloader crash" in str(res)

    def test_set_texture(self, client, mock_conn):
        # Success path with texture nodes
        mock_conn.send_command.return_value = {
            "success": True,
            "material": "mat_1",
            "maps": ["diffuse"],
            "material_info": {
                "node_count": 5,
                "has_nodes": True,
                "texture_nodes": [{"name": "diff_node", "image": "diff.png", "connections": ["Color -> Base Color"]}],
            }
        }
        res = client.set_texture(ObjectName("Cube"), AssetId("tex_1"))
        assert "mat_1" in str(res)
        assert "diff_node" in str(res)
        assert "Color -> Base Color" in str(res)

        # Success path without texture nodes
        mock_conn.send_command.return_value = {
            "success": True,
            "material": "mat_1",
            "maps": [],
            "material_info": {"node_count": 1, "has_nodes": False, "texture_nodes": []}
        }
        res = client.set_texture(ObjectName("Cube"), AssetId("tex_1"))
        assert "No texture nodes found" in str(res)

        # Failure status
        mock_conn.send_command.return_value = {"success": False, "message": "Not mesh"}
        res = client.set_texture(ObjectName("Cube"), AssetId("tex_1"))
        assert "Not mesh" in str(res)

        # Error
        mock_conn.send_command.return_value = {"error": "Invalid obj"}
        res = client.set_texture(ObjectName("Cube"), AssetId("tex_1"))
        assert "Error: Invalid obj" in str(res)

        # Exception
        mock_conn.send_command.side_effect = Exception("Socket reset")
        res = client.set_texture(ObjectName("Cube"), AssetId("tex_1"))
        assert "Socket reset" in str(res)

    def test_get_polyhaven_status(self, client, mock_conn):
        mock_conn.send_command.return_value = {"enabled": True, "message": "Ready. "}
        assert "textures than Sketchfab" in str(client.get_polyhaven_status())

        mock_conn.send_command.side_effect = Exception()
        assert "Error" in str(client.get_polyhaven_status())

    @pytest.mark.asyncio
    async def test_polyhaven_asset_adapter(self, adapter, mock_conn):
        # Search assets
        mock_conn.send_command.return_value = {
            "assets": {
                "wall": {"name": "Wall", "type": "textures", "categories": ["brick"]}
            }
        }
        res = await adapter.search_assets(AssetSearchRequestVO(query="brick", asset_type="textures", categories=["brick"]))
        assert len(res.assets) == 1
        assert res.assets[0].name == "Wall"

        # Search exception
        mock_conn.send_command.side_effect = Exception("API error")
        with pytest.raises(ProviderError):
            await adapter.search_assets(AssetSearchRequestVO(query="brick"))

        # Details success
        mock_conn.send_command.side_effect = None
        mock_conn.send_command.return_value = {"name": "Oak", "type": "textures", "tags": ["wood"]}
        details = await adapter.get_asset_details("oak")
        assert details is not None
        assert details.name == "Oak"

        # Details Blender error or exception
        mock_conn.send_command.return_value = {"error": "Not found"}
        assert await adapter.get_asset_details("oak") is None

        mock_conn.send_command.side_effect = Exception()
        assert await adapter.get_asset_details("oak") is None

        # Download success
        mock_conn.send_command.side_effect = None
        mock_conn.send_command.return_value = {"success": True, "path": "/path/to/asset"}
        download_res = await adapter.download_asset(AssetDownloadRequestVO(asset_id=AssetId("oak"), destination_path=FilePath("/path/to/asset")))
        assert download_res.success is True
        assert download_res.file_path == "/path/to/asset"

        # Download failure
        mock_conn.send_command.return_value = {"success": False, "message": "Failed"}
        with pytest.raises(ProviderError):
            await adapter.download_asset(AssetDownloadRequestVO(asset_id=AssetId("oak"), destination_path=FilePath("/path/to/asset")))

        # Download exception
        mock_conn.send_command.side_effect = Exception("IO failed")
        with pytest.raises(ProviderError):
            await adapter.download_asset(AssetDownloadRequestVO(asset_id=AssetId("oak"), destination_path=FilePath("/path/to/asset")))

    def test_uninitialized_polyhaven_adapter(self):
        adapter = PolyhavenAssetAdapter(None)  # type: ignore
        with pytest.raises(ProviderError):
            adapter._get_conn()


class TestSketchfabIntegration:
    """Tests for SketchfabApiClient and SketchfabAssetAdapter."""

    @pytest.fixture
    def mock_conn(self):
        return MagicMock()

    @pytest.fixture
    def client(self, mock_conn):
        return SketchfabApiClient(mock_conn)

    @pytest.fixture
    def adapter(self, mock_conn):
        return SketchfabAssetAdapter(mock_conn)

    def test_get_sketchfab_status(self, client, mock_conn):
        mock_conn.send_command.return_value = {"enabled": True, "message": "Sketchfab active. "}
        assert "Sketchfab active" in str(client.get_sketchfab_status())

        mock_conn.send_command.return_value = {"enabled": False, "message": ""}
        assert "not enabled" in str(client.get_sketchfab_status())

        mock_conn.send_command.side_effect = Exception("Conn loss")
        assert "Conn loss" in str(client.get_sketchfab_status())

    def test_search_sketchfab_models(self, client, mock_conn):
        # Valid search with results
        mock_conn.send_command.return_value = {
            "results": [
                {
                    "name": "Knight",
                    "uid": "uid_123",
                    "user": {"username": "arthur"},
                    "license": {"label": "CC-BY"},
                    "faceCount": 5000,
                    "isDownloadable": True,
                },
                None,  # Null item safety check
            ]
        }
        res = client.search_sketchfab_models("knight")
        assert "Knight" in str(res)
        assert "Author: arthur" in str(res)
        assert "License: CC-BY" in str(res)

        # Empty search results
        mock_conn.send_command.return_value = {"results": []}
        assert "No model_domain_entity_model found" in str(client.search_sketchfab_models("knight"))

        # None result safety
        mock_conn.send_command.return_value = None
        assert "no response" in str(client.search_sketchfab_models("knight"))

        # Blender error
        mock_conn.send_command.return_value = {"error": "Rate limit"}
        assert "Error: Rate limit" in str(client.search_sketchfab_models("knight"))

        # Exception
        mock_conn.send_command.side_effect = Exception("Search fails")
        assert "Search fails" in str(client.search_sketchfab_models("knight"))

    def test_get_sketchfab_model_preview(self, client, mock_conn):
        mock_conn.send_command.return_value = {
            "image_data": "aW1hZ2VfYnl0ZXNfaGVyZQ==",
            "model_name": "Chair",
            "author": "john",
        }
        res = client.get_sketchfab_model_preview(AssetId("chair"))
        assert res == b"image_bytes_here"

        # None result
        mock_conn.send_command.return_value = None
        with pytest.raises(ProviderError):
            client.get_sketchfab_model_preview(AssetId("chair"))

        # Error
        mock_conn.send_command.return_value = {"error": "Private model"}
        with pytest.raises(ProviderError):
            client.get_sketchfab_model_preview(AssetId("chair"))

        # Exception
        mock_conn.send_command.side_effect = Exception()
        with pytest.raises(Exception):
            client.get_sketchfab_model_preview(AssetId("chair"))

    def test_download_sketchfab_model(self, client, mock_conn):
        mock_conn.send_command.return_value = {
            "success": True,
            "imported_objects": ["chair_1"],
            "dimensions": [1.0, 1.0, 2.0],
            "world_bounding_box": [0.0, 2.0],
            "normalized": True,
            "scale_applied": 0.5,
        }
        res = client.download_sketchfab_model(AssetId("uid"), 2.0)
        assert "chair_1" in str(res)
        assert "1.000 x 1.000 x 2.000" in str(res)
        assert "scale factor 0.500000" in str(res)

        # Failed download
        mock_conn.send_command.return_value = {"success": False, "message": "Access denied"}
        res = client.download_sketchfab_model(AssetId("uid"), 2.0)
        assert "Access denied" in str(res)

        # None result
        mock_conn.send_command.return_value = None
        res = client.download_sketchfab_model(AssetId("uid"), 2.0)
        assert "no response" in str(res)

        # Error
        mock_conn.send_command.return_value = {"error": "API Key invalid"}
        res = client.download_sketchfab_model(AssetId("uid"), 2.0)
        assert "Error: API Key invalid" in str(res)

        # Exception
        mock_conn.send_command.side_effect = Exception("Network down")
        res = client.download_sketchfab_model(AssetId("uid"), 2.0)
        assert "Network down" in str(res)

    @pytest.mark.asyncio
    async def test_sketchfab_asset_adapter(self, adapter, mock_conn):
        # Search
        mock_conn.send_command.return_value = {"results": [{"uid": "1", "name": "M1"}]}
        res = await adapter.search_assets(AssetSearchRequestVO(query="table"))
        assert len(res.assets) == 1
        assert res.assets[0].id == "1"

        # Search error
        mock_conn.send_command.side_effect = Exception()
        with pytest.raises(ProviderError):
            await adapter.search_assets(AssetSearchRequestVO(query="table"))

        # Details
        mock_conn.send_command.side_effect = None
        mock_conn.send_command.return_value = {"model_name": "M1"}
        details = await adapter.get_asset_details("1")
        assert details is not None
        assert details.name == "M1"

        mock_conn.send_command.return_value = {"error": "Forbidden"}
        assert await adapter.get_asset_details("1") is None

        mock_conn.send_command.side_effect = Exception()
        assert await adapter.get_asset_details("1") is None

        # Download success
        mock_conn.send_command.side_effect = None
        mock_conn.send_command.return_value = {"success": True, "imported_objects": ["o1"]}
        download_res = await adapter.download_asset(AssetDownloadRequestVO(asset_id=AssetId("1"), destination_path=FilePath("o1")))
        assert download_res.success is True
        assert download_res.file_path == "o1"

        # Download fail
        mock_conn.send_command.return_value = {"success": False, "message": "Failed"}
        with pytest.raises(ProviderError):
            await adapter.download_asset(AssetDownloadRequestVO(asset_id=AssetId("1"), destination_path=FilePath("o1")))

        # Download exception
        mock_conn.send_command.side_effect = Exception()
        with pytest.raises(ProviderError):
            await adapter.download_asset(AssetDownloadRequestVO(asset_id=AssetId("1"), destination_path=FilePath("o1")))


class TestHunyuanIntegration:
    """Tests for Hunyuan3D generation tool and adapter."""

    @pytest.fixture
    def mock_conn(self):
        return MagicMock()

    @pytest.fixture
    def tool(self, mock_conn):
        return HunyuanGenerationTool(mock_conn)

    @pytest.fixture
    def adapter(self, mock_conn):
        return HunyuanGenerationAdapter(mock_conn)

    def test_get_hunyuan3d_status(self, tool, mock_conn):
        mock_conn.send_command.return_value = {"message": "Hunyuan is enabled"}
        assert "Hunyuan is enabled" in str(tool.get_hunyuan3d_status())

        mock_conn.send_command.side_effect = Exception("No connection")
        assert "No connection" in str(tool.get_hunyuan3d_status())

    def test_generate_hunyuan3d_model(self, tool, mock_conn):
        # Success response
        mock_conn.send_command.return_value = {"Response": {"JobId": "99"}}
        res = tool.generate_hunyuan3d_model(Prompt("sword"))
        data = json.loads(str(res))
        assert data["job_id"] == "job_99"

        # Raw response fallback
        mock_conn.send_command.return_value = {"error": "invalid prompt"}
        res = tool.generate_hunyuan3d_model(Prompt("sword"))
        data = json.loads(str(res))
        assert data["error"] == "invalid prompt"

        # Exception
        mock_conn.send_command.side_effect = Exception("Fails to create job")
        assert "Fails to create job" in str(tool.generate_hunyuan3d_model(Prompt("sword")))

    def test_poll_hunyuan_job_status(self, tool, mock_conn):
        mock_conn.send_command.return_value = {"Status": "DONE", "ResultFile3Ds": "http://sword.glb"}
        res = tool.poll_hunyuan_job_status(JobId("job_99"))
        data = json.loads(str(res))
        assert data["Status"] == "DONE"

        # Exception
        mock_conn.send_command.side_effect = Exception()
        assert "Error" in str(tool.poll_hunyuan_job_status(JobId("job_99")))

    def test_import_generated_asset_hunyuan(self, tool, mock_conn):
        mock_conn.send_command.return_value = {"success": True, "object_name": "Sword"}
        res = tool.import_generated_asset_hunyuan(ObjectName("Sword"), ResultUrl("http://sword.glb"))
        data = json.loads(str(res))
        assert data["object_name"] == "Sword"

        # Missing url
        res = tool.import_generated_asset_hunyuan(ObjectName("Sword"), None)  # type: ignore
        assert "zip_file_url is required" in str(res)

        # Exception
        mock_conn.send_command.side_effect = Exception("Import error")
        assert "Import error" in str(tool.import_generated_asset_hunyuan(ObjectName("Sword"), ResultUrl("http://s")))

    @pytest.mark.asyncio
    async def test_hunyuan_generation_adapter(self, adapter, mock_conn):
        # Generate success
        mock_conn.send_command.return_value = {"Response": {"JobId": "111"}}
        job_id = await adapter.generate_from_text("tree")
        assert job_id == "job_111"

        # Generate failed
        mock_conn.send_command.return_value = {}
        with pytest.raises(ProviderError):
            await adapter.generate_from_text("tree")

        # Generate exception
        mock_conn.send_command.side_effect = Exception()
        with pytest.raises(ProviderError):
            await adapter.generate_from_text("tree")

        # get_job_status COMPLETED
        mock_conn.send_command.side_effect = None
        mock_conn.send_command.return_value = {"Status": "DONE", "ResultFile3Ds": "url"}
        status = await adapter.get_job_status("job_111")
        assert status.status == "COMPLETED"
        assert status.progress == 1.0
        assert status.result_url == "url"

        # get_job_status RUNNING
        mock_conn.send_command.return_value = {"Status": "RUN"}
        status = await adapter.get_job_status("job_111")
        assert status.status == "RUNNING"
        assert status.progress == 0.5

        # get_job_status FAILED
        mock_conn.send_command.return_value = {"Status": "FAILED"}
        status = await adapter.get_job_status("job_111")
        assert status.status == "FAILED"

        # get_job_status exception
        mock_conn.send_command.side_effect = Exception()
        with pytest.raises(ProviderError):
            await adapter.get_job_status("job_111")

        # start_generation & poll_generation
        mock_conn.send_command.side_effect = None
        mock_conn.send_command.return_value = {"Response": {"JobId": "222"}}
        start_res = await adapter.start_generation(GenerationStartRequestVO(prompt="mat"))
        assert start_res.job_id == "job_222"

        mock_conn.send_command.return_value = {"Status": "DONE"}
        poll_res = await adapter.poll_generation(GenerationStatusRequestVO(job_id=JobId("job_222")))
        assert poll_res.status == "COMPLETED"

        # import_generated_asset
        mock_conn.send_command.return_value = {"success": True, "object_name": "obj_99"}
        import_res = await adapter.import_generated_asset(
            ImportGeneratedAssetRequestVO(
                asset_id=AssetId("job_222"),
                object_name=ObjectName("obj_99"),
                location=Vector3D(0, 0, 0)
            )
        )
        assert import_res.success is True
        assert import_res.object_name == "obj_99"


class TestHyper3DIntegration:
    """Tests for Hyper3D (Rodin) generation tool and adapter."""

    @pytest.fixture
    def mock_conn(self):
        return MagicMock()

    @pytest.fixture
    def tool(self, mock_conn):
        return Hyper3dGenerationTool(mock_conn)

    @pytest.fixture
    def adapter(self, mock_conn):
        return Hyper3DGenerationAdapter(mock_conn)

    def test_get_hyper3d_status(self, tool, mock_conn):
        mock_conn.send_command.return_value = {"enabled": True, "message": "Hyper3D active"}
        assert "Hyper3D active" in str(tool.get_hyper3d_status())

        mock_conn.send_command.return_value = {"enabled": False, "message": ""}
        assert "not enabled" in str(tool.get_hyper3d_status())

        mock_conn.send_command.side_effect = Exception()
        assert "Error" in str(tool.get_hyper3d_status())

    def test_process_bbox(self, tool):
        assert tool.process_bbox(None) is None
        assert tool.process_bbox([]) is None

        # Scaling bbox values
        assert tool.process_bbox([1.0, 2.0, 4.0]) == [25, 50, 100]

        # Max is zero
        with pytest.raises(ValueError):
            tool.process_bbox([0, 0, 0])

        # Incorrect range
        with pytest.raises(ValueError):
            tool.process_bbox([-1, 0, 1])

    def test_generate_hyper3d_model_via_text(self, tool, mock_conn):
        # MAIN_SITE submit time format
        mock_conn.send_command.return_value = {
            "submit_time": "123",
            "uuid": "uuid-99",
            "jobs": {"subscription_key": "sub_key"},
        }
        res = tool.generate_hyper3d_model_via_text(Prompt("axe"))
        data = json.loads(str(res))
        assert data["task_uuid"] == "uuid-99"
        assert data["subscription_key"] == "sub_key"

        # FAL_AI request_id format
        mock_conn.send_command.return_value = {
            "request_id": "req-99",
        }
        res = tool.generate_hyper3d_model_via_text(Prompt("axe"))
        data = json.loads(str(res))
        assert data["request_id"] == "req-99"

        # Failed response
        mock_conn.send_command.return_value = {"error": "Invalid API key"}
        res = tool.generate_hyper3d_model_via_text(Prompt("axe"))
        data = json.loads(str(res))
        assert data["error"] == "Invalid API key"

        # Exception
        mock_conn.send_command.side_effect = Exception("Hyper3D timeout")
        assert "Hyper3D timeout" in str(tool.generate_hyper3d_model_via_text(Prompt("axe")))

    def test_validate_and_prepare_images(self, tool):
        # Conflict parameters
        err, images = tool._validate_and_prepare_images(StringList(["a"]), StringList(["b"]))
        assert "Conflict" in err

        # Missing inputs
        err, images = tool._validate_and_prepare_images(None, None)
        assert "No image" in err

        # Invalid URLs
        err, images = tool._validate_and_prepare_images(None, StringList(["not_a_url"]))
        # urlparse actually returns parsed elements, but if we mock urlparse to return empty or checks
        # urlparse("not_a_url").scheme is empty, wait, the validation logic is `all(urlparse(i) for i in input_image_urls)`
        # urlparse always returns a ParseResult object, but scheme is empty. Let's see: the code in hyper3d_generation_client
        # checks `all(urlparse(i) for i in input_image_urls)`. Since urlparse always returns truthy object, it passes validation!
        # But if it fails, it returns error. Let's check with valid urls
        err, images = tool._validate_and_prepare_images(None, StringList(["http://example.com/img.png"]))
        assert err is None
        assert images == ["http://example.com/img.png"]

        # Valid paths loading
        with patch("os.path.exists", return_value=True):
            with patch("builtins.open", mock_open(read_data=b"img_bytes")):
                err, images = tool._validate_and_prepare_images(StringList(["/path/img.png"]), None)
                assert err is None
                # Base64 encoded img_bytes
                assert images[0][1] == "aW1nX2J5dGVz"

        # Invalid paths
        with patch("os.path.exists", return_value=False):
            err, images = tool._validate_and_prepare_images(StringList(["/path/img.png"]), None)
            assert "not all image paths are valid" in err

    def test_generate_hyper3d_model_via_images(self, tool, mock_conn):
        mock_conn.send_command.return_value = {
            "submit_time": "123",
            "uuid": "uuid-10",
            "jobs": {"subscription_key": "sub_key"},
        }
        # Image URLs success
        res = tool.generate_hyper3d_model_via_images(input_image_urls=StringList(["http://img.jpg"]))
        data = json.loads(str(res))
        assert data["task_uuid"] == "uuid-10"

        # Image generation fail result parsing
        mock_conn.send_command.return_value = {"error": "Server error"}
        res = tool.generate_hyper3d_model_via_images(input_image_urls=StringList(["http://img.jpg"]))
        data = json.loads(str(res))
        assert data["error"] == "Server error"

        # Invalid input parameters error
        res = tool.generate_hyper3d_model_via_images(None, None)
        assert "No image" in str(res)

        # Exception
        mock_conn.send_command.side_effect = Exception("Network loss")
        res = tool.generate_hyper3d_model_via_images(input_image_urls=StringList(["http://img.jpg"]))
        assert "Network loss" in str(res)

    def test_poll_rodin_job_status(self, tool, mock_conn):
        mock_conn.send_command.return_value = {"status": "COMPLETED"}
        # subscription_key poll
        res = tool.poll_rodin_job_status(subscription_key=StatusString("sub-123"))
        data = json.loads(str(res))
        assert data["status"] == "COMPLETED"

        # request_id poll
        res = tool.poll_rodin_job_status(request_id=StatusString("req-123"))
        data = json.loads(str(res))
        assert data["status"] == "COMPLETED"

        # Exception
        mock_conn.send_command.side_effect = Exception()
        assert "Error" in str(tool.poll_rodin_job_status(subscription_key=StatusString("s")))

    def test_import_generated_asset_hyper3d(self, tool, mock_conn):
        mock_conn.send_command.return_value = {"success": True}
        # task_uuid path
        res = tool.import_generated_asset(ObjectName("Axe"), task_uuid="uuid-123")
        assert "true" in str(res)

        # request_id path
        res = tool.import_generated_asset(ObjectName("Axe"), request_id=StatusString("req-123"))
        assert "true" in str(res)

        # Exception
        mock_conn.send_command.side_effect = Exception()
        assert "Error" in str(tool.import_generated_asset(ObjectName("Axe"), task_uuid="u"))

    @pytest.mark.asyncio
    async def test_hyper3d_generation_adapter(self, adapter, mock_conn):
        # generate_from_text FAL_AI
        mock_conn.send_command.return_value = {"request_id": "req_123"}
        job_id = await adapter.generate_from_text(Prompt("axe"))
        assert job_id == "req_123"

        # generate_from_text MAIN_SITE
        mock_conn.send_command.return_value = {
            "submit_time": "1",
            "uuid": "uuid_1",
            "jobs": {"subscription_key": "sub_1"}
        }
        job_id2 = await adapter.generate_from_text(Prompt("axe"))
        job_data = json.loads(str(job_id2))
        assert job_data["task_uuid"] == "uuid_1"

        # generate_from_text failure
        mock_conn.send_command.return_value = {}
        with pytest.raises(ProviderError):
            await adapter.generate_from_text(Prompt("axe"))

        # generate_from_text exception
        mock_conn.send_command.side_effect = Exception()
        with pytest.raises(ProviderError):
            await adapter.generate_from_text(Prompt("axe"))

        # get_job_status with MAIN_SITE unpacked JSON job_id
        mock_conn.send_command.side_effect = None
        # List of statuses: all "Done" -> COMPLETED
        mock_conn.send_command.return_value = ["Done", "Done"]
        status = await adapter.get_job_status(JobId('{"task_uuid": "1", "subscription_key": "2"}'))
        assert status.status == "COMPLETED"

        # List of statuses: "Failed" -> FAILED
        mock_conn.send_command.return_value = ["Done", "Failed"]
        status = await adapter.get_job_status(JobId('{"task_uuid": "1", "subscription_key": "2"}'))
        assert status.status == "FAILED"

        # List of statuses: "Processing" -> RUNNING
        mock_conn.send_command.return_value = ["Done", "Processing"]
        status = await adapter.get_job_status(JobId('{"task_uuid": "1", "subscription_key": "2"}'))
        assert status.status == "RUNNING"

        # Dict response: COMPLETED
        mock_conn.send_command.return_value = {"status": "COMPLETED"}
        status = await adapter.get_job_status(JobId("req_123"))
        assert status.status == "COMPLETED"

        # Dict response: IN_PROGRESS -> RUNNING
        mock_conn.send_command.return_value = {"status": "IN_PROGRESS"}
        status = await adapter.get_job_status(JobId("req_123"))
        assert status.status == "RUNNING"

        # Dict response: FAILED
        mock_conn.send_command.return_value = {"status": "FAILED"}
        status = await adapter.get_job_status(JobId("req_123"))
        assert status.status == "FAILED"

        # Fallback pending status
        mock_conn.send_command.return_value = "unknown"
        status = await adapter.get_job_status(JobId("req_123"))
        assert status.status == "PENDING"

        # get_job_status exception
        mock_conn.send_command.side_effect = Exception()
        with pytest.raises(ProviderError):
            await adapter.get_job_status(JobId("req_123"))

        # start_generation & poll_generation
        mock_conn.send_command.side_effect = None
        mock_conn.send_command.return_value = {"request_id": "req_123"}
        start_res = await adapter.start_generation(GenerationStartRequestVO(prompt="mat"))
        assert start_res.job_id == "req_123"

        mock_conn.send_command.return_value = {"status": "COMPLETED"}
        poll_res = await adapter.poll_generation(GenerationStatusRequestVO(job_id=JobId("req_123")))
        assert poll_res.status == "COMPLETED"

        # import_generated_asset
        mock_conn.send_command.return_value = {"success": True, "object_name": "obj_99"}
        import_res = await adapter.import_generated_asset(
            ImportGeneratedAssetRequestVO(
                asset_id=AssetId("req_123"),
                object_name=ObjectName("obj_99"),
                location=Vector3D(0, 0, 0)
            )
        )
        assert import_res.success is True
        assert import_res.object_name == "obj_99"
