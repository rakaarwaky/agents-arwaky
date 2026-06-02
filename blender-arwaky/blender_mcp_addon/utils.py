import logging
import os
import shutil

import bpy  # type: ignore
import mathutils  # type: ignore

logger = logging.getLogger(__name__)


def _get_aabb(obj):
    """Calculate axis-aligned bounding box for an object in world space."""
    matrix = obj.matrix_world
    if obj.type == "MESH":
        coords = [matrix @ mathutils.Vector(v.co) for v in obj.data.vertices]
    else:
        coords = [matrix @ mathutils.Vector(v) for v in obj.bound_box]

    if not coords:
        return (0, 0, 0, 0, 0, 0)

    min_x = min(c[0] for c in coords)
    max_x = max(c[0] for c in coords)
    min_y = min(c[1] for c in coords)
    max_y = max(c[1] for c in coords)
    min_z = min(c[2] for c in coords)
    max_z = max(c[2] for c in coords)

    return (min_x, max_x, min_y, max_y, min_z, max_z)


def get_viewport_screenshot(filepath):
    """
    Captures a screenshot of the current viewport.
    FIX 7: If in headless mode, ensure a camera exists and is set as active.
    """
    is_headless = bpy.app.background

    if is_headless:
        # In headless mode, we need an active camera to render
        camera = bpy.context.scene.camera
        created_temp_camera = False
        if not camera:
            # Create a temporary camera if none exists
            bpy.ops.object.camera_add(location=(5, -5, 5), rotation=(1.1, 0, 0.78))
            camera = bpy.context.active_object
            bpy.context.scene.camera = camera
            created_temp_camera = True
            print("[BlenderMCP] Created temporary camera for headless screenshot")
            logger.info("Created temporary camera for headless screenshot")

        # Set render settings for quick screenshot
        bpy.context.scene.render.image_settings.file_format = "PNG"
        bpy.context.scene.render.filepath = filepath

        # Use EEVEE/Workbench for fast headless capture
        original_engine = bpy.context.scene.render.engine
        bpy.context.scene.render.engine = "BLENDER_EEVEE"

        bpy.ops.render.render(write_still=True)

        # Cleanup temporary camera
        if created_temp_camera and camera:
            bpy.data.objects.remove(camera, do_unlink=True)
            print("[BlenderMCP] Removed temporary camera")
            logger.info("Removed temporary camera")

        # Restore engine
        bpy.context.scene.render.engine = original_engine
    else:
        # GUI mode: use screencast or opengl render
        bpy.ops.render.opengl(write_still=True)
        # The above saves to render.filepath, so we move it
        render_path = bpy.context.scene.render.frame_path()
        if os.path.exists(render_path):
            shutil.move(render_path, filepath)

    return filepath


def clean_imported_glb(filepath, mesh_name=None):
    """Imports a GLB, finds the mesh, and renames it. Returns the mesh object."""
    existing_objects = set(bpy.data.objects.keys())
    bpy.ops.import_scene.gltf(filepath=filepath)
    bpy.context.view_layer.update()

    new_objects = [bpy.data.objects[name] for name in set(bpy.data.objects.keys()) - existing_objects]
    if not new_objects:
        return None

    # Find the main mesh
    mesh_obj = next((o for o in new_objects if o.type == "MESH"), None)
    if not mesh_obj:
        # Check children of empty nodes (common in GLTF imports)
        for o in new_objects:
            if o.type == "EMPTY" and o.children:
                mesh_obj = next((c for c in o.children if c.type == "MESH"), None)
                if mesh_obj:
                    mesh_obj.parent = None
                    bpy.data.objects.remove(o)
                    break

    if mesh_obj and mesh_name:
        mesh_obj.name = mesh_name
        if mesh_obj.data:
            mesh_obj.data.name = mesh_name

    return mesh_obj
