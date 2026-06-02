import bpy  # type: ignore
from bpy.props import BoolProperty  # type: ignore


class BLENDERMCP_AddonPreferences(bpy.types.AddonPreferences):
    bl_idname = __package__

    telemetry_consent: BoolProperty(  # type: ignore
        name="Allow Telemetry",
        description="Allow collection of prompts, code snippets, and screenshots to help improve Blender MCP",
        default=False,
    )

    def draw(self, context):
        layout = self.layout

        # Telemetry section
        layout.label(text="Telemetry & Privacy:", icon="PREFERENCES")

        box = layout.box()
        row = box.row()
        row.prop(self, "telemetry_consent", text="Allow Telemetry")

        # Info text
        box.separator()
        if self.telemetry_consent:
            box.label(
                text="With consent: We collect anonymized prompts, code, and screenshots.",
                icon="INFO",
            )
        else:
            box.label(
                text="Without consent: We only collect minimal anonymous usage data",
                icon="INFO",
            )
            box.label(
                text="(tool names, success/failure, duration - no prompts or code).",
                icon="BLANK1",
            )
        box.separator()
        box.label(
            text="All data is fully anonymized. You can change this anytime.",
            icon="CHECKMARK",
        )

        # Terms and Conditions link (removed — use local copy if needed)
        box.separator()


class BLENDERMCP_PT_Panel(bpy.types.Panel):
    bl_label = "Blender MCP"
    bl_idname = "BLENDERMCP_PT_Panel"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "BlenderMCP"

    def draw(self, context):
        layout = self.layout
        scene = context.scene

        layout.prop(scene, "blendermcp_port")
        layout.prop(scene, "blendermcp_use_polyhaven", text="Use assets from Poly Haven")

        layout.prop(
            scene,
            "blendermcp_use_hyper3d",
            text="Use Hyper3D Rodin 3D model generation",
        )
        if scene.blendermcp_use_hyper3d:
            layout.prop(scene, "blendermcp_hyper3d_mode", text="Rodin Mode")
            layout.prop(scene, "blendermcp_hyper3d_api_key", text="API Key")
            # Free trial key removed — get your own key from hyper3d.ai

        layout.prop(scene, "blendermcp_use_sketchfab", text="Use assets from Sketchfab")
        if scene.blendermcp_use_sketchfab:
            layout.prop(scene, "blendermcp_sketchfab_api_key", text="API Key")

        layout.prop(
            scene,
            "blendermcp_use_hunyuan3d",
            text="Use Tencent Hunyuan 3D model generation",
        )
        if scene.blendermcp_use_hunyuan3d:
            layout.prop(scene, "blendermcp_hunyuan3d_mode", text="Hunyuan3D Mode")
            if scene.blendermcp_hunyuan3d_mode == "OFFICIAL_API":
                layout.prop(scene, "blendermcp_hunyuan3d_secret_id", text="SecretId")
                layout.prop(scene, "blendermcp_hunyuan3d_secret_key", text="SecretKey")
            if scene.blendermcp_hunyuan3d_mode == "LOCAL_API":
                layout.prop(scene, "blendermcp_hunyuan3d_api_url", text="API URL")
                layout.prop(
                    scene,
                    "blendermcp_hunyuan3d_octree_resolution",
                    text="Octree Resolution",
                )
                layout.prop(
                    scene,
                    "blendermcp_hunyuan3d_num_inference_steps",
                    text="Number of Inference Steps",
                )
                layout.prop(scene, "blendermcp_hunyuan3d_guidance_scale", text="Guidance Scale")
                layout.prop(scene, "blendermcp_hunyuan3d_texture", text="Generate Texture")

        is_running = (
            hasattr(bpy.types, "blendermcp_server")
            and bpy.types.blendermcp_server
            and getattr(bpy.types.blendermcp_server, "running", False)
        )

        if not is_running:
            layout.operator("blendermcp.start_server", text="Connect to MCP server")
        else:
            layout.operator("blendermcp.stop_server", text="Disconnect from MCP server")
            layout.label(text=f"Running on port {scene.blendermcp_port}")


classes = (
    BLENDERMCP_AddonPreferences,
    BLENDERMCP_PT_Panel,
)


def register() -> None:
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister() -> None:
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)  # type: ignore
