from pathlib import Path

import bpy
from mathutils import Vector

BLEND_PATH = Path("/home/ubuntu/mpfb_native_rigify_evidence/native_mpfb2_rigify_character.blend")
OUTPUT_PATH = Path("/home/ubuntu/mpfb_native_rigify_evidence/native_mpfb2_rigify_full_skeleton.png")

bpy.ops.wm.open_mainfile(filepath=str(BLEND_PATH))
scene = bpy.context.scene
character = bpy.data.objects.get("Native_Render_MPFB2_Character")
rig = bpy.data.objects.get("Native_Render_Rigify_Control")
camera = scene.camera
if character is None or rig is None or camera is None:
    raise RuntimeError("Native MPFB2 scene is missing character, rig, or camera")


def make_material(name, color, strength):
    material = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    material.use_nodes = True
    nodes = material.node_tree.nodes
    links = material.node_tree.links
    nodes.clear()
    emission = nodes.new("ShaderNodeEmission")
    emission.inputs["Color"].default_value = (*color, 1.0)
    emission.inputs["Strength"].default_value = strength
    output = nodes.new("ShaderNodeOutputMaterial")
    links.new(emission.outputs[0], output.inputs[0])
    return material


def make_curve(name, material, bevel_depth):
    curve = bpy.data.curves.new(name, type="CURVE")
    curve.dimensions = "3D"
    curve.bevel_depth = bevel_depth
    curve.bevel_resolution = 1
    curve.materials.append(material)
    obj = bpy.data.objects.new(name, curve)
    bpy.context.collection.objects.link(obj)
    return curve


def add_bone_line(curve, bone, offset):
    spline = curve.splines.new("POLY")
    spline.points.add(1)
    head = rig.matrix_world @ Vector(bone.head) + offset
    tail = rig.matrix_world @ Vector(bone.tail) + offset
    spline.points[0].co = (head.x, head.y, head.z, 1.0)
    spline.points[1].co = (tail.x, tail.y, tail.z, 1.0)

all_curve = make_curve("Native_Rigify_Full_Skeleton", make_material("Native_Rigify_All_Bones", (0.18, 0.35, 0.95), 2.0), 0.0025)
control_curve = make_curve("Native_Rigify_Control_Bones", make_material("Native_Rigify_Control_Bones", (0.0, 1.0, 0.18), 4.0), 0.006)
ik_curve = make_curve("Native_Rigify_IK_Targets", make_material("Native_Rigify_IK_Targets", (1.0, 0.55, 0.01), 5.0), 0.009)
center = character.location.copy()
offset = (camera.location - center).normalized() * 0.055
for bone in rig.pose.bones:
    add_bone_line(all_curve, bone, offset)
    if bone.name.startswith(("DEF-", "ORG-", "MCH-")):
        continue
    if "_ik" in bone.name or "_ik_" in bone.name or bone.name.endswith("_ik"):
        add_bone_line(ik_curve, bone, offset * 1.35)
    else:
        add_bone_line(control_curve, bone, offset * 1.2)

rig.show_in_front = True
rig.hide_viewport = False
rig.data.display_type = "OCTAHEDRAL"
scene.render.engine = "BLENDER_EEVEE"
scene.render.filepath = str(OUTPUT_PATH)
scene.render.image_settings.file_format = "PNG"
scene.render.resolution_x = 900
scene.render.resolution_y = 1100
scene.render.resolution_percentage = 100
for obj in scene.objects:
    if obj.type == "ARMATURE":
        obj.hide_render = True
bpy.ops.render.render(write_still=True)
print(
    "NATIVE_RIGIFY_FULL_SKELETON_OK",
    {
        "image": str(OUTPUT_PATH),
        "rig": rig.name,
        "bone_count": len(rig.pose.bones),
        "control_bone_count": len(control_curve.splines),
        "ik_bone_count": len(ik_curve.splines),
        "show_in_front": rig.show_in_front,
        "display_type": rig.data.display_type,
    },
)
