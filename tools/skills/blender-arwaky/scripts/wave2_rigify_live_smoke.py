import bpy


bpy.ops.wm.read_factory_settings(use_empty=True)

try:
    bpy.ops.preferences.addon_enable(module="rigify")
except Exception as error:
    raise RuntimeError(f"Rigify enable failed: {error}") from error

operator = getattr(getattr(bpy.ops, "object", None), "armature_human_metarig_add", None)
if not callable(operator):
    raise RuntimeError("Rigify human metarig operator is unavailable after enabling Rigify")

operator()
metarig = bpy.context.object
if metarig is None or metarig.type != "ARMATURE":
    raise RuntimeError("Rigify did not create an armature metarig")

if len(metarig.data.bones) == 0:
    raise RuntimeError("Rigify metarig contains no bones")

print(
    "WAVE2_RIGIFY_LIVE_OK",
    {
        "blender_version": bpy.app.version_string,
        "object_name": metarig.name,
        "bone_count": len(metarig.data.bones),
        "operator": "object.armature_human_metarig_add",
    },
)
