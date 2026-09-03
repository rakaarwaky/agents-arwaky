#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
VENDOR_DIR="$REPO_ROOT/vendor/context7"
DIST_DIR="$SCRIPT_DIR/dist"
MCP_DIR="$VENDOR_DIR/packages/mcp"

if [ ! -d "$VENDOR_DIR" ] || [ ! -f "$MCP_DIR/package.json" ]; then
  echo "Error: Upstream source not found at $VENDOR_DIR."
  echo "Run 'git submodule update --init --recursive vendor/context7' first."
  exit 1
fi

echo ">>> Building Context7 MCP..."
mkdir -p "$DIST_DIR"
cp "$MCP_DIR/package.json" "$DIST_DIR/"
npm install --prefix "$DIST_DIR"

if [ -d "$MCP_DIR/node_modules" ] && [ ! -L "$MCP_DIR/node_modules" ]; then
  mv "$MCP_DIR/node_modules" "$MCP_DIR/node_modules.bak"
fi

ln -sfn "$DIST_DIR/node_modules" "$MCP_DIR/node_modules"
cd "$MCP_DIR"
npx -p typescript tsc --outDir "$DIST_DIR" --skipLibCheck --module es2020 --moduleResolution node
rm -f "$MCP_DIR/node_modules"

if [ -d "$MCP_DIR/node_modules.bak" ]; then
  mv "$MCP_DIR/node_modules.bak" "$MCP_DIR/node_modules"
fi

echo ">>> Pruning dev dependencies..."
npm prune --prefix "$DIST_DIR" --omit=dev

cp "$MCP_DIR/package.json" "$SCRIPT_DIR/package.json"
chmod 755 "$DIST_DIR/index.js"

echo ">>> Context7 built successfully in $DIST_DIR/index.js"
