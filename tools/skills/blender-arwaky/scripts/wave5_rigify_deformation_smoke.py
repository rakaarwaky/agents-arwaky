import bpy


bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.preferences.addon_enable(module="rigify")
bpy.ops.object.armature_human_metarig_add()
armature = bpy.context.object

mesh = bpy.data.meshes.new("Wave5DeformationMesh")
mesh.from_pydata([(0.0, 0.0, 0.0), (1.0, 0.0, 0.0), (0.0, 1.0, 0.0)], [], [(0, 1, 2)])
mesh_object = bpy.data.objects.new("Wave5DeformationMesh", mesh)
bpy.context.collection.objects.link(mesh_object)

modifier = mesh_object.modifiers.new(name="RigifyArmature", type="ARMATURE")
modifier.object = armature
basis = mesh_object.shape_key_add(name="Basis")
smile = mesh_object.shape_key_add(name="Smile")
smile.value = 0.5

pose_bone = armature.pose.bones.get("upper_arm.L")
if pose_bone is None:
    raise RuntimeError("Rigify metarig bone not found")
constraint = pose_bone.constraints.new(type="COPY_ROTATION")
constraint.name = "Wave5CopyRotation"

armature_modifiers = [item for item in mesh_object.modifiers if item.type == "ARMATURE"]
shape_keys = [item.name for item in mesh_object.data.shape_keys.key_blocks]
constraints = [item.name for item in pose_bone.constraints]

if len(armature_modifiers) != 1:
    raise RuntimeError("Expected one armature modifier")
if shape_keys != ["Basis", "Smile"]:
    raise RuntimeError(f"Unexpected shape keys: {shape_keys}")
if "Wave5CopyRotation" not in constraints:
    raise RuntimeError("Expected deformation constraint")

print(
    "WAVE5_RIGIFY_DEFORMATION_LIVE_OK",
    {
        "blender_version": bpy.app.version_string,
        "mesh_name": mesh_object.name,
        "armature_name": armature.name,
        "armature_modifiers": len(armature_modifiers),
        "shape_keys": shape_keys,
        "constraints": constraints,
    },
)
