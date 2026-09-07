from pathlib import Path

import bpy
from mathutils import Vector

BLEND_PATH = Path("/home/ubuntu/mpfb_native_rigify_evidence/native_mpfb2_rigify_character.blend")
OUTPUT_PATH = Path("/home/ubuntu/mpfb_native_rigify_evidence/native_mpfb2_rigify_def_overlay.png")

bpy.ops.wm.open_mainfile(filepath=str(BLEND_PATH))
scene = bpy.context.scene
character = bpy.data.objects.get("Native_Render_MPFB2_Character")
rig = bpy.data.objects.get("Native_Render_Rigify_Control")
camera = scene.camera
if character is None or rig is None or camera is None:
    raise RuntimeError("Native MPFB2 scene is missing character, rig, or camera")

material = bpy.data.materials.get("Native_Rigify_DEF_Material") or bpy.data.materials.new("Native_Rigify_DEF_Material")
material.use_nodes = True
nodes = material.node_tree.nodes
links = material.node_tree.links
nodes.clear()
emission = nodes.new("ShaderNodeEmission")
emission.inputs["Color"].default_value = (0.95, 0.02, 0.01, 1.0)
emission.inputs["Strength"].default_value = 4.0
output = nodes.new("ShaderNodeOutputMaterial")
links.new(emission.outputs[0], output.inputs[0])

curve = bpy.data.curves.new("Native_Rigify_DEF_Overlay_Curve", type="CURVE")
curve.dimensions = "3D"
curve.bevel_depth = 0.006
curve.bevel_resolution = 1
curve.materials.append(material)
overlay = bpy.data.objects.new("Native_Rigify_DEF_Overlay", curve)
bpy.context.collection.objects.link(overlay)
center = character.location.copy()
offset = (camera.location - center).normalized() * 0.028
primary = (
    "DEF-spine", "DEF-spine.001", "DEF-spine.002", "DEF-spine.003", "DEF-spine.004", "DEF-spine.005",
    "DEF-neck", "DEF-head", "DEF-shoulder.L", "DEF-upper_arm.L", "DEF-forearm.L", "DEF-hand.L",
    "DEF-shoulder.R", "DEF-upper_arm.R", "DEF-forearm.R", "DEF-hand.R", "DEF-thigh.L", "DEF-shin.L",
    "DEF-foot.L", "DEF-toe.L", "DEF-thigh.R", "DEF-shin.R", "DEF-foot.R", "DEF-toe.R",
)
for name in primary:
    bone = rig.pose.bones.get(name)
    if bone is None:
        continue
    spline = curve.splines.new("POLY")
    spline.points.add(1)
    head = rig.matrix_world @ Vector(bone.head) + offset
    tail = rig.matrix_world @ Vector(bone.tail) + offset
    spline.points[0].co = (head.x, head.y, head.z, 1.0)
    spline.points[1].co = (tail.x, tail.y, tail.z, 1.0)

scene.render.engine = "BLENDER_EEVEE"
scene.render.filepath = str(OUTPUT_PATH)
scene.render.image_settings.file_format = "PNG"
scene.render.resolution_x = 700
scene.render.resolution_y = 900
scene.render.resolution_percentage = 100
for obj in scene.objects:
    if obj.type == "ARMATURE":
        obj.hide_render = True
bpy.ops.render.render(write_still=True)
print("NATIVE_RIGIFY_DEF_OVERLAY_OK", {"image": str(OUTPUT_PATH), "rig": rig.name, "bone_count": len(rig.data.bones)})
