#!/usr/bin/env bash
# tools/distrobox/export-bins.sh
# Exports compiled tools from Distrobox container to host ~/.local/bin
set -euo pipefail

CONTAINER_NAME="agents-env"
SOURCE_BIN_DIR="${XDG_DATA_HOME:-$HOME/.local/share}/agents-arwaky/internal-bin"
TARGET_BIN_DIR="${XDG_BIN_HOME:-$HOME/.local/bin}"

FILTER_TOOL="${1:-}"

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
MANIFEST_FILE="$REPO_ROOT/tools/arwaky/manifest.json"

TARGET_LIST=()
if [ -n "$FILTER_TOOL" ]; then
  if [ -f "$MANIFEST_FILE" ]; then
    MANIFEST_BIN="$(jq -r --arg q "$FILTER_TOOL" '.tools[] | select(.id == $q or .binary == $q or (.alias? != null and .alias == $q)) | .binary' "$MANIFEST_FILE" 2>/dev/null | head -n1 || true)"
    [ -n "$MANIFEST_BIN" ] && FILTER_TOOL="$MANIFEST_BIN"
  fi

  for f in "$SOURCE_BIN_DIR"/*; do
    [ -e "$f" ] || continue
    b="$(basename "$f")"
    if [[ "$b" == *"$FILTER_TOOL"* ]]; then
      TARGET_LIST+=("$b")
    fi
  done
  [ ${#TARGET_LIST[@]} -eq 0 ] && TARGET_LIST+=("$FILTER_TOOL")
else
  for f in "$SOURCE_BIN_DIR"/*; do
    [ -e "$f" ] || continue
    TARGET_LIST+=("$(basename "$f")")
  done
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
