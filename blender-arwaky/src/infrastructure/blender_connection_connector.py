"""Blender socket connection management"""

import contextlib
import json
import logging
import os
import select
import socket
import threading
import time
from typing import Any

from contract import BlenderConnectionFactoryPort, BlenderConnectionPort, ConfigPort
from taxonomy import (
    ActionName,
    BlenderConnectionError,
    ConfigPath,
    Details,
    ErrorMessage,
    ExecutionError,
    SuccessFlag,
)

logger = logging.getLogger("BlenderMCPServer")

MAX_RETRIES = 3
RETRY_DELAY = 1.0
RECEIVE_TIMEOUT = 180.0


class BlenderConnection(BlenderConnectionPort):
    """Manages persistent socket connection to Blender addon"""

    def __init__(self, host: str = "localhost", port: int = 9876):
        self.host = host
        self.port = port
        self.sock: socket.socket | None = None
        self._lock = threading.Lock()

    def connect(self) -> SuccessFlag:
        """Connect to Blender with retries. Thread-safe."""
        with self._lock:
            if self.sock is not None:
                if self._is_socket_alive():
                    return SuccessFlag(True)
                self._close_socket()  # pragma: no cover

            for attempt in range(MAX_RETRIES):
                try:
                    self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    self.sock.settimeout(10.0)
                    self.sock.connect((self.host, self.port))
                    logger.info(f"Connected to Blender at {self.host}:{self.port}")
                    return SuccessFlag(True)
                except Exception as e:
                    logger.warning(f"Connection attempt {attempt + 1}/{MAX_RETRIES} failed: {e}")
                    self._close_socket()
                    if attempt < MAX_RETRIES - 1:
                        time.sleep(RETRY_DELAY)

            logger.error("Failed to connect to Blender after all retries")
            return SuccessFlag(False)

    def _close_socket(self):
        if self.sock:
            with contextlib.suppress(Exception):
                self.sock.close()
            self.sock = None

    def disconnect(self):
        """Disconnect from Blender. Thread-safe."""
        with self._lock:
            self._close_socket()

    def _is_socket_alive(self) -> bool:
        if self.sock is None:
            return False
        try:
            ready, _, _ = select.select([self.sock], [], [], 0)
            if ready:
                data = self.sock.recv(1, socket.MSG_PEEK)
                if not data:
                    return False
            return True
        except (ConnectionError, BrokenPipeError, ConnectionResetError, OSError, BlenderConnectionError):
            return False

    def _read_response_chunks(self, sock: socket.socket, buffer_size: int) -> tuple:
        """Read socket chunks until a complete JSON is received or connection ends.

        Returns (chunks, completed_via_json) where completed_via_json is True
        if we successfully parsed JSON and have the complete response.
        """
        chunks: list[bytes] = []
        try:
            while True:
                try:
                    chunk = sock.recv(buffer_size)
                    if not chunk:
                        if not chunks:
                            raise BlenderConnectionError(ErrorMessage("Connection closed before receiving any data"))
                        break
                    chunks.append(chunk)
                    try:
                        data = b"".join(chunks)
                        json.loads(data.decode("utf-8"))
                        logger.info(f"Received complete response ({len(data)} bytes)")
                        return chunks, True
                    except json.JSONDecodeError:
                        continue
                except TimeoutError:
                    logger.warning("Socket timeout during chunked receive")
                    break
                except (ConnectionError, BrokenPipeError, ConnectionResetError) as e:
                    logger.error(f"Socket connection error: {e}")
                    raise
        except TimeoutError:
            logger.warning("Socket timeout during chunked receive")  # pragma: no cover
        except Exception as e:
            logger.error(f"Error during receive: {e}")
            raise
        return chunks, False

    def _finalize_chunks(self, chunks: list[bytes]) -> bytes:
        """Process collected chunks into a complete response."""
        data = b"".join(chunks)
        logger.info(f"Returning data after receive completion ({len(data)} bytes)")
        try:
            json.loads(data.decode("utf-8"))
            return data
        except json.JSONDecodeError as e:
            raise ExecutionError(ErrorMessage("Incomplete JSON response received")) from e

    def receive_full_response(self, sock: socket.socket, buffer_size: int = 8192) -> bytes:
        chunks, completed = self._read_response_chunks(sock, buffer_size)
        if completed:
            return b"".join(chunks)
        if chunks:
            return self._finalize_chunks(chunks)
        raise BlenderConnectionError(ErrorMessage("No data received"))

    def is_connected(self) -> SuccessFlag:
        return SuccessFlag(self._is_socket_alive())  # pragma: no cover

    def _handle_command_response(self, response_data: bytes) -> dict[str, Any]:
        """Parse and validate the JSON response from Blender."""
        response = json.loads(response_data.decode("utf-8"))
        logger.info(f"Response parsed, status: {response.get('status', 'unknown')}")

        if response.get("status") == "error":
            logger.error(f"Blender error: {response.get('message')}")
            raise ExecutionError(ErrorMessage(response.get("message", "Unknown error from Blender")))

        result: dict[str, Any] = response.get("result", {})
        return result

    def send_command(self, command_type: ActionName, params: Details | None = None) -> Details:
        with self._lock:
            if self.sock is None and not self.connect():
                raise ConnectionError("Not connected to Blender")

            active_sock = self.sock
            if active_sock is None:
                raise ConnectionError("Socket initialization failed")

            command = {"type": str(command_type), "params": params or {}}

            response_data: bytes = b""
            try:
                logger.info(f"Sending command: {command_type} with params: {params}")
                active_sock.settimeout(RECEIVE_TIMEOUT)
                active_sock.sendall(json.dumps(command).encode("utf-8"))
                logger.info("Command sent, waiting for response...")
                response_data = self.receive_full_response(active_sock)
                logger.info(f"Received {len(response_data)} bytes of data")

                return self._handle_command_response(response_data)
            except TimeoutError as e:
                logger.error("Socket timeout while waiting for response")
                self._close_socket()
                raise BlenderConnectionError(
                    ErrorMessage("Timeout waiting for Blender response - try simplifying your request")
                ) from e
            except (ConnectionError, BrokenPipeError, ConnectionResetError) as e:
                logger.error(f"Socket connection error: {e}")
                self._close_socket()
                raise BlenderConnectionError(ErrorMessage(f"Connection to Blender lost: {e}")) from e
            except json.JSONDecodeError as e:
                logger.error(f"Invalid JSON response from Blender: {e}")
                if response_data:
                    logger.error(
                        f"Raw response (first 200 bytes): {response_data[:200].decode('utf-8', errors='replace')}"
                    )
                raise ExecutionError(ErrorMessage(f"Invalid response from Blender: {e}")) from e
            except Exception as e:
                logger.error(f"Error communicating with Blender: {e}")
                self._close_socket()
                raise BlenderConnectionError(ErrorMessage(f"Communication error with Blender: {e}")) from e


