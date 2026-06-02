"""Unit tests for the infrastructure layer (Adapters, config loader, socket connector)."""
import os
import pytest
import socket
from unittest.mock import MagicMock, patch, mock_open
from pathlib import Path

from taxonomy import (
    PythonCode,
    ObjectName,
    MaxSize,
    ActionName,
    Prompt,
    ConnectionError,
    ExecutionError,
)
from infrastructure.config_file_loader import (
    ApplicationConfigLoader,
)
from infrastructure.code_execution_adapter import CodeExecutionAdapter
from infrastructure.blender_socket_adapter import BlenderSocketAdapter
from infrastructure.blender_connection_connector import (
    BlenderConnection,
    BlenderConnectionFactory,
    get_blender_connection,
    shutdown_connection,
)
from infrastructure.command_catalog_client import CommandCatalogClient


class TestApplicationConfigLoader:
    """Tests for ApplicationConfigLoader and config caching."""

    @pytest.fixture(autouse=True)
    def reset_loader(self):
        ApplicationConfigLoader._config = None
        yield
        ApplicationConfigLoader._config = None

    def test_get_project_root_env_cfg(self):
        with patch.dict(os.environ, {"BLENDERMCP_CONFIG_PATH": "/mock/dir/config.yaml"}):
            with patch.object(Path, "is_file", return_value=True):
                # resolved to parent
                res = ApplicationConfigLoader.get_project_root()
                assert res == Path("/mock/dir")

    def test_get_project_root_env_root(self):
        with patch.dict(os.environ, {"BLENDER_MCP_ROOT": "/mock/root"}):
            res = ApplicationConfigLoader.get_project_root()
            assert res == Path("/mock/root")

    def test_get_project_root_relative_dev(self):
        with patch.object(Path, "exists", return_value=True):
            res = ApplicationConfigLoader.get_project_root()
            # Loop will find config.yaml
            assert res is not None

    def test_get_project_root_xdg(self):
        with patch.dict(os.environ, {"XDG_CONFIG_HOME": "/mock/xdg"}):
            def exists_mock(self_path):
                return "/mock/xdg" in str(self_path)
            with patch.object(Path, "exists", exists_mock):
                res = ApplicationConfigLoader.get_project_root()
                assert res == Path("/mock/xdg/blender-mcp")

    def test_get_project_root_fallback_cwd(self):
        # We simulate all exists checks returning False
        with patch.dict(os.environ, {}, clear=True):
            with patch.object(Path, "exists", return_value=False):
                res = ApplicationConfigLoader.get_project_root()
                assert res == Path.cwd().resolve()

    def test_load_config_file_not_found(self):
        with patch.object(Path, "exists", return_value=False):
            assert ApplicationConfigLoader.load_config() == {}

    def test_load_config_file_error(self):
        with patch.object(Path, "exists", return_value=True):
            with patch("builtins.open", side_effect=Exception("Read error")):
                assert ApplicationConfigLoader.load_config() == {}

    def test_load_config_success(self):
        mock_yaml = "server:\n  port: 1234\n"
        with patch.object(Path, "exists", return_value=True):
            with patch("builtins.open", mock_open(read_data=mock_yaml)):
                config = ApplicationConfigLoader.load_config()
                assert config == {"server": {"port": 1234}}

    def test_get_config_all(self):
        ApplicationConfigLoader._config = {"a": "b"}
        assert ApplicationConfigLoader.get_config("") == {"a": "b"}

    def test_get_config_port_style(self):
        loader = ApplicationConfigLoader()
        ApplicationConfigLoader._config = {"x": {"y": "z"}}
        assert loader.get("x.y") == "z"
        assert loader.get("x.nonexistent", "default") == "default"


