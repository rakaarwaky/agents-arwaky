#!/usr/bin/env bash
# XDG Base Directory Specification helper for Linux
# Adheres strictly to freedesktop.org XDG standards
# Every vendor tool has its own dedicated top-level namespace:
#   $XDG_DATA_HOME/<tool>/
#   $XDG_CONFIG_HOME/<tool>/
#   $XDG_CACHE_HOME/<tool>/
#   $XDG_BIN_HOME/<tool-bin>

export XDG_DATA_HOME="${XDG_DATA_HOME:-$HOME/.local/share}"
export XDG_CONFIG_HOME="${XDG_CONFIG_HOME:-$HOME/.config}"
export XDG_CACHE_HOME="${XDG_CACHE_HOME:-$HOME/.cache}"
export XDG_BIN_HOME="${XDG_BIN_HOME:-$HOME/.local/bin}"
export PATH="${XDG_DATA_HOME:-$HOME/.local/share}/agents-arwaky/internal-bin:${XDG_BIN_HOME:-$HOME/.local/bin}:$PATH"


# Helper function to resolve paths for a specific vendor tool
xdg_data_dir() {
  local tool="$1"
  local dir="$XDG_DATA_HOME/$tool"
  mkdir -p "$dir"
  echo "$dir"
}

xdg_config_dir() {
  local tool="$1"
  local dir="$XDG_CONFIG_HOME/$tool"
  mkdir -p "$dir"
  echo "$dir"
}

xdg_cache_dir() {
  local tool="$1"
  local dir="$XDG_CACHE_HOME/$tool"
  mkdir -p "$dir"
  echo "$dir"
}

mkdir -p "$XDG_BIN_HOME"
