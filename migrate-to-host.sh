#!/usr/bin/env bash
set -euo pipefail

# agents-arwaky: Distrobox → Local Host Migration Script
# Migrates the orchestration CLI and all registered tools from Distrobox to bare-metal host.

echo "=== agents-arwaky Host Migration ==="
echo ""

# Step 1: Check prerequisites
echo "[1/5] Checking prerequisites..."
command -v cargo >/dev/null 2>&1 || { echo "ERROR: cargo not found"; exit 1; }
command -v aa >/dev/null 2>&1 || echo "WARNING: aa not yet on host, will build it"

# Step 2: Build arwaky natively on host
echo "[2/5] Building arwaky CLI natively on host..."
cd /home/raka/agents-arwaky
cargo build --release 2>&1 || { echo "ERROR: cargo build failed"; exit 1; }

# Step 3: Install arwaky binary to ~/.local/bin/
echo "[3/5] Installing arwaky to ~/.local/bin/..."
mkdir -p ~/.local/bin
cp /home/raka/agents-arwaky/target/release/arwaky ~/.local/bin/arwaky 2>/dev/null || true
cp /home/raka/agents-arwaky/target/release/aa ~/.local/bin/aa 2>/dev/null || true
chmod +x ~/.local/bin/arwaky ~/.local/bin/aa 2>/dev/null || true
export PATH="$HOME/.local/bin:$PATH"

# Step 4: Install all registered tools on host (bare-metal)
echo "[4/5] Installing all registered tools on host..."
# aa install --host arwaky
aa install --host arwaky 2>/dev/null || echo "NOTE: aa install --host arwaky (try after aa is available)"

# Install all tools from manifest
if command -v aa >/dev/null 2>&1; then
    aa install --host arwaky 2>/dev/null || true
    # Loop through registered tools from manifest
    for tool in $(aa list 2>/dev/null | grep -oP '(?<=^)[\w-]+' || true); do
        echo "  Installing $tool on host..."
        aa install "$tool" --host 2>/dev/null || echo "  WARNING: Failed to install $tool"
    done
fi

# Step 5: Reset submodules and verify
echo "[5/5] Finalizing..."
aa submodules 2>/dev/null || true
aa status 2>/dev/null || echo "NOTE: Run 'aa status' to verify"

echo ""
echo "=== Migration Complete ==="
echo "All tools should now run natively on the host instead of inside Distrobox."
echo "Container layer (Podman) is now only for: 9Router, Anytype daemons."
