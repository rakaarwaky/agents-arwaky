#!/usr/bin/env bash
# Run the repository quality gates locally.

set -uo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

# Tests intentionally exercise the default launcher registry path. Remove only
# generated runtime state; never remove source or user configuration files.
cleanup_runtime_state() {
    rm -f "$ROOT_DIR/launcher_state.json" "$ROOT_DIR/registry.json"
}
trap cleanup_runtime_state EXIT

passed=0
failed=0

run_check() {
    local name="$1"
    shift
    printf '▸ %s\n' "$name"
    if "$@"; then
        printf '  ✓ passed\n\n'
        passed=$((passed + 1))
    else
        printf '  ✗ failed\n\n'
        failed=$((failed + 1))
    fi
}

run_check "Ruff lint (modules only)" uv run ruff check modules
run_check "Ruff format (modules only)" uv run ruff format --check modules
run_check "AES architecture full scan" bash scripts/run_lint_arwaky_architecture.sh
run_check "Python syntax" python -m compileall -q modules blender_mcp_addon
run_check "Bandit security (modules only)" uv run bandit -r modules -x '*/tests/*' -ll -ii
run_check "Tests" uv run pytest -q --tb=short
run_check "Addon package" bash -c 'uv run python scripts/build/build_addon_package.py && unzip -t dist/blender_mcp_addon.zip >/dev/null'
run_check "Python distributions" bash -c 'build_dir=$(mktemp -d) && trap "rm -rf \"$build_dir\"" EXIT && uv build --out-dir "$build_dir" >/dev/null && test -n "$(find "$build_dir" -maxdepth 1 -type f -print -quit)"'

printf '%s\n' '=== Summary ==='
printf 'Passed: %s\n' "$passed"
if [ "$failed" -gt 0 ]; then
    printf 'Failed: %s\n' "$failed"
    exit 1
fi
printf '%s\n' 'All checks passed!'
