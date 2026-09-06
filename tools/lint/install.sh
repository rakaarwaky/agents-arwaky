#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
# shellcheck source=/dev/null
source "$REPO_ROOT/tools/lib/xdg.sh"

INTERNAL_DIR="$REPO_ROOT/internal/lint-arwaky"
TARGET_BIN="${XDG_BIN_HOME:-$HOME/.local/bin}"
CONFIG_DIR="${XDG_CONFIG_HOME:-$HOME/.config}/lint-arwaky"
REPORT_DIR="${XDG_DATA_HOME:-$HOME/.local/share}/lint-arwaky/reports"

if [ ! -d "$INTERNAL_DIR" ] || [ ! -f "$INTERNAL_DIR/Cargo.toml" ]; then
  echo ">>> Initializing submodule internal/lint-arwaky..."
  git -C "$REPO_ROOT" submodule update --init internal/lint-arwaky
fi

if ! command -v cargo >/dev/null 2>&1; then
  echo "Error: cargo is required to build lint-arwaky." >&2
  echo "Please run inside Distrobox (aa install lint) or install Rust on your host." >&2
  exit 1
fi

echo ">>> Building lint-arwaky (AES Architecture Linter) into $TARGET_BIN..."
mkdir -p "$TARGET_BIN" "$CONFIG_DIR/rules" "$REPORT_DIR"

(
  cd "$INTERNAL_DIR"
  RUST_MIN_STACK=33554432 cargo build --release
)

RELEASE_DIR="$INTERNAL_DIR/target/release"
BINARIES=(lint-arwaky la lint-arwaky-cli lint-arwaky-mcp lint-arwaky-tui)

for BIN in "${BINARIES[@]}"; do
  if [ -f "$RELEASE_DIR/$BIN" ]; then
    install -m 0755 "$RELEASE_DIR/$BIN" "$TARGET_BIN/$BIN"
    echo "  -> $TARGET_BIN/$BIN"
  fi
done

# Ensure lac symlink exists
if [ -f "$TARGET_BIN/lint-arwaky-cli" ]; then
  ln -sf "$TARGET_BIN/lint-arwaky-cli" "$TARGET_BIN/lac"
fi

# Copy docs & .agents config to XDG config
if [ -d "$INTERNAL_DIR/.agents" ]; then
  mkdir -p "$CONFIG_DIR/.agents/skills" "$CONFIG_DIR/.agents/rules" "$CONFIG_DIR/.agents/prompts"
  cp -r "$INTERNAL_DIR/.agents"/* "$CONFIG_DIR/.agents/" 2>/dev/null || true
fi

for DOC in "ARCHITECTURE.md" "MIGRATION_RUST.md" "MIGRATION_PYTHON.md" "MIGRATION_TYPESCRIPT.md"; do
  if [ -f "$INTERNAL_DIR/$DOC" ]; then
    cp "$INTERNAL_DIR/$DOC" "$CONFIG_DIR/$DOC"
  fi
done

if [ -f "$INTERNAL_DIR/.agents/rules/RULES_AES.md" ]; then
  cp "$INTERNAL_DIR/.agents/rules/RULES_AES.md" "$CONFIG_DIR/RULES_AES.md"
fi

echo ">>> Successfully installed lint-arwaky -> $TARGET_BIN"
