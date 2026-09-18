"""Harness surface — CLI adapters for aa connect / aa disconnect.

Port of tools/connect/connect.py: thin dispatch layer that parses CLI args,
resolves harness targets through the adapter registry, and delegates to the
per-harness capability modules via the orchestrator.
"""
from __future__ import annotations

from modules.harness.src.agent_harness_orchestrator import log_err
from modules.harness.contract.contract_harness_aggregate import IHarnessAggregate

HELP = """agents-arwaky Harness Connector / Disconnector — surface command.

aa connect|disconnect <targets> [--all] [--force] [--dry-run]
                        [--mcp-only] [--skills-only] [--env-only] [--copy-skills]

Targets: --antigravity --hermes --opencode --qwencode --grok-build
Skill provisioning links each skill directory to the repo pack under skills/
by default; --copy-skills restores snapshots."""


def _parse_targets(args: list[str]) -> tuple[tuple[str, ...], str | None]:
    """Parse CLI args into (harness_id_list, unknown_or_None); 'help' short-circuits."""
    if "help" in args or "--help" in args:
        return (), "help"
    targets: list[str] = []
    unknown: str | None = None
    for a in args:
        if a in ("--all", "all"):
            targets.extend(["--antigravity", "--hermes", "--opencode", "--qwencode", "--grok-build"])
        elif a.startswith("--"):
            targets.append(a)
        elif a in ("antigravity", "hermes", "opencode", "qwencode", "grok-build"):
            targets.append(a)
        else:
            unknown = a
            break
    return tuple(targets), unknown


def cmd_connect(args: list[str], orch: IHarnessAggregate) -> int:
    """aa connect [targets] — parse global flags, route to the orchestrator."""
    force = dry_run = mcp_only = skills_only = env_only = copy_skills = False
    clean_args: list[str] = []
    for a in args:
        if a in ("--force", "-f"):
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
        print(HELP)
        return 0
    if unknown is not None:
        log_err(f"Unknown target or option: {unknown}")
        return 1
    if not targets:
        log_err("No target agent harness specified.")
        print(HELP)
        return 1
    return orch.connect(
        targets,
        force=force,
        dry_run=dry_run,
        mcp_only=mcp_only,
        skills_only=skills_only,
        env_only=env_only,
        copy_skills=copy_skills,
    )


def cmd_disconnect(args: list[str], orch: IHarnessAggregate) -> int:
    """aa disconnect [targets] --dry-run."""
    dry_run = False
    clean_args: list[str] = []
    for a in args:
        if a == "--dry-run":
            dry_run = True
        else:
            clean_args.append(a)
    targets, unknown = _parse_targets(clean_args)
    if unknown == "help":
        print(HELP)
        return 0
    if unknown is not None:
        log_err(f"Unknown target or option: {unknown}")
        return 1
    if not targets:
        log_err("No target agent harness specified.")
        print(HELP)
        return 1
    return orch.disconnect(targets, dry_run=dry_run)


def main(argv, orch: IHarnessAggregate | None = None):
    """Standalone dispatch — accepts both 'aa connect/disconnect ...' style
    and direct alias/flag calls (port of connect.py main())."""
    if len(argv) < 2 or argv[1] in ("-h", "--help", "help"):
        print(HELP)
        return 0
    # Accept both "aa connect/disconnect ..." style and direct calls
    args = argv[1:]
    if orch is None:
        from modules.harness.src.root_harness_container import create_harness_feature
        orch = create_harness_feature()
    if args and args[0] in ("disconnect", "unconnect"):
        return cmd_disconnect(args[1:], orch)
    if args and args[0] == "connect":
        return cmd_connect(args[1:], orch)
    if args and args[0] in ("--all", "all"):
        # default action: connect (for backward compat with connect-agent.sh calls)
        return cmd_connect(args, orch)
    return cmd_disconnect(args, orch)
