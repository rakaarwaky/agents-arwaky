#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

echo "=========================================="
echo " Running agents-arwaky Verification"
echo "=========================================="

ERRORS=0

echo "[1/4] Checking executable permissions on scripts..."
while IFS= read -r -d '' script; do
  if [ ! -x "$script" ]; then
    echo "  [FAIL] Script not executable: $script"
    ERRORS=$((ERRORS + 1))
  fi
done < <(find "$REPO_ROOT/tools" -name "*.sh" -print0)
echo "  Permissions check completed."

echo "[2/4] Validating JSON configuration templates..."
while IFS= read -r -d '' json_file; do
  if ! jq empty "$json_file" 2>/dev/null; then
    echo "  [FAIL] Invalid JSON syntax: $json_file"
    ERRORS=$((ERRORS + 1))
  else
    echo "  [OK] $json_file"
  fi
done < <(find "$REPO_ROOT/tools" -name "*.json" -print0)

echo "[3/4] ShellCheck linting..."
if command -v shellcheck >/dev/null 2>&1; then
  while IFS= read -r -d '' script; do
    if ! shellcheck "$script"; then
      echo "  [FAIL] Shellcheck error in: $script"
      ERRORS=$((ERRORS + 1))
    fi
  done < <(find "$REPO_ROOT/tools" -name "*.sh" -print0)
  echo "  Shellcheck completed."
else
  echo "  [SKIP] Shellcheck not installed."
fi

echo "[4/4] Verifying submodules configuration..."
if [ -f "$REPO_ROOT/.gitmodules" ]; then
  git -C "$REPO_ROOT" submodule status
  echo "  Submodules check completed."
else
  echo "  [FAIL] Missing .gitmodules"
  ERRORS=$((ERRORS + 1))
fi

echo "=========================================="
if [ "$ERRORS" -gt 0 ]; then
  echo " Verification FAILED with $ERRORS errors."
  exit 1
else
  echo " All verifications PASSED successfully!"
fi
