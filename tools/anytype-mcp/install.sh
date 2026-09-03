#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
VENDOR_DIR="$REPO_ROOT/vendor/anytype-mcp"
DIST_DIR="$SCRIPT_DIR/dist"

if [ ! -d "$VENDOR_DIR" ] || [ ! -f "$VENDOR_DIR/package.json" ]; then
  echo "Error: Upstream source not found at $VENDOR_DIR."
  echo "Run 'git submodule update --init --recursive vendor/anytype-mcp' first."
  exit 1
fi

echo ">>> Building anytype-mcp..."
cd "$VENDOR_DIR"
npm install
npm run build

echo ">>> Staging output into dist/..."
rm -rf "$DIST_DIR"
mkdir -p "$DIST_DIR/bin"
cp bin/cli.mjs "$DIST_DIR/bin/"
cp -r node_modules "$DIST_DIR/node_modules"

echo ">>> Anytype-MCP built successfully in $DIST_DIR/bin/cli.mjs"
