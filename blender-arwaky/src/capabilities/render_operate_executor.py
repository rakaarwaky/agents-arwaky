"""Handler: Render and viewport capture operations."""

import logging

from contract import (
    BlenderPort,
    RenderOperateProtocol,
)
from taxonomy import (
    BlenderMCPError,
    CoordinateList,
    ErrorMessage,
    GetScreenshotRequestVO,
    ImageFormat,
    Prompt,
    PythonCode,
    RenderEngine,
    RenderRequestVO,
    RenderResponseVO,
    RenderSamples,
    ResolutionX,
    ResolutionY,
    RotationVector,
    RuleName,
    ScreenshotResponseVO,
    SuccessFlag,
    UseDenoising,
)

logger = logging.getLogger("BlenderMCPServer")


class RenderOperateExecutor(RenderOperateProtocol):
    """Business logic for rendering and visualization."""

    def __init__(self, blender_port: BlenderPort):
        self.blender = blender_port

    async def get_viewport_screenshot(self, request: GetScreenshotRequestVO) -> ScreenshotResponseVO:
        logger.info(f"Capturing viewport screenshot with max size {request.max_size}")
        try:
            image_data = await self.blender.get_screenshot(max_size=request.max_size)
            return ScreenshotResponseVO(
                success=SuccessFlag(True),
                image_data=image_data,
                format=request.format or ImageFormat("png"),
                width=ResolutionX(800),
                height=ResolutionY(600),
            )
        except Exception as e:
            logger.error(f"Failed to capture screenshot: {e}")
            raise BlenderMCPError(ErrorMessage(f"Screenshot failed: {e}")) from e

    async def setup_camera(
        self, location: CoordinateList, rotation: RotationVector, target: CoordinateList | None = None
    ) -> Prompt:
        logger.info(f"Setting up camera at {location}")
        code = (
            "import bpy\n"
            "camera = bpy.data.objects.get('Camera')\n"
            "if not camera:\n"
            "    bpy.ops.object.camera_add()\n"
            "    camera = bpy.context.active_object\n"
            f"camera.location = ({location[0]}, {location[1]}, {location[2]})\n"
            f"camera.rotation_euler = ({rotation[0]}, {rotation[1]}, {rotation[2]})\n"
        )
        if target is not None:
            code += (
                "constraint = camera.constraints.get('Track To')\n"
                "if not constraint:\n"
                "    constraint = camera.constraints.new(type='TRACK_TO')\n"
                "target_obj = bpy.data.objects.get('Target')\n"
                "if not target_obj:\n"
                "    bpy.ops.object.empty_add(type='PLAIN_AXES')\n"
                "    target_obj = bpy.context.active_object\n"
                "    target_obj.name = 'Target'\n"
                f"target_obj.location = ({target[0]}, {target[1]}, {target[2]})\n"
                "constraint.target = target_obj\n"
                "constraint.track_axis = 'TRACK_NEGATIVE_Z'\n"
                "constraint.up_axis = 'UP_Y'\n"
            )
        try:
            await self.blender.execute_code(PythonCode(code))
            return Prompt("Camera setup successful")
        except Exception as e:
            logger.error(f"setup_camera failed: {e}")
            raise BlenderMCPError(ErrorMessage(f"Failed to setup camera: {e}")) from e

    async def setup_render(
        self,
        engine: RenderEngine | None = None,
        samples: RenderSamples | None = None,
        resolution: CoordinateList | None = None,
        use_denoising: UseDenoising | None = None,
    ) -> Prompt:
        engine = engine or RenderEngine("CYCLES")
        samples = samples or RenderSamples(128)
        use_denoising = use_denoising or UseDenoising(True)
        logger.info(f"Setting up render engine: {engine}")
        code = f"import bpy\nbpy.context.scene.render.engine = '{str(engine).upper()}'\n"
        if str(engine).upper() == "CYCLES":
            code += (
                f"bpy.context.scene.cycles.samples = {int(samples)}\n"
                f"bpy.context.scene.cycles.use_denoising = {str(bool(use_denoising))}\n"
            )
        if resolution is not None:
            code += (
                f"bpy.context.scene.render.resolution_x = {resolution[0]}\n"
                f"bpy.context.scene.render.resolution_y = {resolution[1]}\n"
            )
        try:
            await self.blender.execute_code(PythonCode(code))
            return Prompt(f"Render configured for {engine}")
        except Exception as e:
            logger.error(f"setup_render failed: {e}")
            raise BlenderMCPError(ErrorMessage(f"Failed to configure render: {e}")) from e

    async def apply_composition(self, rule: RuleName | None = None) -> Prompt:
        rule = rule or RuleName("thirds")
        logger.info(f"Applying composition rule: {rule}")
        code = (
            "import bpy\n"
            "camera = bpy.data.objects.get('Camera')\n"
            "if camera and camera.type == 'CAMERA':\n"
            "    camera.data.show_guide = True\n"
            f"    if '{rule}' == 'thirds':\n"
            f"        camera.data.show_guide_rule_of_thirds = True\n"
            f"    elif '{rule}' == 'golden':\n"
            f"        camera.data.show_guide_golden_ratio = True\n"
        )
        try:
            await self.blender.execute_code(PythonCode(code))
            return Prompt(f"Composition rule {rule} applied")
        except Exception as e:
            logger.error(f"apply_composition failed: {e}")
            raise BlenderMCPError(ErrorMessage(f"Failed to apply composition: {e}")) from e

    async def render(self, request: RenderRequestVO) -> RenderResponseVO:
        logger.info(f"Rendering frame to {request.output_path}")
        code = (
            "import bpy\n"
            f"bpy.context.scene.render.filepath = '{request.output_path}'\n"
            f"bpy.ops.render.render(write_still=True)\n"
        )
        try:
            await self.blender.execute_code(PythonCode(code))
            return RenderResponseVO(
                success=SuccessFlag(True), image_path=request.output_path, render_time=1.5, message="Render complete"
            )
        except Exception as e:
            logger.error(f"Render failed: {e}")
            raise BlenderMCPError(ErrorMessage(f"Render failed: {e}")) from e
