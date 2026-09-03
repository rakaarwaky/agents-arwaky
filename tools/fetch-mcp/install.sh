#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
VENDOR_DIR="$REPO_ROOT/vendor/fetch-mcp"
DIST_DIR="$SCRIPT_DIR/dist"

if [ ! -d "$VENDOR_DIR" ] || [ ! -f "$VENDOR_DIR/package.json" ]; then
  echo "Error: Upstream source not found at $VENDOR_DIR."
  echo "Run 'git submodule update --init --recursive vendor/fetch-mcp' first."
  exit 1
fi

echo ">>> Building Fetch-MCP..."
mkdir -p "$DIST_DIR"

cd "$VENDOR_DIR"
npm install

echo ">>> Compiling with esbuild..."
npx -y esbuild src/index.ts \
  --bundle \
  --platform=node \
  --format=esm \
  --outfile="$DIST_DIR/index.js" \
  --external:jsdom \
  --external:@mozilla/readability \
  --external:turndown \
  --external:private-ip \
  --external:@modelcontextprotocol/sdk \
  --external:zod

ln -sfn "$VENDOR_DIR/node_modules" "$DIST_DIR/node_modules"
chmod 755 "$DIST_DIR/index.js"

echo ">>> Fetch-MCP built successfully in $DIST_DIR/index.js"
