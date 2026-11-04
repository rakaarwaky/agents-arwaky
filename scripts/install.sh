#!/usr/bin/env bash
# scripts/install.sh
#
# Install the standalone sdc (skill-design) and stc (skill-traces) CLI
# binaries to the XDG bin home ($XDG_BIN_HOME, default $HOME/.local/bin)
# so they live on PATH instead of inside the project directory.
#
# No bin/ directory is kept in the project; this installer is the single
# source of the binaries and carries them inline.
#
# XDG Base Directory spec (v0.8) compliance:
#   - XDG_BIN_HOME must be absolute; relative/tilde values are rejected.
#   - Directories the installer creates are 0700.
#   - Installed binaries are 0755.
#   - Pre-existing shared ancestors (e.g. ~/.local) are left untouched.
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

BIN_DIR="${XDG_BIN_HOME:-$HOME/.local/bin}"

# XDG rule: absolute only. Reject relative values and tilde paths that
# were never shell-expanded (Path("~/x").expanduser() would silently
# write $HOME/x).
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

if [[ ! -d "$BIN_DIR" ]]; then
  mkdir -p "$BIN_DIR"
  chmod 700 "$BIN_DIR"
fi

cat > "$BIN_DIR/sdc" <<'SDC_EOF'
#!/usr/bin/env python3
"""sdc — skills-design CLI (standalone binary).

Entry point for ``sdc`` (skill-design-cli): a fully standalone AES
7-layer package that bootstraps only its own namespace root
(``skills_design``/``cli``). No shared dependency, no coupling to the
skill-traces app.

The modules tree is located via the ``SDC_MODULES_DIR`` environment
variable, which must be an absolute path (XDG Base Directory rule:
relative/tilde values are rejected). Falls back to walking up from the
binary to find the repository's modules tree.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

_MODULES_ENV = "SDC_MODULES_DIR"
_DEFAULT_RELATIVE = Path("skills") / "skill-authoring" / "skill-design" / "modules"


def _resolve_modules_dir() -> Path:
    raw = os.environ.get(_MODULES_ENV)
    if raw:
        value = raw.strip()
        if value:
            p = Path(value)
            if not p.is_absolute():
                print(
                    f"sdc: warning: ${_MODULES_ENV}={value!r} is not absolute; ignoring",
                    file=sys.stderr,
                )
            elif str(value).startswith("~"):
                print(
                    f"sdc: warning: ${_MODULES_ENV}={value!r} is a tilde path; ignoring",
                    file=sys.stderr,
                )
            else:
                return p
    # Fallback: walk up from this binary to find the repo modules tree.
    here = Path(__file__).resolve()
    for candidate in (here.parent, *here.parents):
        mod = candidate / _DEFAULT_RELATIVE
        if mod.is_dir():
            return mod
    return here.parent / _DEFAULT_RELATIVE


_MODULES = _resolve_modules_dir()
if str(_MODULES) not in sys.path:
    sys.path.insert(0, str(_MODULES))

from cli.src.surface_skills_command import cmd_skills  # noqa: E402
from skills_design.src.root_skills_container import default_aggregate  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    """Entry point for ``sdc <verb> [flags]``."""
    args = argv if argv is not None else sys.argv[1:]
    if not args:
        print(
            "Usage: sdc <list|read|lint|catalog|discover|move|archive|create> [flags]",
            file=sys.stderr,
        )
        return 2
    aggregate = default_aggregate()
    return cmd_skills(args, aggregate)


if __name__ == "__main__":
    raise SystemExit(main())
SDC_EOF
chmod 755 "$BIN_DIR/sdc"

cat > "$BIN_DIR/stc" <<'STC_EOF'
#!/usr/bin/env python3
"""stc — skills-traces CLI (standalone binary).

Entry point for ``stc`` (skill-traces-cli): a fully standalone AES
7-layer package that bootstraps only its own namespace root
(``skills_traces``/``cli``). No shared dependency, no coupling to the
skill-design app.

The modules tree is located via the ``STC_MODULES_DIR`` environment
variable, which must be an absolute path (XDG Base Directory rule:
relative/tilde values are rejected). Falls back to walking up from the
binary to find the repository's modules tree.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

_MODULES_ENV = "STC_MODULES_DIR"
_DEFAULT_RELATIVE = Path("skills") / "skill-authoring" / "skill-traces" / "modules"


def _resolve_modules_dir() -> Path:
    raw = os.environ.get(_MODULES_ENV)
    if raw:
        value = raw.strip()
        if value:
            p = Path(value)
            if not p.is_absolute():
                print(
                    f"stc: warning: ${_MODULES_ENV}={value!r} is not absolute; ignoring",
                    file=sys.stderr,
                )
            elif str(value).startswith("~"):
                print(
                    f"stc: warning: ${_MODULES_ENV}={value!r} is a tilde path; ignoring",
                    file=sys.stderr,
                )
            else:
                return p
    # Fallback: walk up from this binary to find the repo modules tree.
    here = Path(__file__).resolve()
    for candidate in (here.parent, *here.parents):
        mod = candidate / _DEFAULT_RELATIVE
        if mod.is_dir():
            return mod
    return here.parent / _DEFAULT_RELATIVE


_MODULES = _resolve_modules_dir()
if str(_MODULES) not in sys.path:
    sys.path.insert(0, str(_MODULES))

from cli.src.surface_skills_traces_command import cmd_traces  # noqa: E402
from root_skills_container import default_container  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    """Entry point for ``stc traces <collect|usage|phrases|materialize|state> [flags]``."""
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

echo "Installed sdc and stc to $BIN_DIR"
echo "Add $BIN_DIR to your PATH if it is not already."
echo "Point each binary at its modules tree, e.g.:"
echo "  export SDC_MODULES_DIR=$REPO_ROOT/skills/skill-authoring/skill-design/modules"
echo "  export STC_MODULES_DIR=$REPO_ROOT/skills/skill-authoring/skill-traces/modules"
echo "Then run:  sdc list   stc traces usage"