# ─── BlenderConnectionFactory ─────────────────────────────────────────────────


class BlenderConnectionFactory(BlenderConnectionFactoryPort):
    """Factory that creates and manages a singleton BlenderConnection.

    Accepts ConfigPort for reading host/port from config.yaml.
    """

    def __init__(self, config: ConfigPort | None = None) -> None:
        self._config = config
        self._connection: BlenderConnection | None = None
        self._lock = threading.Lock()

    def get_connection(self) -> BlenderConnectionPort:
        host = "localhost"
        port = 9876
        if self._config is not None:
            host_val = self._config.get(ConfigPath("blender.host"), "localhost")
            host = str(host_val) if host_val is not None else "localhost"
            port_val = self._config.get(ConfigPath("blender.port"), 9876)
            port = int(port_val) if isinstance(port_val, (int, str)) else 9876

        host = os.getenv("BLENDER_HOST", host)
        port = int(os.getenv("BLENDER_PORT", port))

        with self._lock:
            if self._connection is not None:
                if self._connection._is_socket_alive():
                    return self._connection
                self._connection.disconnect()
                self._connection = None

            self._connection = BlenderConnection(host=host, port=port)
            if not self._connection.connect():
                self._connection = None
                raise BlenderConnectionError(
                    ErrorMessage("Could not connect to Blender. Make sure the Blender addon is running.")
                )
            return self._connection

    def shutdown(self):
        with self._lock:
            if self._connection is not None:
                self._connection.disconnect()
                self._connection = None


# ─── Backward-compat global singleton helpers ─────────────────────────────────

_blender_connection: BlenderConnection | None = None
_connection_lock = threading.Lock()
_default_factory: BlenderConnectionFactory | None = None


def get_blender_connection() -> BlenderConnection:
    """Get or create a persistent Blender connection singleton (backward compat)."""
    global _blender_connection, _default_factory

    with _connection_lock:
        if _blender_connection is not None:
            if _blender_connection._is_socket_alive():
                return _blender_connection
            _blender_connection.disconnect()
            _blender_connection = None

        if _default_factory is None:
            _default_factory = BlenderConnectionFactory()

        conn = _default_factory.get_connection()
        if isinstance(conn, BlenderConnection):
            _blender_connection = conn
        else:
            msg = "BlenderConnectionFactory returned unexpected type"
            raise TypeError(msg)
        return _blender_connection


def shutdown_connection():
    """Shutdown the persistent Blender connection."""
    global _blender_connection, _default_factory
    with _connection_lock:
        if _default_factory is not None:
            _default_factory.shutdown()
            _default_factory = None
        _blender_connection = None
