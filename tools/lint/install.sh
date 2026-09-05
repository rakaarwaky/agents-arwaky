#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
# shellcheck source=/dev/null
source "$REPO_ROOT/tools/lib/xdg.sh"

INTERNAL_DIR="$REPO_ROOT/internal/lint-arwaky"
TARGET_BIN="$XDG_BIN_HOME"

if [ ! -d "$INTERNAL_DIR" ] || [ ! -f "$INTERNAL_DIR/Cargo.toml" ]; then
  echo ">>> Initializing submodule internal/lint-arwaky..."
  git -C "$REPO_ROOT" submodule update --init internal/lint-arwaky
fi

if ! command -v cargo >/dev/null 2>&1; then
  echo "Error: cargo is required to build lint-arwaky." >&2
  echo "Please run inside Distrobox (make install) or install Rust on your host." >&2
  exit 1
fi

echo ">>> Building lint-arwaky (AES Architecture Linter) into $TARGET_BIN..."
mkdir -p "$TARGET_BIN"

# Call internal submodule's own local installer within its directory
(
  cd "$INTERNAL_DIR"
  LINT_ARWAKY_INSTALL_BIN="$TARGET_BIN" \
  XDG_BIN_HOME="$TARGET_BIN" \
  bash "$INTERNAL_DIR/scripts/install.local.sh"
)

# Create lac symlink as official short alias
if [ -f "$TARGET_BIN/lint-arwaky-cli" ]; then
  ln -sf "$TARGET_BIN/lint-arwaky-cli" "$TARGET_BIN/lac"
  echo ">>> Created official short alias: $TARGET_BIN/lac -> lint-arwaky-cli"
fi

echo ">>> Successfully installed lint-arwaky -> $TARGET_BIN"
