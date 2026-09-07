from pathlib import Path

import bpy
from mathutils import Vector

BLEND_PATH = Path("/home/ubuntu/mpfb_native_rigify_evidence/native_mpfb2_rigify_character.blend")
OUTPUT_PATH = Path("/home/ubuntu/mpfb_native_rigify_evidence/native_mpfb2_rigify_hand_closeup.png")

bpy.ops.wm.open_mainfile(filepath=str(BLEND_PATH))
scene = bpy.context.scene
rig = bpy.data.objects.get("Native_Render_Rigify_Control")
character = bpy.data.objects.get("Native_Render_MPFB2_Character")
if rig is None or character is None:
    raise RuntimeError("Native MPFB2 scene is missing character or Rigify rig")


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
    curve.bevel_resolution = 2
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


def is_left_hand_bone(bone):
    name = bone.name.lower()
    if not name.endswith(".l") and ".l." not in name:
        return False
    hand_terms = ("hand", "thumb", "f_index", "f_middle", "f_ring", "f_pinky", "f_little")
    return any(term in name for term in hand_terms)

hand_def = make_curve("Native_Rigify_Hand_DEF_Bones", make_material("Native_Rigify_Hand_DEF_Material", (1.0, 0.1, 0.02), 5.0), 0.0028)
hand_controls = make_curve("Native_Rigify_Hand_Control_Bones", make_material("Native_Rigify_Hand_Control_Material", (0.0, 0.95, 1.0), 5.0), 0.004)
hand_ik = make_curve("Native_Rigify_Hand_IK_Bones", make_material("Native_Rigify_Hand_IK_Material", (1.0, 0.65, 0.02), 5.0), 0.005)
def_count = 0
control_count = 0
ik_count = 0
for bone in rig.pose.bones:
    if not is_left_hand_bone(bone):
        continue
    offset = Vector((0.0, -0.014, 0.004))
    if bone.name.startswith("DEF-"):
        add_bone_line(hand_def, bone, offset)
        def_count += 1
    elif "_ik" in bone.name or "target" in bone.name.lower():
        add_bone_line(hand_ik, bone, offset * 1.4)
        ik_count += 1
    elif not bone.name.startswith(("MCH-", "ORG-")):
        add_bone_line(hand_controls, bone, offset * 1.2)
        control_count += 1


def look_at(obj, target):
    obj.rotation_euler = (target - obj.location).to_track_quat("-Z", "Y").to_euler()

hand_target = Vector((0.49, -0.285, 0.98))
camera = scene.camera
camera.location = Vector((0.49, -1.05, 1.02))
look_at(camera, hand_target)
camera.data.lens = 90
camera.data.sensor_width = 36
scene.render.engine = "BLENDER_EEVEE"
scene.render.resolution_x = 1100
scene.render.resolution_y = 900
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = "PNG"
scene.render.filepath = str(OUTPUT_PATH)
for obj in scene.objects:
    if obj.type == "ARMATURE":
        obj.hide_render = True
bpy.ops.render.render(write_still=True)
print(
    "NATIVE_RIGIFY_HAND_CLOSEUP_OK",
    {
        "image": str(OUTPUT_PATH),
        "def_bone_count": def_count,
        "control_bone_count": control_count,
        "ik_bone_count": ik_count,
        "camera_target": tuple(round(v, 4) for v in hand_target),
        "lens": camera.data.lens,
    },
)
