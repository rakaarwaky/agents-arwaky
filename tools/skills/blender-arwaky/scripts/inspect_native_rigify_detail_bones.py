from pathlib import Path

import bpy
from mathutils import Vector

BLEND_PATH = Path("/home/ubuntu/mpfb_native_rigify_evidence/native_mpfb2_rigify_character.blend")
bpy.ops.wm.open_mainfile(filepath=str(BLEND_PATH))
rig = bpy.data.objects.get("Native_Render_Rigify_Control")
character = bpy.data.objects.get("Native_Render_MPFB2_Character")
if rig is None or character is None:
    raise RuntimeError("Expected native MPFB2 character and Rigify control rig")

face_terms = ("head", "face", "jaw", "eye", "brow", "cheek", "lip", "nose", "ear", "teeth")
hand_terms = ("hand", "thumb", "f_index", "f_middle", "f_ring", "f_pinky", "f_little")

def dump_group(label, terms):
    selected = []
    for bone in rig.pose.bones:
        name = bone.name.lower()
        if any(term in name for term in terms):
            head = rig.matrix_world @ Vector(bone.head)
            tail = rig.matrix_world @ Vector(bone.tail)
            selected.append((bone.name, tuple(round(v, 4) for v in head), tuple(round(v, 4) for v in tail)))
    print(label, "count", len(selected))
    for item in selected:
        print(item)

dump_group("FACE_BONES", face_terms)
dump_group("HAND_BONES", hand_terms)
print("CHARACTER_LOCATION", tuple(round(v, 4) for v in character.location))
print("RIG_LOCATION", tuple(round(v, 4) for v in rig.location))
print("RIG_BONE_COUNT", len(rig.pose.bones))
