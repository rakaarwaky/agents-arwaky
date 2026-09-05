#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
# shellcheck source=/dev/null
source "$REPO_ROOT/tools/lib/xdg.sh"

INTERNAL_DIR="$REPO_ROOT/internal/blender-arwaky"
TARGET_BIN="$XDG_BIN_HOME"

if [ ! -d "$INTERNAL_DIR" ]; then
  echo ">>> Initializing submodule internal/blender-arwaky..."
  git -C "$REPO_ROOT" submodule update --init internal/blender-arwaky
fi

echo ">>> Building blender-arwaky into $TARGET_BIN..."
mkdir -p "$TARGET_BIN"

(
  cd "$INTERNAL_DIR"
  XDG_BIN_HOME="$TARGET_BIN" \
  bash "$INTERNAL_DIR/scripts/install/install.sh"
)

# Ensure official alias 'ba' exists
if [ -f "$TARGET_BIN/blender-arwaky" ]; then
  ln -sf "$TARGET_BIN/blender-arwaky" "$TARGET_BIN/ba"
  echo ">>> Verified official alias: $TARGET_BIN/ba -> blender-arwaky"
fi

echo ">>> Successfully installed blender-arwaky -> $TARGET_BIN"
