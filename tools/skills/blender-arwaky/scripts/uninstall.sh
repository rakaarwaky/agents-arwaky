#!/usr/bin/env bash
# scripts/uninstall.sh — Clean uninstaller for blender-arwaky
set -euo pipefail

BIN_DIR="${XDG_BIN_HOME:-$HOME/.local/bin}"
DATA_DIR="${XDG_DATA_HOME:-$HOME/.local/share}/blender-arwaky"
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

echo "=== Uninstalling blender-arwaky ==="

# Remove bin wrappers
COMMANDS=("blender-arwaky" "blender-cli" "blender-mcp")
for cmd in "${COMMANDS[@]}"; do
    if [ -f "$BIN_DIR/$cmd" ]; then
        rm -f "$BIN_DIR/$cmd"
        echo "✓ Removed $BIN_DIR/$cmd"
    fi
done

# Remove in-tree .venv symlink if it points to XDG
for name in ".venv" "venv"; do
    if [ -L "$PROJECT_DIR/$name" ]; then
        rm -f "$PROJECT_DIR/$name"
        echo "✓ Removed $PROJECT_DIR/$name symlink"
    fi
done

if [[ "${1:-}" == "--purge" ]]; then
    if [ -d "$DATA_DIR" ]; then
        rm -rf "$DATA_DIR"
        echo "✓ Purged $DATA_DIR"
    fi
fi

echo "Uninstall complete."
