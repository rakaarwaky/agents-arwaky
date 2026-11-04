"""Skills-design CLI entry (AES root layer).

The single entry point for ``aa skills`` design-side verbs: parses argv,
builds a ``SkillsContainer``, injects the aggregate into the surface, and
returns the process exit code. This is the only module that knows both
the root and surface packages exist and composes them at the call site.

Dispatch table:
  - skills <list|read|lint|catalog|discover|move|archive|create> [flags]
"""

from __future__ import annotations

import sys

from cli.src.surface_skills_command import cmd_skills
from skills_design.src.root_skills_container import default_aggregate


def main(argv: list[str] | None = None) -> int:
    """Entry point for ``aa skills <verb> [flags]``."""
    args = argv if argv is not None else sys.argv[1:]
    if not args:
        print("Usage: aa skills <list|read|lint|catalog|discover|move|archive|create> [flags]", file=sys.stderr)
        return 2
    aggregate = default_aggregate()
    return cmd_skills(args, aggregate)


if __name__ == "__main__":
    raise SystemExit(main())