class TestCodeExecutionAdapter:
    """Tests for CodeExecutionAdapter."""

    @pytest.mark.asyncio
    async def test_execute_code_success(self):
        mock_conn = MagicMock()
        mock_conn.send_command.return_value = {"result": "output_val"}
        adapter = CodeExecutionAdapter(mock_conn)

        res = await adapter.execute_blender_code(Prompt("print('hello')"))
        assert "output_val" in str(res)
        mock_conn.send_command.assert_called_once_with(ActionName("execute_code"), {"code": "print('hello')"})

    @pytest.mark.asyncio
    async def test_execute_code_exception(self):
        mock_conn = MagicMock()
        mock_conn.send_command.side_effect = Exception("Connection lost")
        adapter = CodeExecutionAdapter(mock_conn)

        res = await adapter.execute_blender_code(Prompt("print('hello')"))
        assert "Connection lost" in str(res)

    @pytest.mark.asyncio
    async def test_execute_code_blocked_os_system(self):
        mock_conn = MagicMock()
        adapter = CodeExecutionAdapter(mock_conn)
        res = await adapter.execute_blender_code(Prompt("os.system('rm -rf /')"))
        assert "Validation error" in str(res)
        assert "blocked" in str(res).lower()
        mock_conn.send_command.assert_not_called()

    @pytest.mark.asyncio
    async def test_execute_code_blocked_subprocess(self):
        mock_conn = MagicMock()
        adapter = CodeExecutionAdapter(mock_conn)
        res = await adapter.execute_blender_code(Prompt("import subprocess; subprocess.run(['ls'])"))
        assert "Validation error" in str(res)
        mock_conn.send_command.assert_not_called()

    @pytest.mark.asyncio
    async def test_execute_code_blocked_dunder_import(self):
        mock_conn = MagicMock()
        adapter = CodeExecutionAdapter(mock_conn)
        res = await adapter.execute_blender_code(Prompt("__import__('os').system('whoami')"))
        assert "Validation error" in str(res)
        mock_conn.send_command.assert_not_called()

    @pytest.mark.asyncio
    async def test_execute_code_blocked_shutil(self):
        mock_conn = MagicMock()
        adapter = CodeExecutionAdapter(mock_conn)
        res = await adapter.execute_blender_code(Prompt("shutil.rmtree('/home')"))
        assert "Validation error" in str(res)
        mock_conn.send_command.assert_not_called()

    @pytest.mark.asyncio
    async def test_execute_code_empty(self):
        mock_conn = MagicMock()
        adapter = CodeExecutionAdapter(mock_conn)
        res = await adapter.execute_blender_code(Prompt(""))
        assert "Validation error" in str(res)
        mock_conn.send_command.assert_not_called()

    @pytest.mark.asyncio
    async def test_execute_code_too_long(self):
        mock_conn = MagicMock()
        adapter = CodeExecutionAdapter(mock_conn)
        long_code = "x = 1\n" * 5000  # Well over 10K chars
        res = await adapter.execute_blender_code(Prompt(long_code))
        assert "Validation error" in str(res)
        mock_conn.send_command.assert_not_called()

    @pytest.mark.asyncio
    async def test_execute_code_valid_bpy(self):
        """Valid bpy code should pass validation and reach send_command."""
        mock_conn = MagicMock()
        mock_conn.send_command.return_value = {"result": "ok"}
        adapter = CodeExecutionAdapter(mock_conn)
        res = await adapter.execute_blender_code(Prompt("import bpy; bpy.ops.mesh.primitive_cube_add()"))
        assert "successfully" in str(res).lower()
        mock_conn.send_command.assert_called_once()


