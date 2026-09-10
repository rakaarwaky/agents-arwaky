#!/usr/bin/env python3
"""agents-arwaky Harness Connector / Disconnector — surface command (P4-A2).

Thin dispatch layer: parses CLI args, resolves harness targets through the
adapter registry, and delegates to per-harness capability modules.

Supports:
    aa disconnect --antigravity|--hermes|--opencode|--qwencode|--all
    aa disconnect <targets> --dry-run

Removes agents-arwaky MCP servers, provisioned skills and env vars from
agent harness paths (NOT the current working directory's .agents/skills —
that is `aa unskill` / skill-manager).
"""
from __future__ import annotations

import os
import re
import shutil
import sys
from pathlib import Path

from antigravity_adapter import (
    register as _register_antigravity,  # type: ignore[import-not-found]
)
from xdg import data_home  # type: ignore[import-not-found]

from connect_shared import (  # type: ignore[import-not-found]
    HOME,
    hermes_home,
    log_err,
    log_header,
    log_ok,
    log_sub,
    log_warn,
    remove_mcp_servers,
)
from hermes_adapter import (
    register as _register_hermes,  # type: ignore[import-not-found]
)
from opencode_adapter import (
    register as _register_opencode,  # type: ignore[import-not-found]
)
from qwencode_adapter import (
    register as _register_qwencode,  # type: ignore[import-not-found]
)

# --- harness registry (P4-A21: adapters register themselves) -----------------
HARNESSES: dict[str, dict] = {}
ALIASES: dict[str, str] = {}
for _mod in (_register_antigravity, _register_hermes, _register_opencode, _register_qwencode):
    _entry = _mod()
    HARNESSES[_entry["id"]] = _entry
    for _alias in _entry["aliases"]:
        ALIASES[_alias] = _entry["id"]
ALL_HARNESS_IDS = tuple(HARNESSES.keys())


def _parse_targets(args):
    """Parse CLI args into (harness_id_list, unknown_or_None).

    Recognizes: --all, --<harness_id>, --<alias>, or bare harness names.
    Returns ("help", None) if --help is in args.
    """
    if "help" in args or "--help" in args:
        return [], "help"
    targets = []
    unknown = None
    for a in args:
        if a in ("--all", "all"):
            targets.extend(ALL_HARNESS_IDS)
        elif a.startswith("--"):
            name = a[2:]
            if name in HARNESSES:
                targets.append(name)
            elif name in ALIASES:
                targets.append(ALIASES[name])
            else:
                unknown = a
                break
        elif a in HARNESSES:
            targets.append(a)
        elif a in ALIASES:
            targets.append(ALIASES[a])
        else:
            unknown = a
            break
    return targets, unknown


def cmd_disconnect(args):
    dry_run = False
    clean_args = []
    for a in args:
        if a == "--dry-run":
            dry_run = True
        else:
            clean_args.append(a)

    targets, unknown = _parse_targets(clean_args)
    if unknown == "help":
        print(__doc__)
        return 0
    if unknown is not None:
        log_err(f"Unknown target or option: {unknown}")
        return 1
    if not targets:
        log_err("No target agent harness specified.")
        print(__doc__)
        return 1

    seen = set()
    targets = [t for t in targets if not (t in seen or seen.add(t))]

    print("Disconnecting agents-arwaky from agent harnesses...")
    print("------------------------------------------------------------------")
    for t in targets:
        HARNESSES[t]["disconnect"](dry_run)
        print()
    print("------------------------------------------------------------------")
    print("\u2713 Disconnect complete. agents-arwaky entries removed from selected harnesses.")
    return 0


def cmd_connect(args):
    force = dry_run = mcp_only = skills_only = env_only = False
    clean_args = []
    for a in args:
        if a == "--force" or a == "-f":
            force = True
        elif a == "--dry-run":
            dry_run = True
        elif a == "--mcp-only":
            mcp_only = True
        elif a == "--skills-only":
            skills_only = True
        elif a == "--env-only":
            env_only = True
        else:
            clean_args.append(a)

    targets, unknown = _parse_targets(clean_args)
    if unknown == "help":
        print(__doc__)
        return 0
    if unknown is not None:
        log_err(f"Unknown target or option: {unknown}")
        return 1
    if not targets:
        log_err("No target agent harness specified.")
        print(__doc__)
        return 1

    seen = set()
    targets = [t for t in targets if not (t in seen or seen.add(t))]
    print("Connecting agents-arwaky to agent harnesses...")
    print("------------------------------------------------------------------")
    for t in targets:
        HARNESSES[t]["connect"](force, dry_run, mcp_only, skills_only, env_only)
        print()
    print("------------------------------------------------------------------")
    print("\u2713 Connection complete. Agent harnesses are now synchronized with agents-arwaky.")
    return 0


def main(argv):
    if len(argv) < 2 or argv[1] in ("-h", "--help", "help"):
        print(__doc__)
        return 0
    # Accept both "aa connect/disconnect ..." style and direct calls
    args = argv[1:]
    if args and args[0] in ("disconnect", "unconnect"):
        return cmd_disconnect(args[1:])
    if args and args[0] == "connect":
        return cmd_connect(args[1:])
    if args and args[0] in ALIASES or (args and args[0] in ("--all", "all")):
        # default action: connect (for backward compat with connect-agent.sh calls)
        return cmd_connect(args)
    return cmd_disconnect(args)


if __name__ == "__main__":
    sys.exit(main(sys.argv))
