#!/usr/bin/env bash
# tools/arwaky/arwaky-cli.sh
# Wrapper tipis: semua logika sudah dipindah ke Python (tools/arwaky/arwaky.py).
# Dipertahankan untuk kompatibilitas & sebagai satu-satunya bash CLI entrypoint.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && cd ../.. && pwd)"

export AGENTS_ARWAKY_ROOT="$ROOT"
export PYTHONPATH="$ROOT/tools/lib${PYTHONPATH:+:${PYTHONPATH}}"

exec python3 "$ROOT/tools/arwaky/arwaky.py" "$@"
