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
)

echo "=========================================="
echo " Exporting Binaries from Distrobox ($CONTAINER_NAME)"
echo "=========================================="

mkdir -p "$TARGET_BIN_DIR"

for tool in "${TOOLS[@]}"; do
  echo "Exporting: $tool..."
  distrobox enter "$CONTAINER_NAME" -- distrobox-export \
    --bin "$SOURCE_BIN_DIR/$tool" \
    --export-path "$TARGET_BIN_DIR"
done

echo "Linking orchestrator: arwaky..."
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
ln -sf "$REPO_ROOT/arwaky" "$TARGET_BIN_DIR/arwaky"

echo "=========================================="
echo " All binaries exported successfully to $TARGET_BIN_DIR"
echo "=========================================="
