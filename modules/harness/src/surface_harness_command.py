"""Harness surface — CLI adapters for aa connect / aa disconnect.

Flag parsing ported from tools/connect/connect.py. Target/alias resolution
and per-connector dispatch happen in the orchestrator.
"""
from __future__ import annotations

from modules.harness.src.agent_harness_orchestrator import HarnessOrchestrator
from modules.shared.src.harness.contract_harness_aggregate import IHarnessAggregate

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
        print(f"Unknown target or option: {unknown}", file=sys.stderr)
        return 1
    if not targets:
        print("No target agent harness specified.", file=sys.stderr)
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
        print(f"Unknown target or option: {unknown}", file=sys.stderr)
        return 1
    if not targets:
        print("No target agent harness specified.", file=sys.stderr)
        print(HELP)
        return 1
    return orch.disconnect(targets, dry_run=dry_run)
