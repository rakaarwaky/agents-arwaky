#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
VENDOR_DIR="$REPO_ROOT/vendor/ponytail"
MCP_DIR="$VENDOR_DIR/ponytail-mcp"
DIST_DIR="$SCRIPT_DIR/dist"

if [ ! -d "$MCP_DIR" ]; then
  echo "Error: Upstream source not found at $MCP_DIR."
  echo "Run 'git submodule update --init --recursive vendor/ponytail' first."
  exit 1
fi

echo ">>> Building Ponytail MCP..."
mkdir -p "$DIST_DIR"

cp "$MCP_DIR/package.json" "$DIST_DIR/"
npm install --prefix "$DIST_DIR"

cp "$MCP_DIR/index.js" "$DIST_DIR/"
cp "$MCP_DIR/instructions.js" "$DIST_DIR/"

rm -rf "$SCRIPT_DIR/hooks" "$SCRIPT_DIR/skills"
cp -r "$VENDOR_DIR/hooks" "$SCRIPT_DIR/hooks"
cp -r "$VENDOR_DIR/skills" "$SCRIPT_DIR/skills"
cp "$VENDOR_DIR/package.json" "$SCRIPT_DIR/package.json"

chmod 755 "$DIST_DIR/index.js"
echo ">>> Ponytail MCP built successfully in $DIST_DIR/index.js"