class TestBlenderSocketAdapter:
    """Tests for BlenderSocketAdapter operations."""

    @pytest.fixture
    def mock_conn(self):
        return MagicMock()

    @pytest.fixture
    def adapter(self, mock_conn):
        return BlenderSocketAdapter(mock_conn)

    @pytest.mark.asyncio
    async def test_execute_code_success(self, adapter, mock_conn):
        mock_conn.send_command.return_value = {"result": "success_msg"}
        res = await adapter.execute_code(PythonCode("import bpy"))
        assert res == "success_msg"

    @pytest.mark.asyncio
    async def test_execute_code_connection_error(self, adapter, mock_conn):
        mock_conn.send_command.side_effect = ConnectionError("Conn error")
        with pytest.raises(ConnectionError):
            await adapter.execute_code(PythonCode("import bpy"))

    @pytest.mark.asyncio
    async def test_execute_code_general_error(self, adapter, mock_conn):
        mock_conn.send_command.side_effect = Exception("Syntax error")
        with pytest.raises(ExecutionError):
            await adapter.execute_code(PythonCode("import bpy"))

    @pytest.mark.asyncio
    async def test_get_scene_info_success(self, adapter, mock_conn):
        mock_conn.send_command.return_value = {
            "objects": [],
            "active_object_id": None,
            "render_engine": "CYCLES",
        }
        info = await adapter.get_scene_info()
        assert info.render_engine == "CYCLES"

    @pytest.mark.asyncio
    async def test_get_scene_info_errors(self, adapter, mock_conn):
        mock_conn.send_command.side_effect = ConnectionError()
        with pytest.raises(ConnectionError):
            await adapter.get_scene_info()

        mock_conn.send_command.side_effect = Exception()
        with pytest.raises(ExecutionError):
            await adapter.get_scene_info()

    @pytest.mark.asyncio
    async def test_get_object_info(self, adapter, mock_conn):
        # Object not found
        mock_conn.send_command.return_value = None
        obj = await adapter.get_object_info(ObjectName("Nonexistent"))
        assert obj is None

        # Object found
        from taxonomy.blender_spatial_vo import Vector3D
        mock_conn.send_command.return_value = {
            "name": "Cube",
            "type": "MESH",
            "location": Vector3D(0.0, 0.0, 0.0),
            "rotation": Vector3D(0.0, 0.0, 0.0),
            "scale": Vector3D(1.0, 1.0, 1.0),
        }
        obj = await adapter.get_object_info(ObjectName("Cube"))
        assert obj is not None
        assert obj.name == "Cube"

        # General error raises None
        mock_conn.send_command.side_effect = Exception()
        assert await adapter.get_object_info(ObjectName("Cube")) is None

        mock_conn.send_command.side_effect = ConnectionError()
        with pytest.raises(ConnectionError):
            await adapter.get_object_info(ObjectName("Cube"))

    @pytest.mark.asyncio
    async def test_get_screenshot_success(self, adapter, mock_conn):
        # We mock tempfile and socket responses
        mock_conn.send_command.return_value = {}
        with patch("os.path.exists", return_value=True):
            with patch("builtins.open", mock_open(read_data=b"image_bytes_here")):
                with patch("os.remove") as mock_remove:
                    img = await adapter.get_screenshot(MaxSize(800))
                    assert img == b"image_bytes_here"
                    mock_remove.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_screenshot_blender_error(self, adapter, mock_conn):
        mock_conn.send_command.return_value = {"error": "Blender failed to capture"}
        with pytest.raises(ExecutionError):
            await adapter.get_screenshot()

    @pytest.mark.asyncio
    async def test_get_screenshot_file_not_created(self, adapter, mock_conn):
        mock_conn.send_command.return_value = {}
        with patch("os.path.exists", return_value=False):
            with pytest.raises(ExecutionError):
                await adapter.get_screenshot()

    @pytest.mark.asyncio
    async def test_get_screenshot_exceptions(self, adapter, mock_conn):
        mock_conn.send_command.side_effect = ConnectionError()
        with pytest.raises(ConnectionError):
            await adapter.get_screenshot()

        mock_conn.send_command.side_effect = Exception()
        with pytest.raises(ExecutionError):
            await adapter.get_screenshot()

    def test_uninitialized_connection(self):
        adapter = BlenderSocketAdapter(None)  # type: ignore
        with pytest.raises(ConnectionError):
            adapter._get_conn()


