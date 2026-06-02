import io
import json
import logging
import queue
import socket
import threading
import time
from contextlib import redirect_stdout

import bpy

from . import hunyuan, hyper3d, polyhaven, sketchfab, utils

logger = logging.getLogger(__name__)


class BlenderMCPServer:
    def __init__(self, host="localhost", port=9876):
        self.host = host
        self.port = port
        self.running = False
        self.socket = None
        self.server_thread = None
        self.command_queue = queue.Queue()
        self._timer_handle = None
        self._shutdown_lock = threading.Lock()
        self._shutdown_requested = False

    def start(self):
        if self.running:
            return
        self.running = True
        self._shutdown_requested = False
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.socket.bind((self.host, self.port))
            self.socket.listen(5)
            self.socket.settimeout(1.0)

            self.server_thread = threading.Thread(target=self._server_loop)
            self.server_thread.daemon = True
            self.server_thread.start()

            # Timer for processing commands in main thread (GUI mode)
            if not bpy.app.background:
                self._timer_handle = bpy.app.timers.register(  # pragma: no cover
                    self.process_commands, first_interval=0.1, persistent=True
                )

            logger.info("BlenderMCP server started on %s:%s", self.host, self.port)
        except Exception as e:  # pragma: no cover
            logger.error("Failed to start server: %s", e)  # pragma: no cover
            self.stop()  # pragma: no cover

    def stop(self):
        with self._shutdown_lock:
            if self._shutdown_requested:
                return
            self._shutdown_requested = True
            self.running = False

        if self.socket:
            try:
                self.socket.close()
            except Exception as e:  # pragma: no cover
                logger.debug("Error closing socket: %s", e)  # pragma: no cover
            self.socket = None

        if self._timer_handle:
            try:  # pragma: no cover
                bpy.app.timers.unregister(self.process_commands)  # pragma: no cover
            except Exception as e:  # pragma: no cover
                logger.debug("Error unregistering timer: %s", e)  # pragma: no cover
            self._timer_handle = None  # pragma: no cover

        # Clear queue to prevent new commands from being processed
        while not self.command_queue.empty():
            try:  # pragma: no cover
                self.command_queue.get_nowait()  # pragma: no cover
            except queue.Empty:  # pragma: no cover
                break  # pragma: no cover

        if self.server_thread:
            self.server_thread.join(timeout=1.0)
            self.server_thread = None
        logger.info("BlenderMCP server stopped")

    def _server_loop(self):
        while self.running:
            try:
                client, addr = self.socket.accept()
                t = threading.Thread(target=self._handle_client, args=(client,))  # pragma: no cover
                t.daemon = True  # pragma: no cover
                t.start()  # pragma: no cover
            except TimeoutError:  # pragma: no cover
                continue  # pragma: no cover
            except Exception as e:  # pragma: no cover
                if self.running:  # pragma: no cover
                    logger.error("Server accept error: %s", e)  # pragma: no cover
                time.sleep(0.1)  # pragma: no cover

    def _handle_client(self, client):
        client.settimeout(30.0)  # pragma: no cover
        buffer = b""  # pragma: no cover
        try:  # pragma: no cover
            while self.running:  # pragma: no cover
                try:  # pragma: no cover
                    data = client.recv(8192)  # pragma: no cover
                    if not data:  # pragma: no cover
                        break  # pragma: no cover
                    buffer += data  # pragma: no cover
                    # pragma: no cover
                    try:  # pragma: no cover
                        decoded = buffer.decode("utf-8")  # pragma: no cover
                        command = json.loads(decoded)  # pragma: no cover
                        buffer = b""  # pragma: no cover
                        # pragma: no cover
                        res_q = queue.Queue()  # pragma: no cover
                        self.command_queue.put((command, client, res_q))  # pragma: no cover
                        # Use timeout to prevent infinite blocking
                        try:  # pragma: no cover
                            res_q.get(timeout=180.0)  # Match RECEIVE_TIMEOUT  # pragma: no cover
                        except queue.Empty:  # pragma: no cover
                            logger.warning(
                                "Command %s timed out waiting for execution", command.get("type")
                            )  # pragma: no cover
                            client.sendall(
                                json.dumps(
                                    {  # pragma: no cover
                                        "status": "error",  # pragma: no cover
                                        "message": "Command execution timed out",  # pragma: no cover
                                    }
                                ).encode("utf-8")
                            )  # pragma: no cover
                    except json.JSONDecodeError:  # pragma: no cover
                        continue  # Wait for more data  # pragma: no cover
                except TimeoutError:  # pragma: no cover
                    continue  # pragma: no cover
                except (ConnectionError, BrokenPipeError, OSError) as e:  # pragma: no cover
                    logger.error("Client connection error: %s", e)  # pragma: no cover
                    break  # pragma: no cover
        finally:  # pragma: no cover
            try:
                client.close()
            except Exception as e:
                logger.debug("Error closing client socket: %s", e)

    def process_commands(self):
        if self._shutdown_requested:
            return 0.1

        while not self.command_queue.empty():
            try:
                cmd, client, res_q = self.command_queue.get_nowait()
                try:
                    # Skip if shutdown requested during processing
                    if self._shutdown_requested:
                        break  # pragma: no cover
                    response = self.execute_command(cmd)
                    client.sendall(json.dumps(response).encode("utf-8"))
                except Exception as e:  # pragma: no cover
                    logger.exception("Exec error: %s", e)
                    try:  # pragma: no cover
                        client.sendall(  # pragma: no cover
                            json.dumps({"status": "error", "message": str(e)}).encode(  # pragma: no cover
                                "utf-8"  # pragma: no cover
                            )  # pragma: no cover
                        )  # pragma: no cover
                    except Exception as send_err:
                        logger.debug("Error sending error response: %s", send_err)
                finally:
                    res_q.put(True)
            except queue.Empty:  # pragma: no cover
                break  # pragma: no cover
        return 0.1

    def execute_command(self, command):
        cmd_type = command.get("type")
        params = command.get("params", {})

        # Dispatch table
        handlers = {
            "get_scene_info": self.get_scene_info,
            "get_object_info": self.get_object_info,
            "get_viewport_screenshot": utils.get_viewport_screenshot,
            "execute_code": self.execute_code,
            "get_polyhaven_categories": polyhaven.get_polyhaven_categories,
            "search_polyhaven_assets": polyhaven.search_polyhaven_assets,
            "download_polyhaven_asset": polyhaven.download_polyhaven_asset,
            "set_texture": polyhaven.set_texture,
            "cleanup_polyhaven": polyhaven.cleanup_polyhaven,
            "get_polyhaven_status": polyhaven.get_polyhaven_status,
            "get_polyhaven_asset_details": polyhaven.get_polyhaven_asset_details,
            "get_sketchfab_status": sketchfab.get_sketchfab_status,
            "get_hyper3d_status": hyper3d.get_hyper3d_status,
            "get_hunyuan3d_status": hunyuan.get_hunyuan3d_status,
            "get_telemetry_consent": self.get_telemetry_consent,
            "create_rodin_job": hyper3d.create_rodin_job,
            "poll_rodin_job_status": hyper3d.poll_rodin_job_status,
            "import_generated_asset": hyper3d.import_generated_asset,
            "search_sketchfab_models": sketchfab.search_sketchfab_models,
            "get_sketchfab_model_preview": sketchfab.get_sketchfab_model_preview,
            "download_sketchfab_model": sketchfab.download_sketchfab_model,
            "create_hunyuan_job": hunyuan.create_hunyuan_job,
            "poll_hunyuan_job_status": hunyuan.poll_hunyuan_job_status,
            "import_generated_asset_hunyuan": hunyuan.import_generated_asset_hunyuan,
        }

        handler = handlers.get(cmd_type)
        if not handler:
            return {"status": "error", "message": f"Unknown command: {cmd_type}"}

        try:
            # Handle methods vs functions
            if hasattr(handler, "__self__") and handler.__self__ == self:
                result = handler(**params)
            else:
                # Most are externalized functions now
                result = handler(**params)
            return {"status": "success", "result": result}
        except Exception as e:
            logger.exception("Command execution failed: %s", command.get("type"))
            return {"status": "error", "message": str(e)}

    def get_scene_info(self):
        scene = bpy.context.scene
        return {
            "name": scene.name,
            "objects": [{"name": o.name, "type": o.type} for o in scene.objects[:50]],
        }

    def get_object_info(self, name):
        obj = bpy.data.objects.get(name)
        if not obj:
            return {"error": "Not found"}
        return {
            "name": obj.name,
            "type": obj.type,
            "location": list(obj.location),
            "rotation": list(obj.rotation_euler),
            "scale": list(obj.scale),
        }

    def execute_code(self, code):
        out = io.StringIO()
        try:
            with redirect_stdout(out):
                exec(code, {"bpy": bpy, "mathutils": __import__("mathutils")})
            return {"executed": True, "result": out.getvalue()}
        except Exception as e:
            return {"executed": False, "error": str(e)}

    def get_telemetry_consent(self):
        # Get telemetry consent from addon preferences
        try:
            addon_prefs = bpy.context.preferences.addons[__package__].preferences
            return {  # pragma: no cover
                "consent": getattr(addon_prefs, "telemetry_consent", False),
                "message": "Telemetry consent status retrieved",
            }
        except Exception as e:
            return {"error": f"Failed to get telemetry consent: {str(e)}"}
