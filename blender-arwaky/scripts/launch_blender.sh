#!/bin/bash
# Launcher script for Blender with correct path and display env

BLENDER="/home/raka/SharedData/App/Blender/blender"

# Set display for GUI mode
export DISPLAY=:0
export WAYLAND_DISPLAY=wayland-1

# Optionally force software rendering
# export LIBGL_ALWAYS_SOFTWARE=1

"$BLENDER" "$@"
