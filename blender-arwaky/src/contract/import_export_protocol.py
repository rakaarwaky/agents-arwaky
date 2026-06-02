"""
Contract: Import/Export Contract (ABC based).
"""

from abc import ABC, abstractmethod

from taxonomy import (
    ExportModelRequestVO,
    ExportModelResponseVO,
    ImportGlbRequestVO,
    ImportGlbResponseVO,
)


class ImportExportProtocol(ABC):
    """Interface for external file operations (GLB/OBJ)."""

    @abstractmethod
    async def import_glb(self, request: ImportGlbRequestVO) -> ImportGlbResponseVO:
        """Import a 3D model into Blender."""
        pass

    @abstractmethod
    async def export_model(self, request: ExportModelRequestVO) -> ExportModelResponseVO:
        """Export Blender objects to file."""
        pass