class TestBlenderConnectionAndFactory:
    """Tests for BlenderConnection socket client, lifecycle, and Factory singleton."""

    @pytest.fixture(autouse=True)
    def clean_singleton(self):
        import infrastructure.blender_connection_connector as bcc
        bcc._blender_connection = None
        bcc._default_factory = None
        yield
        bcc._blender_connection = None
        bcc._default_factory = None

    def test_connection_connect_success(self):
        conn = BlenderConnection()
        mock_sock = MagicMock()
        with patch("socket.socket", return_value=mock_sock):
            assert conn.connect() is True
            assert conn.sock is mock_sock

    def test_connection_connect_fails_all_retries(self):
        conn = BlenderConnection()
        with patch("socket.socket", side_effect=Exception("Connection refused")):
            with patch("time.sleep") as mock_sleep:
                assert conn.connect() is False
                assert conn.sock is None
                assert mock_sleep.call_count == 2

    def test_disconnect(self):
        conn = BlenderConnection()
        mock_sock = MagicMock()
        conn.sock = mock_sock
        conn.disconnect()
        mock_sock.close.assert_called_once()
        assert conn.sock is None

    def test_is_socket_alive(self):
        conn = BlenderConnection()
        assert conn._is_socket_alive() is False

        # Live socket
        mock_sock = MagicMock()
        conn.sock = mock_sock
        with patch("select.select", return_value=([], [], [])):
            assert conn._is_socket_alive() is True

        # Peek reads closed connection
        with patch("select.select", return_value=([mock_sock], [], [])):
            mock_sock.recv.return_value = b""
            assert conn._is_socket_alive() is False

        # Socket throws exception during peek
        with patch("select.select", side_effect=OSError()):
            assert conn._is_socket_alive() is False

    def test_read_response_chunks_success(self):
        conn = BlenderConnection()
        mock_sock = MagicMock()
        # Returns raw JSON chunk then empty or timeout
        mock_sock.recv.side_effect = [b'{"status": "ok", ', b'"result": {"msg": "done"}}']

        chunks, completed = conn._read_response_chunks(mock_sock, 1024)
        assert completed is True
        assert b"".join(chunks) == b'{"status": "ok", "result": {"msg": "done"}}'

    def test_read_response_chunks_timeout(self):
        conn = BlenderConnection()
        mock_sock = MagicMock()
        mock_sock.recv.side_effect = socket.timeout("timeout")

        chunks, completed = conn._read_response_chunks(mock_sock, 1024)
        assert completed is False
        assert len(chunks) == 0

    def test_read_response_chunks_empty_disconnect(self):
        conn = BlenderConnection()
        mock_sock = MagicMock()
        mock_sock.recv.return_value = b""

        with pytest.raises(Exception) as exc:
            conn._read_response_chunks(mock_sock, 1024)
        assert "closed" in str(exc.value)

    def test_finalize_chunks(self):
        conn = BlenderConnection()
        res = conn._finalize_chunks([b'{"a": ', b'1}'])
        assert res == b'{"a": 1}'

        with pytest.raises(Exception) as exc:
            conn._finalize_chunks([b'{"a": 1'])
        assert "JSON" in str(exc.value)

    def test_receive_full_response_no_data(self):
        conn = BlenderConnection()
        mock_sock = MagicMock()
        mock_sock.recv.return_value = b""
        with pytest.raises(Exception):
            conn.receive_full_response(mock_sock)

    def test_send_command_success(self):
        conn = BlenderConnection()
        mock_sock = MagicMock()
        conn.sock = mock_sock

        mock_response = b'{"status": "success", "result": {"status": "ok"}}'
        with patch.object(conn, "receive_full_response", return_value=mock_response):
            res = conn.send_command(ActionName("test_cmd"))
            assert res == {"status": "ok"}
            mock_sock.sendall.assert_called_once()

    def test_send_command_error_status(self):
        conn = BlenderConnection()
        mock_sock = MagicMock()
        conn.sock = mock_sock

        mock_response = b'{"status": "error", "message": "Blender crashed"}'
        with patch.object(conn, "receive_full_response", return_value=mock_response):
            with pytest.raises(Exception) as exc:
                conn.send_command(ActionName("test_cmd"))
            assert "Blender crashed" in str(exc.value)

    def test_send_command_exceptions(self):
        conn = BlenderConnection()
        mock_sock = MagicMock()
        conn.sock = mock_sock

        # Timeout exception
        mock_sock.sendall.side_effect = socket.timeout()
        with pytest.raises(Exception) as exc:
            conn.send_command(ActionName("test_cmd"))
        assert "Timeout" in str(exc.value)

        # Connection error
        conn.sock = mock_sock
        import builtins
        mock_sock.sendall.side_effect = builtins.ConnectionError("broken pipe")
        with pytest.raises(Exception) as exc:
            conn.send_command(ActionName("test_cmd"))
        assert "lost" in str(exc.value)

        # Invalid JSON
        conn.sock = mock_sock
        mock_sock.sendall.side_effect = None
        with patch.object(conn, "receive_full_response", return_value=b"invalid json"):
            with pytest.raises(Exception) as exc:
                conn.send_command(ActionName("test_cmd"))
            assert "Invalid" in str(exc.value)

    def test_connection_factory(self):
        mock_config = MagicMock()
        mock_config.get.side_effect = lambda k, d: 9876 if "port" in str(k) else "localhost"

        factory = BlenderConnectionFactory(mock_config)

        with patch.object(BlenderConnection, "connect", return_value=True):
            conn = factory.get_connection()
            assert isinstance(conn, BlenderConnection)

            # Check singleton resolution when alive
            with patch.object(BlenderConnection, "_is_socket_alive", return_value=True):
                conn2 = factory.get_connection()
                assert conn is conn2

            # When dead, recreates
            with patch.object(BlenderConnection, "_is_socket_alive", return_value=False):
                with patch.object(BlenderConnection, "disconnect") as mock_dis:
                    conn3 = factory.get_connection()
                    assert conn3 is not conn
                    mock_dis.assert_called_once()

    def test_factory_connection_fails(self):
        factory = BlenderConnectionFactory()
        with patch.object(BlenderConnection, "connect", return_value=False):
            with pytest.raises(Exception) as exc:
                factory.get_connection()
            assert "Make sure" in str(exc.value)

    def test_factory_shutdown(self):
        factory = BlenderConnectionFactory()
        with patch.object(BlenderConnection, "connect", return_value=True):
            conn = factory.get_connection()
            with patch.object(conn, "disconnect") as mock_dis:
                factory.shutdown()
                mock_dis.assert_called_once()
                assert factory._connection is None

    def test_global_singleton_helpers(self):
        # test get_blender_connection and shutdown_connection
        with patch.object(BlenderConnection, "connect", return_value=True):
            conn = get_blender_connection()
            assert isinstance(conn, BlenderConnection)

            shutdown_connection()
            # factory should be cleared
            assert conn.sock is None


