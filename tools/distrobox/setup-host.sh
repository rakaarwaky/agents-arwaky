#!/usr/bin/env bash
# tools/distrobox/setup-host.sh
# Checks host prerequisites (Podman and Distrobox) and optionally installs them
set -euo pipefail

AUTO_INSTALL=false
if [ "${1:-}" = "--install" ] || [ "${1:-}" = "-y" ]; then
  AUTO_INSTALL=true
fi

echo "=========================================="
echo " Checking Host Container Prerequisites"
echo "=========================================="

MISSING=()

if ! command -v podman >/dev/null 2>&1 && ! command -v docker >/dev/null 2>&1; then
  MISSING+=("podman")
fi

if ! command -v distrobox >/dev/null 2>&1; then
  MISSING+=("distrobox")
fi

if [ ${#MISSING[@]} -eq 0 ]; then
  echo " [OK] Container runtime: $(command -v podman 2>/dev/null || command -v docker)"
  echo " [OK] Distrobox: $(command -v distrobox)"
  echo ""
  echo "Host environment is ready for Distrobox First-Class operation!"
  exit 0
fi

echo "The following required tools are missing on your host Linux system:"
for tool in "${MISSING[@]}"; do
  echo "  - $tool"
done
echo ""

if [ "$AUTO_INSTALL" = true ]; then
  echo ">>> Attempting automated installation via system package manager..."
  if command -v apt-get >/dev/null 2>&1; then
    echo "Running: sudo apt-get update && sudo apt-get install -y podman distrobox"
    sudo apt-get update && sudo apt-get install -y podman distrobox
  elif command -v pacman >/dev/null 2>&1; then
    echo "Running: sudo pacman -S --noconfirm podman distrobox"
    sudo pacman -S --noconfirm podman distrobox
  elif command -v dnf >/dev/null 2>&1; then
    echo "Running: sudo dnf install -y podman distrobox"
    sudo dnf install -y podman distrobox
  else
    echo "Unsupported package manager. Please install manually:" >&2
    exit 1
  fi
  echo ">>> Prerequisites successfully installed!"
  exit 0
fi

echo "To install missing prerequisites automatically, run:"
echo "  make setup"
echo "  (or: ./tools/distrobox/setup-host.sh --install)"
echo ""
echo "Or install manually for your Linux distribution:"
echo "---------------------------------------------------------"
if command -v apt-get >/dev/null 2>&1; then
  echo "Debian / Ubuntu / Deepin:"
  echo "  sudo apt update && sudo apt install -y podman distrobox"
elif command -v pacman >/dev/null 2>&1; then
  echo "Arch Linux:"
  echo "  sudo pacman -S podman distrobox"
elif command -v dnf >/dev/null 2>&1; then
  echo "Fedora:"
  echo "  sudo dnf install -y podman distrobox"
fi
echo ""
echo "Or install Distrobox standalone (rootless):"
echo "  curl -s https://raw.githubusercontent.com/89luca89/distrobox/main/install | sh -s -- --prefix ~/.local"
echo "---------------------------------------------------------"
exit 1
