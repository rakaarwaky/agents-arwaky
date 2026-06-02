"""Handler: Blender object manipulation operations."""

import logging

from contract import (
    BlenderPort,
    ObjectOperateProtocol,
)
from taxonomy import (
    ApplyModifierRequestVO,
    ApplyModifierResponseVO,
    BlenderMCPError,
    CoordinateList,
    CreatePrimitiveRequestVO,
    CreatePrimitiveResponseVO,
    DeleteObjectRequestVO,
    DeleteObjectResponseVO,
    ErrorMessage,
    GetObjectInfoRequestVO,
    GetObjectInfoResponseVO,
    ObjectName,
    PlaceAssetRequestVO,
    PlaceAssetResponseVO,
    PythonCode,
    SetMaterialRequestVO,
    SetMaterialResponseVO,
    SetObjectTransformRequestVO,
    SetObjectTransformResponseVO,
    SuccessFlag,
)

logger = logging.getLogger("BlenderMCPServer")


class ObjectOperateExecutor(ObjectOperateProtocol):
    """Business logic for object manipulation (transform, material, etc.)."""

    def __init__(self, blender_port: BlenderPort):
        self.blender = blender_port

    async def place_asset(self, request: PlaceAssetRequestVO) -> PlaceAssetResponseVO:
        logger.info(f"Placing asset {request.asset_id} at {request.location}")
        if request.object_name:
            code = (
                "import bpy\n"
                f"obj = bpy.data.objects.get('{request.object_name}')\n"
                "if obj:\n"
                f"    obj.location = ({request.location[0]}, {request.location[1]}, {request.location[2]})\n"
            )
        else:
            code = (
                "import bpy\n"
                "for obj in bpy.context.selected_objects:\n"
                f"    obj.location = ({request.location[0]}, {request.location[1]}, {request.location[2]})\n"
            )
        try:
            await self.blender.execute_code(PythonCode(code))
            return PlaceAssetResponseVO(
                success=SuccessFlag(True),
                object_name=request.object_name or ObjectName(str(request.asset_id)),
                asset_id=request.asset_id,
                location=CoordinateList(request.location),
                message="Asset placed successfully",
            )
        except Exception as e:
            logger.error(f"Failed to place asset: {e}")
            raise BlenderMCPError(ErrorMessage(f"Failed to place asset: {e}")) from e

    async def get_object_info(self, request: GetObjectInfoRequestVO) -> GetObjectInfoResponseVO:
        try:
            obj = await self.blender.get_object_info(request.object_name)
            return GetObjectInfoResponseVO(
                success=SuccessFlag(True), object_info=obj, message="Object info retrieved successfully"
            )
        except Exception as e:
            logger.error(f"get_object_info failed: {e}")
            raise BlenderMCPError(ErrorMessage(f"Failed to get object info: {e}")) from e

    async def set_object_transform(self, request: SetObjectTransformRequestVO) -> SetObjectTransformResponseVO:
        logger.info(f"Setting transform for object {request.object_name}")
        lines = ["import bpy", f"obj = bpy.data.objects.get('{request.object_name}')", "if obj:"]
        if request.location is not None:
            lines.append(f"    obj.location = ({request.location[0]}, {request.location[1]}, {request.location[2]})")
        if request.rotation is not None:
            lines.append(
                f"    obj.rotation_euler = ({request.rotation[0]}, {request.rotation[1]}, {request.rotation[2]})"
            )
        if request.scale is not None:
            lines.append(f"    obj.scale = ({request.scale[0]}, {request.scale[1]}, {request.scale[2]})")
        code = "\n".join(lines)
        try:
            await self.blender.execute_code(PythonCode(code))
            return SetObjectTransformResponseVO(
                success=SuccessFlag(True), object_name=request.object_name, message="Transform set successfully"
            )
        except Exception as e:
            logger.error(f"set_object_transform failed: {e}")
            raise BlenderMCPError(ErrorMessage(f"Failed to set transform: {e}")) from e

    async def delete_object(self, request: DeleteObjectRequestVO) -> DeleteObjectResponseVO:
        logger.info(f"Deleting object {request.object_name}")
        code = (
            "import bpy\n"
            f"obj = bpy.data.objects.get('{request.object_name}')\n"
            "if obj:\n"
            "    bpy.data.objects.remove(obj, do_unlink=True)\n"
        )
        try:
            await self.blender.execute_code(PythonCode(code))
            return DeleteObjectResponseVO(
                success=SuccessFlag(True), object_name=request.object_name, message="Object deleted successfully"
            )
        except Exception as e:
            logger.error(f"delete_object failed: {e}")
            raise BlenderMCPError(ErrorMessage(f"Failed to delete object: {e}")) from e

    async def create_primitive(self, request: CreatePrimitiveRequestVO) -> CreatePrimitiveResponseVO:
        logger.info(f"Creating primitive: {request.primitive_type}")
        ptype = str(request.primitive_type).lower()

        ops_map = {
            "cube": "bpy.ops.mesh.primitive_cube_add",
            "sphere": "bpy.ops.mesh.primitive_uv_sphere_add",
            "cylinder": "bpy.ops.mesh.primitive_cylinder_add",
            "cone": "bpy.ops.mesh.primitive_cone_add",
            "torus": "bpy.ops.mesh.primitive_torus_add",
            "grid": "bpy.ops.mesh.primitive_grid_add",
            "monkey": "bpy.ops.mesh.primitive_monkey_add",
            "plane": "bpy.ops.mesh.primitive_plane_add",
        }
        op = ops_map.get(ptype, "bpy.ops.mesh.primitive_cube_add")

        kwargs = []
        if request.location is not None:
            kwargs.append(f"location=({request.location[0]}, {request.location[1]}, {request.location[2]})")
        if request.scale is not None:
            kwargs.append(f"scale=({request.scale[0]}, {request.scale[1]}, {request.scale[2]})")

        args_str = ", ".join(kwargs)

        code = f"import bpy\n{op}({args_str})\n"
        if request.name:
            code += (
                f"created_obj = bpy.context.active_object\nif created_obj:\n    created_obj.name = '{request.name}'\n"
            )

        try:
            await self.blender.execute_code(PythonCode(code))
            return CreatePrimitiveResponseVO(
                success=SuccessFlag(True),
                object_name=request.name or ObjectName("Primitive"),
                primitive_type=request.primitive_type,
                message="Primitive created successfully",
            )
        except Exception as e:
            logger.error(f"create_primitive failed: {e}")
            raise BlenderMCPError(ErrorMessage(f"Failed to create primitive: {e}")) from e

    async def set_material(self, request: SetMaterialRequestVO) -> SetMaterialResponseVO:
        logger.info(f"Setting material {request.material_name} on object {request.object_name}")
        code = (
            "import bpy\n"
            f"obj = bpy.data.objects.get('{request.object_name}')\n"
            f"mat = bpy.data.materials.get('{request.material_name}')\n"
            f"if not mat:\n"
            f"    mat = bpy.data.materials.new(name='{request.material_name}')\n"
            f"if obj:\n"
            f"    if len(obj.data.materials) == 0:\n"
            f"        obj.data.materials.append(mat)\n"
            f"    else:\n"
            f"        obj.data.materials[0] = mat\n"
        )
        try:
            await self.blender.execute_code(PythonCode(code))
            return SetMaterialResponseVO(
                success=SuccessFlag(True),
                object_name=request.object_name,
                material_name=request.material_name,
                message="Material set successfully",
            )
        except Exception as e:
            logger.error(f"set_material failed: {e}")
            raise BlenderMCPError(ErrorMessage(f"Failed to set material: {e}")) from e

    async def apply_modifier(self, request: ApplyModifierRequestVO) -> ApplyModifierResponseVO:
        logger.info(f"Applying modifier {request.modifier_name} on object {request.object_name}")
        code = (
            "import bpy\n"
            f"obj = bpy.data.objects.get('{request.object_name}')\n"
            f"if obj:\n"
            f"    mod_type = '{request.modifier_name}'.upper()\n"
            f"    mod = obj.modifiers.new(name='{request.modifier_name}', type=mod_type)\n"
            f"    bpy.context.view_layer.objects.active = obj\n"
            f"    bpy.ops.object.modifier_apply(modifier=mod.name)\n"
        )
        try:
            await self.blender.execute_code(PythonCode(code))
            return ApplyModifierResponseVO(
                success=SuccessFlag(True),
                object_name=request.object_name,
                modifier_name=request.modifier_name,
                message="Modifier applied successfully",
            )
        except Exception as e:
            logger.error(f"apply_modifier failed: {e}")
            raise BlenderMCPError(ErrorMessage(f"Failed to apply modifier: {e}")) from e