class TestCommandCatalogClient:
    """Tests for CommandCatalogClient."""

    def test_catalog_client_methods(self):
        client = CommandCatalogClient()
        # Verify list_actions
        cmds = client.list_actions()
        assert len(cmds) > 0

        # Verify filter_by_domain
        filtered = client.filter_by_domain("scene")
        assert len(filtered) > 0
        for spec in filtered.values():
            assert spec["domain"] == "scene"

        # Verify specific command retrieval
        cmd_spec = client.get_command_spec(ActionName("cleanup_scene"))
        assert cmd_spec is not None
        assert cmd_spec["domain"] == "scene"

        # Nonexistent command
        assert client.get_command_spec(ActionName("nonexistent_command_123")) is None


class TestSceneInspectionAdapter:
    """Tests for SceneInspectionAdapter."""

    @pytest.mark.asyncio
    async def test_get_scene_info(self):
        from infrastructure.scene_inspection_adapter import SceneInspectionAdapter
        mock_conn = MagicMock()
        mock_exec = MagicMock()
        adapter = SceneInspectionAdapter(mock_conn, mock_exec)

        # Success path
        mock_conn.send_command.return_value = {"objects": [{"name": "Cube"}]}
        res = await adapter.get_scene_info()
        assert "Cube" in str(res)
        mock_conn.send_command.assert_called_once_with(ActionName("get_scene_info"))

        # Exception path
        mock_conn.send_command.side_effect = Exception("Blender crash")
        res2 = await adapter.get_scene_info()
        assert "Blender crash" in str(res2)

    @pytest.mark.asyncio
    async def test_get_object_info(self):
        from infrastructure.scene_inspection_adapter import SceneInspectionAdapter
        mock_conn = MagicMock()
        mock_exec = MagicMock()
        adapter = SceneInspectionAdapter(mock_conn, mock_exec)

        # Success path
        mock_conn.send_command.return_value = {"name": "Cube", "type": "MESH"}
        res = await adapter.get_object_info(ObjectName("Cube"))
        assert "Cube" in str(res)
        mock_conn.send_command.assert_called_once_with(ActionName("get_object_info"), {"name": "Cube"})

        # Exception path
        mock_conn.send_command.side_effect = Exception("Blender offline")
        res2 = await adapter.get_object_info(ObjectName("Cube"))
        assert "Blender offline" in str(res2)

    @pytest.mark.asyncio
    async def test_cleanup_scene(self):
        from infrastructure.scene_inspection_adapter import SceneInspectionAdapter
        mock_conn = MagicMock()
        mock_exec = MagicMock()
        adapter = SceneInspectionAdapter(mock_conn, mock_exec)

        # Success path
        async def mock_execute(code):
            return Prompt("All objects deleted")
        mock_exec.execute_blender_code = mock_execute

        res = await adapter.cleanup_scene()
        assert "All objects deleted" in str(res)

        # Exception path
        async def mock_execute_fail(code):
            raise Exception("Execution error")
        mock_exec.execute_blender_code = mock_execute_fail

        res2 = await adapter.cleanup_scene()
        assert "Execution error" in str(res2)


