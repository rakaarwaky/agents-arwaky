#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
VENDOR_DIR="$REPO_ROOT/vendor/graphify"

if [ ! -d "$VENDOR_DIR" ]; then
  echo "Error: Upstream source not found at $VENDOR_DIR."
  echo "Run 'git submodule update --init --recursive vendor/graphify' first."
  exit 1
fi

echo ">>> Graphify source ready at $VENDOR_DIR"
if [ -f "$VENDOR_DIR/package.json" ]; then
  echo ">>> Installing npm dependencies in vendor/graphify..."
  cd "$VENDOR_DIR"
  npm install
elif [ -f "$VENDOR_DIR/pyproject.toml" ] || [ -f "$VENDOR_DIR/setup.py" ]; then
  echo ">>> Python project detected at $VENDOR_DIR"
fi

echo ">>> Graphify build check complete."
