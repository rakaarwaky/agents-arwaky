#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
VENDOR_DIR="$REPO_ROOT/vendor/lean-ctx"
DIST_DIR="$SCRIPT_DIR/dist"

if [ ! -d "$VENDOR_DIR/rust" ]; then
  echo "Error: Upstream source not found at $VENDOR_DIR/rust."
  echo "Run 'git submodule update --init --recursive vendor/lean-ctx' first."
  exit 1
fi

echo ">>> Building lean-ctx (release)..."
mkdir -p "$DIST_DIR"
cd "$VENDOR_DIR/rust"
export RUST_MIN_STACK=67108864
cargo build --release --locked

cp "$VENDOR_DIR/rust/target/release/lean-ctx" "$DIST_DIR/lean-ctx"
chmod 755 "$DIST_DIR/lean-ctx"

echo ">>> Installing to ~/.local/bin/..."
mkdir -p "$HOME/.local/bin"
cp "$DIST_DIR/lean-ctx" "$HOME/.local/bin/lean-ctx"
chmod 755 "$HOME/.local/bin/lean-ctx"

echo ">>> Setting up Qwen Code integration..."
export PATH="$HOME/.local/bin:$PATH"
if command -v lean-ctx >/dev/null 2>&1; then
  lean-ctx init --agent qwen || true
  echo ">>> Qwen Code integration initialized."
fi

echo ">>> Done! Binary ready at $DIST_DIR/lean-ctx and ~/.local/bin/lean-ctx"
