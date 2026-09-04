#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
TOOLS_DIR="$REPO_ROOT/tools"

echo "=========================================="
echo " Building agents-arwaky tools"
echo "=========================================="

FAILED_BUILDS=()
SUCCESS_BUILDS=()

build_tool() {
  local name="$1"
  local script="$2"
  echo "------------------------------------------"
  echo "Building: $name"
  echo "------------------------------------------"
  if [ -x "$script" ]; then
    if "$script"; then
      SUCCESS_BUILDS+=("$name")
    else
      echo "Failed to build $name" >&2
      FAILED_BUILDS+=("$name")
    fi
  else
    echo "Executable script not found: $script" >&2
    FAILED_BUILDS+=("$name")
  fi
}

# Submodule checkout check
echo "Ensuring submodules are initialized..."
git -C "$REPO_ROOT" submodule update --init vendor/

build_tool "context7"    "$TOOLS_DIR/context7/install.sh"
build_tool "fetch-mcp"   "$TOOLS_DIR/fetch-mcp/install.sh"
build_tool "lean-ctx"    "$TOOLS_DIR/lean-ctx/install.sh"
build_tool "ponytail"    "$TOOLS_DIR/ponytail/install.sh"
build_tool "graphify"    "$TOOLS_DIR/graphify/install.sh"
build_tool "anytype-mcp" "$TOOLS_DIR/anytype-mcp/install.sh"
build_tool "codegraph"   "$TOOLS_DIR/codegraph/install.sh"
build_tool "9router"     "$TOOLS_DIR/9router/install.sh"

echo "=========================================="
echo " Build Summary"
echo "=========================================="
echo "Success: ${#SUCCESS_BUILDS[@]} [${SUCCESS_BUILDS[*]}]"
if [ ${#FAILED_BUILDS[@]} -gt 0 ]; then
  echo "Failed:  ${#FAILED_BUILDS[@]} [${FAILED_BUILDS[*]}]" >&2
  exit 1
else
  echo "All tools built successfully!"
fi
