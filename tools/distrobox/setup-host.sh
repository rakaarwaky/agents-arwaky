#!/usr/bin/env bash
# tools/distrobox/setup-host.sh
# Checks host prerequisites (Podman and Distrobox) and helps install if missing
set -euo pipefail

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
  echo "Host environment is ready to use Distrobox!"
  echo "Run 'make distrobox-create' to initialize the environment."
  exit 0
fi

echo "The following required tools are missing on your host Linux system:"
for tool in "${MISSING[@]}"; do
  echo "  - $tool"
done
echo ""
echo "Installation commands for Linux:"
echo "---------------------------------------------------------"
if command -v apt >/dev/null 2>&1; then
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
exit 0
