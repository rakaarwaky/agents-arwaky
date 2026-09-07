import bpy


bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.preferences.addon_enable(module="rigify")
bpy.ops.object.armature_human_metarig_add()
armature = bpy.context.object

mesh = bpy.data.meshes.new("Wave6ShapeKeyMesh")
mesh.from_pydata([(0.0, 0.0, 0.0), (1.0, 0.0, 0.0), (0.0, 1.0, 0.0)], [], [(0, 1, 2)])
mesh_object = bpy.data.objects.new("Wave6ShapeKeyMesh", mesh)
bpy.context.collection.objects.link(mesh_object)

basis = mesh_object.shape_key_add(name="Basis")
smile = mesh_object.shape_key_add(name="Smile")
smile.value = 0.75
smile.slider_min = 0.0
smile.slider_max = 1.0

if basis.name != "Basis":
    raise RuntimeError("Basis shape key was not created")
if smile.name != "Smile":
    raise RuntimeError("Smile shape key was not created")
if abs(smile.value - 0.75) > 1e-6:
    raise RuntimeError("Shape key value was not assigned")
if smile.slider_min != 0.0 or smile.slider_max != 1.0:
    raise RuntimeError("Shape key slider range was not assigned")

mesh_object.active_shape_key_index = 1
mesh_object.shape_key_remove(smile)
if mesh_object.data.shape_keys.key_blocks.get("Smile") is not None:
    raise RuntimeError("Shape key was not removed")

print(
    "WAVE6_RIGIFY_SHAPE_KEY_LIVE_OK",
    {
        "blender_version": bpy.app.version_string,
        "armature_name": armature.name,
        "mesh_name": mesh_object.name,
        "remaining_shape_keys": [item.name for item in mesh_object.data.shape_keys.key_blocks],
    },
)