class TestViewportCaptureAdapter:
    """Tests for ViewportCaptureAdapter."""

    def test_get_viewport_screenshot_success(self):
        from infrastructure.viewport_capture_adapter import ViewportCaptureAdapter
        mock_conn = MagicMock()
        adapter = ViewportCaptureAdapter(mock_conn)

        mock_conn.send_command.return_value = {"success": True}

        with patch("os.path.exists", return_value=True):
            with patch("builtins.open", mock_open(read_data=b"screenshot_bytes")):
                with patch("os.remove") as mock_remove:
                    res = adapter.get_viewport_screenshot(max_size=400)
                    assert res == b"screenshot_bytes"
                    mock_remove.assert_called_once()
                    mock_conn.send_command.assert_called_once()
                    args, kwargs = mock_conn.send_command.call_args
                    assert args[0] == ActionName("get_viewport_screenshot")
                    assert args[1]["max_size"] == 400

    def test_get_viewport_screenshot_failures(self):
        from infrastructure.viewport_capture_adapter import ViewportCaptureAdapter
        mock_conn = MagicMock()
        adapter = ViewportCaptureAdapter(mock_conn)

        # 1. No result returned from Blender
        mock_conn.send_command.return_value = None
        with pytest.raises(Exception) as exc:
            adapter.get_viewport_screenshot()
        assert "No result returned" in str(exc.value)

        # 2. File not created
        mock_conn.send_command.side_effect = None
        mock_conn.send_command.return_value = {"success": True}
        with patch("os.path.exists", return_value=False):
            with pytest.raises(Exception) as exc:
                adapter.get_viewport_screenshot()
            assert "was not created" in str(exc.value)

        # 3. Exception in send_command
        mock_conn.send_command.side_effect = Exception("Socket crash")
        with pytest.raises(Exception) as exc:
            adapter.get_viewport_screenshot()
        assert "Socket crash" in str(exc.value)
