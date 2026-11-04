#!/usr/bin/env bash
# skills/skill-authoring/skill-traces/scripts/install.sh
#
# Install the stc (skill-traces-cli) standalone binary to the XDG bin home
# ($XDG_BIN_HOME, default $HOME/.local/bin). stc only — no sdc, no other
# binary.
#
# No bin/ directory is kept in the project; this installer is the source
# of the stc binary and carries it inline.
#
# XDG Base Directory spec (v0.8):
#   - XDG_BIN_HOME must be absolute; relative/tilde values are rejected.
#   - Directories the installer creates are 0700.
#   - Installed binary is 0755.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PACKAGE_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
MODULES_DIR="$PACKAGE_ROOT/modules"

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

# Remove any pre-existing file/symlink at $BIN_DIR/stc so we never write
# through a stale symlink to another location.
if [[ -e "$BIN_DIR/stc" || -L "$BIN_DIR/stc" ]]; then
  rm -f "$BIN_DIR/stc"
fi

if [[ ! -d "$BIN_DIR" ]]; then
  mkdir -p "$BIN_DIR"
  chmod 700 "$BIN_DIR"
fi

cat > "$BIN_DIR/stc" <<'STC_EOF'
#!/usr/bin/env python3
"""stc — skills-traces CLI (standalone binary)."""
from __future__ import annotations

import os
import sys
from pathlib import Path

_DEFAULT_MODULES = Path("skills") / "skill-authoring" / "skill-traces" / "modules"


def _resolve_modules_dir() -> Path:
    raw = os.environ.get("STC_MODULES_DIR")
    if raw:
        value = raw.strip()
        if value:
            p = Path(value)
            if not p.is_absolute() or str(value).startswith("~"):
                print(
                    f"stc: warning: STC_MODULES_DIR={value!r} ignored (not absolute)",
                    file=sys.stderr,
                )
            else:
                return p
    here = Path(__file__).resolve()
    for candidate in (here.parent, *here.parents):
        mod = candidate / _DEFAULT_MODULES
        if mod.is_dir():
            return mod
    return here.parent / _DEFAULT_MODULES


_MODULES = _resolve_modules_dir()
if str(_MODULES) not in sys.path:
    sys.path.insert(0, str(_MODULES))

from cli.src.surface_skills_traces_command import cmd_traces  # noqa: E402
from root_skills_container import default_container  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    args = argv if argv is not None else sys.argv[1:]
    if not args or args[0] != "traces":
        print(
            "Usage: stc traces <collect|usage|phrases|materialize|state> [flags]",
            file=sys.stderr,
        )
        return 2
    sub = args[1:]
    container = default_container()
    aggregate = container.aggregate
    return cmd_traces(sub, aggregate)


if __name__ == "__main__":
    raise SystemExit(main())
STC_EOF
chmod 755 "$BIN_DIR/stc"

echo "Installed stc to $BIN_DIR"
echo "Add $BIN_DIR to your PATH if it is not already."
echo "Then run (with STC_MODULES_DIR pointed at the skill-traces modules tree):"
echo "  export STC_MODULES_DIR=$MODULES_DIR"
echo "  stc traces usage"
