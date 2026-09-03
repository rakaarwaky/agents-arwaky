#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
VENDOR_DIR="$REPO_ROOT/vendor/codegraph"
DIST_DIR="$SCRIPT_DIR/dist"

if [ ! -d "$VENDOR_DIR" ] || [ ! -f "$VENDOR_DIR/package.json" ]; then
  echo "Error: Upstream source not found at $VENDOR_DIR."
  echo "Run 'git submodule update --init vendor/codegraph' first."
  exit 1
fi

echo ">>> Building CodeGraph from source..."
mkdir -p "$DIST_DIR"
cd "$VENDOR_DIR"

echo ">>> Installing dependencies..."
npm ci || npm install

echo ">>> Building Rust kernel..."
if [ -d "codegraph-kernel" ]; then
  npm run build:kernel || (cd codegraph-kernel && cargo build --release)
fi

echo ">>> Compiling TypeScript..."
npm run build

echo ">>> Staging build output to dist/..."
rm -rf "${DIST_DIR:?}"/*
cp -r dist/* "$DIST_DIR/"
cp package.json "$DIST_DIR/"
if [ -d "node_modules" ]; then
  cp -r node_modules "$DIST_DIR/"
fi

chmod +x "$DIST_DIR/bin/codegraph.js" 2>/dev/null || true
echo ">>> Done! CodeGraph built into $DIST_DIR/bin/codegraph.js"
