#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
# shellcheck source=/dev/null
source "$REPO_ROOT/tools/lib/xdg.sh"

INTERNAL_DIR="$REPO_ROOT/internal/qwen-web-arwaky"
TARGET_BIN="$XDG_BIN_HOME"

if [ ! -d "$INTERNAL_DIR" ]; then
  echo ">>> Initializing submodule internal/qwen-web-arwaky..."
  git -C "$REPO_ROOT" submodule update --init internal/qwen-web-arwaky
fi

echo ">>> Building qwen-web-arwaky into $TARGET_BIN..."
mkdir -p "$TARGET_BIN"

(
  cd "$INTERNAL_DIR"
  XDG_BIN_HOME="$TARGET_BIN" \
  bash "$INTERNAL_DIR/scripts/install.sh"
)

# Ensure official alias 'qwa' and 'qwen-web-arwaky' exist
if [ -f "$TARGET_BIN/qwen-web-arwaky" ]; then
  ln -sf "$TARGET_BIN/qwen-web-arwaky" "$TARGET_BIN/qwa"
  echo ">>> Verified official alias: $TARGET_BIN/qwa -> qwen-web-arwaky"
elif [ -f "$TARGET_BIN/qwen-web-cli" ]; then
  ln -sf "$TARGET_BIN/qwen-web-cli" "$TARGET_BIN/qwen-web-arwaky"
  ln -sf "$TARGET_BIN/qwen-web-cli" "$TARGET_BIN/qwa"
  echo ">>> Created official aliases: $TARGET_BIN/qwen-web-arwaky, $TARGET_BIN/qwa -> qwen-web-cli"
fi

echo ">>> Successfully installed qwen-web-arwaky -> $TARGET_BIN"
