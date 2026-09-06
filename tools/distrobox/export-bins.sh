#!/usr/bin/env bash
# tools/distrobox/export-bins.sh
# Exports compiled tools from Distrobox container to host ~/.local/bin
set -euo pipefail

CONTAINER_NAME="agents-env"
SOURCE_BIN_DIR="${XDG_DATA_HOME:-$HOME/.local/share}/agents-arwaky/internal-bin"
TARGET_BIN_DIR="${XDG_BIN_HOME:-$HOME/.local/bin}"

TOOLS=(
  "context7-mcp"
  "ctx7"
  "fetch-mcp"
  "mcp-fetch"
  "lean-ctx"
  "ponytail-mcp"
  "anytype-mcp"
  "codegraph-mcp"
  "codegraph"
  "9router"
  "workspace-mcp"
  "mnemosyne"
  "mnemosyne-mcp"
  # Internal Tools (Full Names & Short Aliases)
  "lint-arwaky"
  "la"
  "lint-arwaky-cli"
  "lac"
  "lint-arwaky-mcp"
  "lint-arwaky-tui"
  "vision-arwaky"
  "va"
  "vision-arwaky-mcp"
  "qwen-web-arwaky"
  "qwa"
  "qwc"
  "qwen-web-mcp"
  "blender-arwaky"
  "ba"
  "blender-mcp"
)

FILTER_TOOL="${1:-}"

TARGET_LIST=()
if [ -n "$FILTER_TOOL" ]; then
  REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
  MANIFEST_FILE="$REPO_ROOT/tools/arwaky/manifest.json"
  if [ -f "$MANIFEST_FILE" ]; then
    MANIFEST_BIN="$(jq -r --arg q "$FILTER_TOOL" '.tools[] | select(.id == $q or .binary == $q or (.alias? != null and .alias == $q)) | .binary' "$MANIFEST_FILE" 2>/dev/null | head -n1 || true)"
    if [ -n "$MANIFEST_BIN" ]; then
      FILTER_TOOL="$MANIFEST_BIN"
    fi
  fi

  for tool in "${TOOLS[@]}"; do
    if [[ "$tool" == "$FILTER_TOOL"* ]] || [[ "$tool" == *"$FILTER_TOOL"* ]]; then
      TARGET_LIST+=("$tool")
    fi
  done
  if [[ "$FILTER_TOOL" == *"context7"* ]]; then
    TARGET_LIST+=("ctx7")
  fi
  if [[ "$FILTER_TOOL" == *"codegraph"* ]]; then
    TARGET_LIST+=("codegraph" "codegraph-mcp")
  fi
  if [[ "$FILTER_TOOL" == *"lint"* ]]; then
    TARGET_LIST+=("la" "lac")
  fi
  if [[ "$FILTER_TOOL" == *"vision"* ]]; then
    TARGET_LIST+=("va")
  fi
  if [[ "$FILTER_TOOL" == *"qwen-web"* ]]; then
    TARGET_LIST+=("qwa" "qwc" "qwen-web-mcp")
  fi
  if [[ "$FILTER_TOOL" == *"blender"* ]]; then
    TARGET_LIST+=("ba" "blender-mcp")
  fi
  if [ ${#TARGET_LIST[@]} -eq 0 ]; then
    TARGET_LIST+=("$FILTER_TOOL")
  fi
else
  TARGET_LIST=("${TOOLS[@]}")
fi

echo "=========================================="
echo " Exporting Binaries from Distrobox ($CONTAINER_NAME)"
echo "=========================================="

mkdir -p "$TARGET_BIN_DIR"

for tool in "${TARGET_LIST[@]}"; do
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
