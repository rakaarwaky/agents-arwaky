#!/usr/bin/env bash
# Build anytype-mcp locally into dist/ using Bun.
set -euo pipefail
cd "$(dirname "$0")/../anytype-mcp"

if ! command -v bun >/dev/null 2>&1; then
  echo "bun not found. Install it first: https://bun.com  (or curl -fsSL https://bun.sh/install | bash)" >&2
  exit 1
fi

bun install --frozen-lockfile
bun run build

mkdir -p ../dist
cp -r dist/* ../dist/ 2>/dev/null || cp -r . ../dist/
echo "Built anytype-mcp -> $(dirname "$0")/../dist/"
echo "Run with: bun run $(dirname "$0")/../anytype-mcp/dist/index.js  (see anytype_local.json)"
