#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
# shellcheck source=/dev/null
source "$REPO_ROOT/tools/lib/xdg.sh"

INTERNAL_DIR="$REPO_ROOT/internal/vision-arwaky"
TARGET_BIN="$XDG_BIN_HOME"

if [ ! -d "$INTERNAL_DIR" ]; then
  echo ">>> Initializing submodule internal/vision-arwaky..."
  git -C "$REPO_ROOT" submodule update --init internal/vision-arwaky
fi

echo ">>> Building vision-arwaky (Computer Vision) into $TARGET_BIN..."
mkdir -p "$TARGET_BIN"

(
  cd "$INTERNAL_DIR"
  XDG_BIN_HOME="$TARGET_BIN" \
  bash "$INTERNAL_DIR/scripts/install.local.sh"
)

# Ensure official alias 'va' exists
if [ -f "$TARGET_BIN/vision-arwaky" ]; then
  ln -sf "$TARGET_BIN/vision-arwaky" "$TARGET_BIN/va"
  echo ">>> Verified official alias: $TARGET_BIN/va -> vision-arwaky"
elif [ -f "$TARGET_BIN/vision-arwaky-cli" ]; then
  ln -sf "$TARGET_BIN/vision-arwaky-cli" "$TARGET_BIN/vision-arwaky"
  ln -sf "$TARGET_BIN/vision-arwaky-cli" "$TARGET_BIN/va"
  echo ">>> Created official aliases: $TARGET_BIN/vision-arwaky, $TARGET_BIN/va -> vision-arwaky-cli"
fi

echo ">>> Successfully installed vision-arwaky -> $TARGET_BIN"
