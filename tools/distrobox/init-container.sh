#!/usr/bin/env bash
# tools/distrobox/init-container.sh
# Automated container initialization script invoked by Distrobox assemble
set -euo pipefail

echo ">>> Initializing agents-arwaky Distrobox environment..."

# 1. Ensure ~/.local/bin is in PATH
mkdir -p "$HOME/.local/bin"
export PATH="$HOME/.local/bin:$PATH"

# 2. Install uv if not present
if ! command -v uv >/dev/null 2>&1; then
  echo ">>> Installing uv..."
  curl -LsSf https://astral.sh/uv/install.sh | env CARGO_DIST_FORCE_INSTALL_DIR="$HOME/.local/bin" sh
fi

# 3. Install Bun if not present
if ! command -v bun >/dev/null 2>&1; then
  echo ">>> Installing Bun..."
  curl -fsSL https://bun.sh/install | bash
  if [ -f "$HOME/.bun/bin/bun" ]; then
    ln -sf "$HOME/.bun/bin/bun" "$HOME/.local/bin/bun"
    ln -sf "$HOME/.bun/bin/bunx" "$HOME/.local/bin/bunx"
  fi
fi

# 4. Install pnpm if not present
if ! command -v pnpm >/dev/null 2>&1; then
  echo ">>> Installing pnpm..."
  curl -fsSL https://get.pnpm.io/install.sh | env PNPM_HOME="$HOME/.local/bin" SHELL=bash sh -
fi

echo ">>> Distrobox environment ready!"
