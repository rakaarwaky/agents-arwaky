#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
# shellcheck source=/dev/null
source "$REPO_ROOT/tools/lib/xdg.sh"

VENDOR_DIR="$REPO_ROOT/vendor/lean-ctx"
TARGET_DIR="$XDG_DATA_HOME/lean-ctx"
LAUNCHER="$XDG_BIN_HOME/lean-ctx"

mkdir -p "$TARGET_DIR/bin"

CARGO_DIR="$VENDOR_DIR"
if [ -f "$VENDOR_DIR/rust/Cargo.toml" ]; then
  CARGO_DIR="$VENDOR_DIR/rust"
fi

if command -v cargo >/dev/null 2>&1; then
  echo ">>> Building lean-ctx from source with cargo..."
  cargo install --path "$CARGO_DIR" --root "$TARGET_DIR"
elif [ -f "$LAUNCHER" ]; then
  echo ">>> Existing lean-ctx binary found at $LAUNCHER"
else
  echo ">>> Cargo not found. Fetching official release binary for Linux..."
  ARCH="$(uname -m)"
  case "$ARCH" in
    x86_64)  ASSET_NAME="lean-ctx-x86_64-unknown-linux-gnu.tar.gz" ;;
    aarch64) ASSET_NAME="lean-ctx-aarch64-unknown-linux-gnu.tar.gz" ;;
    *) echo "Unsupported architecture: $ARCH" >&2; exit 1 ;;
  esac
  RELEASE_URL="https://github.com/yvgude/lean-ctx/releases/download/v3.10.0/$ASSET_NAME"
  echo ">>> Downloading $RELEASE_URL..."
  curl -sL "$RELEASE_URL" | tar -xzf - -C "$TARGET_DIR/bin"
  chmod +x "$TARGET_DIR/bin/lean-ctx"
fi

if [ -f "$TARGET_DIR/bin/lean-ctx" ]; then
  cp "$TARGET_DIR/bin/lean-ctx" "$LAUNCHER"
  chmod +x "$LAUNCHER"
  echo ">>> Successfully installed lean-ctx -> $LAUNCHER"
  "$LAUNCHER" --version
fi
