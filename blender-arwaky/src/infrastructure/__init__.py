"""Infrastructure Layer: Technical adapters and service implementations.

All infrastructure components must follow the Dependency Injection (DI) pattern
and receive their dependencies (e.g., BlenderConnectionPort) via constructor.
"""

from .blender_connection_connector import BlenderConnection, BlenderConnectionFactory
from .blender_socket_adapter import BlenderSocketAdapter
from .code_execution_adapter import CodeExecutionAdapter
from .hunyuan_generation_adapter import HunyuanGenerationAdapter
from .hyper3d_generation_adapter import Hyper3DGenerationAdapter
from .polyhaven_asset_adapter import PolyhavenAssetAdapter
from .scene_inspection_adapter import SceneInspectionAdapter
from .sketchfab_asset_adapter import SketchfabAssetAdapter
from .telemetry_signal_recorder import TelemetrySignalRecorder
from .viewport_capture_adapter import ViewportCaptureAdapter

__all__ = [
    "BlenderConnection",
    "BlenderConnectionFactory",
    "BlenderSocketAdapter",
    "PolyhavenAssetAdapter",
    "SketchfabAssetAdapter",
    "Hyper3DGenerationAdapter",
    "HunyuanGenerationAdapter",
    "TelemetrySignalRecorder",
    "ViewportCaptureAdapter",
    "SceneInspectionAdapter",
    "CodeExecutionAdapter",
]
