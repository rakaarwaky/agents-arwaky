from pathlib import Path

import bpy
from mathutils import Vector

BLEND_PATH = Path("/home/ubuntu/mpfb_native_rigify_evidence/native_mpfb2_rigify_character.blend")
OUTPUT_PATH = Path("/home/ubuntu/mpfb_native_rigify_evidence/native_mpfb2_rigify_front_overlay.png")

bpy.ops.wm.open_mainfile(filepath=str(BLEND_PATH))
scene = bpy.context.scene
character = bpy.data.objects.get("Native_Render_MPFB2_Character")
rig = bpy.data.objects.get("Native_Render_Rigify_Control")
camera = scene.camera
if character is None or rig is None or camera is None:
    raise RuntimeError("Native MPFB2 scene is missing character, rig, or camera")

material = bpy.data.materials.get("Native_Rigify_Front_Material") or bpy.data.materials.new("Native_Rigify_Front_Material")
material.use_nodes = True
nodes = material.node_tree.nodes
links = material.node_tree.links
nodes.clear()
emission = nodes.new("ShaderNodeEmission")
emission.inputs["Color"].default_value = (1.0, 0.03, 0.005, 1.0)
emission.inputs["Strength"].default_value = 5.0
output = nodes.new("ShaderNodeOutputMaterial")
links.new(emission.outputs[0], output.inputs[0])

curve = bpy.data.curves.new("Native_Rigify_Front_Overlay_Curve", type="CURVE")
curve.dimensions = "3D"
curve.bevel_depth = 0.007
curve.bevel_resolution = 1
curve.materials.append(material)
overlay = bpy.data.objects.new("Native_Rigify_Front_Overlay", curve)
bpy.context.collection.objects.link(overlay)
center = character.location.copy()
offset = (camera.location - center).normalized() * 0.04
primary = (
    "upper_arm_ik.L", "forearm_fk.L", "hand_ik.L", "upper_arm_ik.R", "forearm_fk.R", "hand_ik.R",
    "foot_ik.L", "foot_heel_ik.L", "foot_ik.R", "foot_heel_ik.R", "thigh_ik_target.L", "thigh_ik_target.R",
    "DEF-spine", "DEF-spine.001", "DEF-spine.002", "DEF-spine.003", "DEF-spine.004", "DEF-neck", "DEF-head",
    "DEF-thigh.L", "DEF-shin.L", "DEF-foot.L", "DEF-thigh.R", "DEF-shin.R", "DEF-foot.R",
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
print("NATIVE_RIGIFY_FRONT_OVERLAY_OK", {"image": str(OUTPUT_PATH), "rig": rig.name, "show_in_front": rig.show_in_front, "display_type": rig.data.display_type})
