"""Render the saved MPFB2 character scene with bounded low-memory settings."""

from __future__ import annotations

from pathlib import Path

import bpy

output_path = Path("/home/ubuntu/blender-arwaky/artifacts/wave5b_mpfb2_character.png")
scene = bpy.context.scene
scene.render.engine = "BLENDER_EEVEE"
scene.render.resolution_x = 320
scene.render.resolution_y = 320
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = "PNG"
scene.render.filepath = str(output_path)
scene.render.film_transparent = False
scene.render.image_settings.color_mode = "RGBA"
scene.render.image_settings.color_depth = "8"
scene.render.engine = "BLENDER_EEVEE"
bpy.ops.render.render(write_still=True)
print("WAVE5B_LOW_MEMORY_RENDER_OK")
print(output_path)
