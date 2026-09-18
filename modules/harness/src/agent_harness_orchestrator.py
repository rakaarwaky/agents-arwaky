"""Harness agent orchestrator — routes connect/disconnect to per-harness connectors.

Port of tools/connect/connect.py: the harness registry (P4-A21: adapters
register themselves), target parsing, the two verbs, and standalone main()
live here, on top of the per-harness connector classes (IHarnessConnector).
"""
from __future__ import annotations

from modules.harness.src.root_harness_connectors import (
    ALIASES,
    ALL_HARNESS_IDS,
    HARNESSES,
)
from modules.harness.src.contract_harness_aggregate import IHarnessAggregate
from modules.harness.src.contract_harness_protocol import IHarnessConnector


def log_err(msg: str) -> None:
    """Emit a diagnostic line to stderr without importing the shared helper."""
    print(msg, file=__import__("sys").stderr)


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

_HELP_DOC = """agents-arwaky Harness Connector / Disconnector \u2014 surface command.

aa disconnect --antigravity|--hermes|--opencode|--qwencode|--grok-build|--all
aa disconnect <targets> --dry-run

Skill provisioning links each skill directory to the repo pack under
``skills/`` by default, so edits made through a harness land in the repo and
every agent shares them; ``aa connect --copy-skills`` restores snapshots.

Removes agents-arwaky MCP servers, provisioned skills and env vars from
agent harness paths (NOT the current working directory's .agents/skills \u2014
that is `aa unskill` / skill-manager).
"""

# --- verb dispatch (port of connect.py) ---------------------------------------
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
        print(_HELP_DOC)
        return 0
    if unknown is not None:
        log_err(f"Unknown target or option: {unknown}")
        return 1
    if not targets:
        log_err("No target agent harness specified.")
        print(_HELP_DOC)
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
    force = dry_run = mcp_only = skills_only = env_only = copy_skills = False
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
        elif a == "--copy-skills":
            copy_skills = True
        else:
            clean_args.append(a)

    targets, unknown = _parse_targets(clean_args)
    if unknown == "help":
        print(_HELP_DOC)
        return 0
    if unknown is not None:
        log_err(f"Unknown target or option: {unknown}")
        return 1
    if not targets:
        log_err("No target agent harness specified.")
        print(_HELP_DOC)
        return 1

    seen = set()
    targets = [t for t in targets if not (t in seen or seen.add(t))]
    print("Connecting agents-arwaky to agent harnesses...")
    print("------------------------------------------------------------------")
    for t in targets:
        HARNESSES[t]["connect"](force, dry_run, mcp_only, skills_only, env_only, copy_skills)
        print()
    print("------------------------------------------------------------------")
    print("\u2713 Connection complete. Agent harnesses are now synchronized with agents-arwaky.")
    return 0


def main(argv):
    if len(argv) < 2 or argv[1] in ("-h", "--help", "help"):
        print(_HELP_DOC)
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


class HarnessOrchestrator(IHarnessAggregate):
    """Registry of connectors, routed by target harness id/alias.

    # Block 1: Constructor (connector registry)
    # Block 2: Target resolution
    # Block 3: Aggregate verb delegation
    """

    # -- Block 1: Constructor ---------------------------------------------------
    def __init__(self, connectors: dict[str, IHarnessConnector]) -> None:
        self._connectors = connectors
        self._aliases: dict[str, str] = {}
        for harness_id in HARNESSES:
            for alias in HARNESSES[harness_id]["aliases"]:
                self._aliases[alias.lstrip("-")] = harness_id

    # -- Block 2: Target resolution -------------------------------------------------
    def resolve_targets(self, targets: tuple[str, ...]) -> tuple[str, ...]:
        """Map raw CLI targets (id/alias) onto canonical ids, deduped, drop unknown."""
        out: list[str] = []
        seen: set[str] = set()
        for target in targets:
            tid = self._aliases.get(target.lstrip("-"), target)
            if tid not in self._connectors or tid in seen:
                continue
            seen.add(tid)
            out.append(tid)
        return tuple(out)

    def all_targets(self) -> tuple[str, ...]:
        return tuple(self._connectors)

    # -- Block 3: Aggregate verb delegation ------------------------------------------
    def connect(self, targets, force: bool = False, dry_run: bool = False, mcp_only: bool = False,
                skills_only: bool = False, env_only: bool = False, copy_skills: bool = False) -> int:
        args = [str(t) for t in targets]
        if force:
            args.append("--force")
        if dry_run:
            args.append("--dry-run")
        if mcp_only:
            args.append("--mcp-only")
        if skills_only:
            args.append("--skills-only")
        if env_only:
            args.append("--env-only")
        if copy_skills:
            args.append("--copy-skills")
        return cmd_connect(args)

    def disconnect(self, targets: tuple[str, ...], dry_run: bool = False) -> int:
        args = [str(t) for t in targets]
        if dry_run:
            args.append("--dry-run")
        return cmd_disconnect(args)
