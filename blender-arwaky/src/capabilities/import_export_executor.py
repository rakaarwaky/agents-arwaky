"""Handler: Import/Export file exchange operations."""

import logging

from contract import (
    BlenderPort,
    ImportExportProtocol,
)
from taxonomy import (
    BlenderMCPError,
    ErrorMessage,
    ExportModelRequestVO,
    ExportModelResponseVO,
    ImportGlbRequestVO,
    ImportGlbResponseVO,
    ObjectName,
    PythonCode,
    SuccessFlag,
)

logger = logging.getLogger("BlenderMCPServer")


class ImportExportExecutor(ImportExportProtocol):
    """Business logic for file exchange operations."""

    def __init__(self, blender_port: BlenderPort):
        self.blender = blender_port

    async def import_glb(self, request: ImportGlbRequestVO) -> ImportGlbResponseVO:
        logger.info(f"Importing GLB from {request.file_path}")
        code = f"import bpy\nbpy.ops.import_scene.gltf(filepath='{request.file_path}')\n"
        if request.object_name:
            code += (
                "imported_obj = bpy.context.active_object\n"
                f"if imported_obj:\n"
                f"    imported_obj.name = '{request.object_name}'\n"
            )
        try:
            await self.blender.execute_code(PythonCode(code))
            return ImportGlbResponseVO(
                success=SuccessFlag(True),
                object_name=request.object_name or ObjectName("ImportedModel"),
                file_path=request.file_path,
                message="Import successful",
            )
        except Exception as e:
            logger.error(f"Import failed: {e}")
            raise BlenderMCPError(ErrorMessage(f"Import failed: {e}")) from e

    async def export_model(self, request: ExportModelRequestVO) -> ExportModelResponseVO:
        logger.info(f"Exporting model {request.object_name} to {request.file_path}")
        code = (
            "import bpy\n"
            f"obj = bpy.data.objects.get('{request.object_name}')\n"
            f"if obj:\n"
            "    bpy.ops.object.select_all(action='DESELECT')\n"
            "    obj.select_set(True)\n"
            "    bpy.context.view_layer.objects.active = obj\n"
            f"    bpy.ops.export_scene.gltf(filepath='{request.file_path}', use_selection=True)\n"
        )
        try:
            await self.blender.execute_code(PythonCode(code))
            return ExportModelResponseVO(
                success=SuccessFlag(True),
                file_path=request.file_path,
                object_name=request.object_name,
                message="Export successful",
            )
        except Exception as e:
            logger.error(f"Export failed: {e}")
            raise BlenderMCPError(ErrorMessage(f"Export failed: {e}")) from e
