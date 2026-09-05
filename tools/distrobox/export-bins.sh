#!/usr/bin/env bash
# tools/distrobox/export-bins.sh
# Exports compiled tools from Distrobox container to host ~/.local/bin
set -euo pipefail

CONTAINER_NAME="agents-env"
SOURCE_BIN_DIR="${XDG_DATA_HOME:-$HOME/.local/share}/agents-arwaky/internal-bin"
TARGET_BIN_DIR="${XDG_BIN_HOME:-$HOME/.local/bin}"

TOOLS=(
  "context7-mcp"
  "fetch-mcp"
  "lean-ctx"
  "ponytail-mcp"
  "anytype-mcp"
  "codegraph-mcp"
  "9router"
  "vision-arwaky"
  "vision-arwaky-mcp"
  "qwen-web-arwaky"
  "qwc"
  "qwen-web-mcp"
  "lint-arwaky-cli"
  "lac"
  "lint-arwaky-mcp"
  "lint-arwaky-tui"
  "blender-arwaky"
  "blender-mcp"
)

echo "=========================================="
echo " Exporting Binaries from Distrobox ($CONTAINER_NAME)"
echo "=========================================="

mkdir -p "$TARGET_BIN_DIR"

for tool in "${TOOLS[@]}"; do
  if distrobox enter "$CONTAINER_NAME" -- test -e "$SOURCE_BIN_DIR/$tool" 2>/dev/null; then
    echo "Exporting: $tool..."
    distrobox enter "$CONTAINER_NAME" -- distrobox-export \
      --bin "$SOURCE_BIN_DIR/$tool" \
      --export-path "$TARGET_BIN_DIR"
  else
    echo "Skipping: $tool (not found in $SOURCE_BIN_DIR)"
  fi
done

echo "Linking orchestrator: agents-arwaky & aa..."
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
ln -sf "$REPO_ROOT/agents-arwaky" "$TARGET_BIN_DIR/agents-arwaky"
ln -sf "$REPO_ROOT/agents-arwaky" "$TARGET_BIN_DIR/aa"
rm -f "$TARGET_BIN_DIR/arwaky"

echo "=========================================="
echo " All binaries exported successfully to $TARGET_BIN_DIR"
echo "=========================================="
