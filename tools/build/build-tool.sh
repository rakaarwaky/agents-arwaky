#!/usr/bin/env bash
# tools/build/build-tool.sh
# Universal single-tool installer dispatcher (used by both Distrobox and Host modes)
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
MANIFEST_FILE="$REPO_ROOT/tools/arwaky/manifest.json"

# shellcheck source=/dev/null
source "$REPO_ROOT/tools/lib/xdg.sh"

if [ $# -lt 1 ]; then
  echo "Error: Tool name required." >&2
  echo "Usage: $0 <tool-name>" >&2
  exit 1
fi

TOOL_INPUT="$1"

# Lookup tool in manifest by id, binary, or alias
TOOL_INFO="$(jq -c --arg q "$TOOL_INPUT" '.tools[] | select(.id == $q or .binary == $q or (.alias? != null and .alias == $q))' "$MANIFEST_FILE" 2>/dev/null | head -n1 || true)"

if [ -z "$TOOL_INFO" ]; then
  echo "Error: Tool '$TOOL_INPUT' not found in manifest." >&2
  echo "Available tools: $(jq -r '.tools[].id' "$MANIFEST_FILE" | tr '\n' ' ')" >&2
  exit 1
fi

TOOL_ID="$(echo "$TOOL_INFO" | jq -r '.id')"
TOOL_CATEGORY="$(echo "$TOOL_INFO" | jq -r '.category')"
TOOL_PATH="$(echo "$TOOL_INFO" | jq -r '.path')"

echo "=========================================="
echo " Building $TOOL_ID ($TOOL_CATEGORY)"
echo "=========================================="

# Ensure submodule is initialized if path is a submodule
if [ -d "$REPO_ROOT/$TOOL_PATH" ] || [ -f "$REPO_ROOT/.gitmodules" ]; then
  if grep -q "path = $TOOL_PATH" "$REPO_ROOT/.gitmodules" 2>/dev/null; then
    echo ">>> Initializing submodule: $TOOL_PATH..."
    git -C "$REPO_ROOT" submodule update --init "$TOOL_PATH"
  fi
fi

# Dispatch to tool-specific installer
if [ "$TOOL_ID" = "anytype-daemon" ]; then
  "$REPO_ROOT/tools/anytype-mcp/daemon/anytype-daemon.sh" status || true
elif [ -x "$REPO_ROOT/tools/$TOOL_ID/install.sh" ]; then
  "$REPO_ROOT/tools/$TOOL_ID/install.sh"
elif [ -x "$REPO_ROOT/tools/${TOOL_ID}-mcp/install.sh" ]; then
  "$REPO_ROOT/tools/${TOOL_ID}-mcp/install.sh"
else
  echo "Error: No installer found for tool '$TOOL_ID'." >&2
  exit 1
fi

echo ">>> Successfully built $TOOL_ID!"
