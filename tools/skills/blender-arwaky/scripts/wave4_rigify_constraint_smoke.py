import bpy


bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.preferences.addon_enable(module="rigify")
bpy.ops.object.armature_human_metarig_add()
armature = bpy.context.object
bone_name = "upper_arm.L"
pose_bone = armature.pose.bones.get(bone_name)
if pose_bone is None:
    raise RuntimeError(f"Rigify metarig bone not found: {bone_name}")

target = bpy.data.objects.new("Wave4ConstraintTarget", None)
bpy.context.collection.objects.link(target)
constraint = pose_bone.constraints.new(type="COPY_ROTATION")
constraint.name = "Arwaky_CopyRotation"
constraint.target = target
constraint.subtarget = "upper_arm.L"

if pose_bone.constraints.get("Arwaky_CopyRotation") is None:
    raise RuntimeError("Rigify pose bone constraint was not created")
if constraint.type != "COPY_ROTATION":
    raise RuntimeError(f"Unexpected constraint type: {constraint.type}")
if constraint.target != target:
    raise RuntimeError("Constraint target object was not assigned")

pose_bone.constraints.remove(constraint)
if pose_bone.constraints.get("Arwaky_CopyRotation") is not None:
    raise RuntimeError("Rigify pose bone constraint was not removed")

print(
    "WAVE4_RIGIFY_CONSTRAINT_LIVE_OK",
    {
        "blender_version": bpy.app.version_string,
        "armature_name": armature.name,
        "bone_name": bone_name,
        "constraint_type": "COPY_ROTATION",
        "target_object": target.name,
    },
)
