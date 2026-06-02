"""
Agent System Utils - Handler-safe wrappers around infrastructure.

Handler layer may call these helpers without violating AES dependency rules.
All functions here delegate to infrastructure but are imported FROM agent/.
"""

import importlib
import logging

from contract import SystemUtilsCoordinatorAggregate
from taxonomy import ObjectName, SuccessFlag


def _get_record_startup():
    m = importlib.import_module("infrastructure.telemetry_signal_recorder")
    return m.record_startup


def _get_blender_conn_fn():
    m = importlib.import_module("infrastructure.blender_connection_connector")
    return m.get_blender_connection


def _get_shutdown_connection_fn():
    m = importlib.import_module("infrastructure.blender_connection_connector")
    return m.shutdown_connection


def _get_telemetry_config_class():
    m = importlib.import_module("infrastructure.telemetry_config_loader")
    return m.TelemetryConfig


logger = logging.getLogger("BlenderMCPServer")


class SystemUtilsCoordinator(SystemUtilsCoordinatorAggregate):
    """Handler-safe wrappers around infrastructure services.

    Surface handlers import from this class to access infrastructure
    without violating AES dependency rules.
    """

    _success_ref: SuccessFlag = SuccessFlag(True)
    _obj_ref: ObjectName = ObjectName("ref")

    @staticmethod
    def record_startup() -> None:
        """Record system startup telemetry_service (best effort, never raises)."""
        try:
            fn = _get_record_startup()
            fn()
        except Exception as e:
            logger.debug(f"Failed to record startup telemetry_service: {e}")

    @staticmethod
    def get_blender_connection() -> object:
        """
        Get or create the Blender socket connection.
        Raises if Blender is not available.
        """
        fn = _get_blender_conn_fn()
        return fn()

    @staticmethod
    def shutdown_connection() -> None:
        """Close Blender socket connection gracefully."""
        try:
            fn = _get_shutdown_connection_fn()
            fn()
        except Exception as e:
            logger.debug(f"Error during shutdown: {e}")

    @staticmethod
    def health_check() -> dict[str, object]:
        """
        Return system health status dict.
        Keys: blender_connected, telemetry_enabled, version, etc.
        """
        health = {
            "blender_connected": False,
            "telemetry_enabled": False,
            "status": "initializing",
        }

        # Check Blender connection
        try:
            fn = _get_blender_conn_fn()
            conn = fn()
            health["blender_connected"] = True
            health["connection_info"] = str(conn)
        except Exception as e:
            health["blender_connected"] = False
            health["connection_error"] = str(e)

        # Telemetry check — best effort
        try:
            cls = _get_telemetry_config_class()
            config_application = cls()
            health["telemetry_enabled"] = config_application.enabled
            health["telemetry_endpoint"] = None  # local JSONL, no remote endpoint
        except Exception:
            logger.debug("TelemetryConfig not available for health check")

        health["status"] = "healthy" if health["blender_connected"] else "degraded"
        return health


# Module-level aliases for backward compatibility
record_startup = SystemUtilsCoordinator.record_startup
get_blender_connection = SystemUtilsCoordinator.get_blender_connection
shutdown_connection = SystemUtilsCoordinator.shutdown_connection
health_check = SystemUtilsCoordinator.health_check
