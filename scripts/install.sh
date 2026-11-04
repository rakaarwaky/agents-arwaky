#!/usr/bin/env bash
# scripts/install.sh
#
# Install the aa (agent-arwaky) standalone CLI binary to the XDG bin home
# ($XDG_BIN_HOME, default $HOME/.local/bin). aa only — no sdc, no stc,
# no other binary.
#
# No bin/ directory is kept in the project; this installer is the single
# source of the aa binary and carries it inline.
#
# XDG Base Directory spec (v0.8) compliance:
#   - XDG_BIN_HOME must be absolute; relative/tilde values are rejected.
#   - Directories the installer creates are 0700.
#   - Installed binary is 0755.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
MODULES_DIR="$REPO_ROOT/modules"

BIN_DIR="${XDG_BIN_HOME:-$HOME/.local/bin}"

case "$BIN_DIR" in
  /*) ;;
  *)
    echo "install.sh: XDG_BIN_HOME must be an absolute path, got: $BIN_DIR" >&2
    exit 1
    ;;
esac
case "$BIN_DIR" in
  ~*)
    echo "install.sh: XDG_BIN_HOME must not begin with tilde, got: $BIN_DIR" >&2
    exit 1
    ;;
esac

# Remove any pre-existing file/symlink at $BIN_DIR/aa so we never write
# through a stale symlink to another location.
if [[ -e "$BIN_DIR/aa" || -L "$BIN_DIR/aa" ]]; then
  rm -f "$BIN_DIR/aa"
fi

if [[ ! -d "$BIN_DIR" ]]; then
  mkdir -p "$BIN_DIR"
  chmod 700 "$BIN_DIR"
fi

cat > "$BIN_DIR/aa" <<'AA_EOF'
#!/usr/bin/env python3
"""aa — agent-arwaky CLI (standalone binary).

Entry point for ``aa`` (agent-arwaky): the standalone AES package that
bootstraps the top-level ``modules`` namespace root plus the two
independent skills packages (skills-design and skills-traces). No shared
dependency between aa and sdc/stc; each package boots its own namespace.

The modules tree is located via the ``AA_MODULES_DIR`` environment
variable, which must be an absolute path (XDG Base Directory rule:
relative/tilde values are rejected). Falls back to walking up from the
binary to find the repository's modules tree.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

_MODULES_ENV = "AA_MODULES_ENV"
_DEFAULT_MODULES = Path("modules")


def _resolve_modules_dir() -> Path:
    raw = os.environ.get("AA_MODULES_DIR")
    if raw:
        value = raw.strip()
        if value:
            p = Path(value)
            if not p.is_absolute() or str(value).startswith("~"):
                print(
                    f"aa: warning: AA_MODULES_DIR={value!r} ignored (not absolute)",
                    file=sys.stderr,
                )
            else:
                return p
    # Fallback: walk up from this binary to find the repo modules tree.
    here = Path(__file__).resolve()
    for candidate in (here.parent, *here.parents):
        mod = candidate / _DEFAULT_MODULES
        if mod.is_dir():
            return mod
    return here.parent / _DEFAULT_MODULES


_MODULES = _resolve_modules_dir()
if str(_MODULES) not in sys.path:
    sys.path.insert(0, str(_MODULES))

# root_cli_entry imports ``modules.shared...`` so the REPO_ROOT (parent of
# modules/) must be on sys.path, not modules/ itself.
if str(_MODULES.parent) not in sys.path:
    sys.path.insert(0, str(_MODULES.parent))

# Add the two independent skills package roots so the ``skills`` command
# can import skills_design / skills_traces on demand.
for _skills_ns in (
    Path("skills") / "skill-authoring" / "skill-design" / "modules",
    Path("skills") / "skill-authoring" / "skill-traces" / "modules",
):
    _here = Path(__file__).resolve()
    for _candidate in (_here.parent, *_here.parents):
        _ns = _candidate / _skills_ns
        if _ns.is_dir() and str(_ns) not in sys.path:
            sys.path.insert(0, str(_ns))
            break

from modules.root_cli_entry import main  # noqa: E402

if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
AA_EOF
chmod 755 "$BIN_DIR/aa"

echo "Installed aa to $BIN_DIR"
echo "Add $BIN_DIR to your PATH if it is not already."
echo "Then run (with AA_MODULES_DIR pointed at the repo modules tree):"
echo "  export AA_MODULES_DIR=$MODULES_DIR"
echo "  aa status   aa skills list   aa tool list"
