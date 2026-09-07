import bpy


bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.preferences.addon_enable(module="rigify")
bpy.ops.object.armature_human_metarig_add()
armature = bpy.context.object
bone_name = "upper_arm.L"
pose_bone = armature.pose.bones.get(bone_name)
if pose_bone is None:
    raise RuntimeError(f"Rigify metarig bone not found: {bone_name}")

rotation = [0.0, 0.5, 0.0]
pose_bone.rotation_mode = "XYZ"
pose_bone.rotation_euler = rotation
actual = list(pose_bone.rotation_euler)
if any(abs(actual[index] - rotation[index]) > 1e-6 for index in range(3)):
    raise RuntimeError(f"Pose transform mismatch: expected {rotation}, got {actual}")

print(
    "WAVE3_RIGIFY_POSE_LIVE_OK",
    {
        "blender_version": bpy.app.version_string,
        "armature_name": armature.name,
        "bone_name": bone_name,
        "rotation_euler": actual,
    },
)
