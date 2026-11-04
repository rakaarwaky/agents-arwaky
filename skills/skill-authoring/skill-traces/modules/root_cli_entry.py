"""Skills traces CLI entry (AES root layer).

The single entry point for ``stc skills traces``: parses argv, builds a
``SkillsContainer``, injects the aggregate into the surface, and returns
the process exit code. This is the only module that knows both the root
and surface packages exist and composes them at the call site.

Dispatch table:
  - skills traces <collect|usage|phrases|materialize|state> [flags]
"""

from __future__ import annotations

import sys

from cli.src.surface_skills_traces_command import cmd_traces
from root_skills_container import default_container


def main(argv: list[str] | None = None) -> int:
    """Entry point for ``stc skills traces``."""
    args = argv if argv is not None else sys.argv[1:]
    if not args or args[0] != "traces":
        print("Usage: stc skills traces <collect|usage|phrases|materialize|state> [flags]", file=sys.stderr)
        return 2
    sub = args[1:]
    container = default_container()
    aggregate = container.aggregate
    return cmd_traces(sub, aggregate)

if __name__ == "__main__":
    raise SystemExit(main())
