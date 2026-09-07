#!/usr/bin/env bash
# Run the pinned full AES architecture scan locally and in CI.
set -euo pipefail
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"
LINT_ARWAKY_VERSION="${LINT_ARWAKY_VERSION:-v3.6.1}"
LINT_ARWAKY_SHA256="${LINT_ARWAKY_SHA256:-1dc8f3fe98cfb7b8cfaf7e42635fa94051277f95f096867794727d37b4788550}"
LINT_ARWAKY_BIN="${LINT_ARWAKY_BIN:-}"
if [[ -z "$LINT_ARWAKY_BIN" ]]; then
    temp_dir="$(mktemp -d)"
    trap 'rm -rf "$temp_dir"' EXIT
    LINT_ARWAKY_BIN="$temp_dir/lint-arwaky-cli"
    curl --fail --silent --show-error --location \
        "https://github.com/rakaarwaky/lint-arwaky/releases/download/${LINT_ARWAKY_VERSION}/lint-arwaky-cli" \
        --output "$LINT_ARWAKY_BIN"
    printf '%s  %s\n' "$LINT_ARWAKY_SHA256" "$LINT_ARWAKY_BIN" | sha256sum --check --status
    chmod +x "$LINT_ARWAKY_BIN"
fi
"$LINT_ARWAKY_BIN" version
"$LINT_ARWAKY_BIN" scan .
