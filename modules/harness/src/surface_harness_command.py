"""Harness surface command — aa connect / aa disconnect CLI adapters.

Thin CLI layer: parses argv, builds the feature via an injected factory
(wired by the root composition layer — AES205), and prints. No capability,
agent, or root imports (AES201/AES205 surface rule).
"""
from __future__ import annotations

import sys
from collections.abc import Callable

from modules.shared.src.contract_harness_aggregate import IHarnessAggregate
from modules.shared.src.taxonomy_harness_constant import (
    ALIASES,
    ALL_HARNESS_IDS,
    HARNESSES,
)

_HELP_DOC = """agents-arwaky Harness Connector / Disconnector — surface command.

aa connect --antigravity|--hermes|--opencode|--qwencode|--grok-build|--all
   [options: --force --dry-run --mcp-only --skills-only --env-only
             --router --copy-skills]
aa disconnect --antigravity|--hermes|--opencode|--qwencode|--grok-build|--all
   [options: --dry-run]

Skill provisioning links each skill directory to the repo pack under
``skills/`` by default, so edits made through a harness land in the repo and
every agent shares them; ``aa connect --copy-skills`` restores snapshots.

Removes agents-arwaky MCP servers, provisioned skills and env vars from
agent harness paths (NOT the current working directory's .agents/skills —
that is `aa unskill` / skill-manager).
"""

_CONNECT_FLAGS = ("force", "dry-run", "mcp-only", "skills-only", "env-only", "router", "copy-skills")
_DISCONNECT_FLAGS = ("dry-run",)


_FeatureFactory = Callable[[], IHarnessAggregate]


def log_err(msg: str) -> None:
    """Emit a diagnostic line to stderr."""
    print(f"  \u2717 {msg}", file=sys.stderr)


def _parse_targets_and_flags(args: list[str], flags_spec: tuple[str, ...],
                            aliases: dict[str, str] | None = None):
    """Split args into (canonical_targets, unknown_or_None, flags_dict).

    ``--all`` / ``all`` expand to every supported id. ``--<id>`` or a bare
    id / alias is a harness token. ``--<flag>`` (or an aliased short flag)
    sets flags_dict. Anything else is returned as ``unknown`` so the CLI
    can surface it. ``flags`` keys use underscores; short aliases map to
    them via the *aliases* dict (e.g. ``-f`` → ``force``).
    """
    targets: list[str] = []
    flags: dict[str, bool] = {f.replace("-", "_"): False for f in flags_spec}
    aliases = aliases or {}
    unknown = None
    for a in args:
        if a in ("--all", "all"):
            targets.extend(ALL_HARNESS_IDS)
            continue
        if a.startswith(("--", "-")):
            name = a.lstrip("-")
            # Normalise an alias like "-f" → "force" before lookup.
            if name in aliases:
                name = aliases[name]
            if name in flags:
                flags[name] = True
            elif name in HARNESSES:
                targets.append(name)
            elif name in ALIASES:
                targets.append(ALIASES[name])
            else:
                # Try with underscores for hyphenated flags (e.g. --dry-run → dry_run).
                norm = name.replace("-", "_")
                if norm in flags:
                    flags[norm] = True
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
    seen: set[str] = set()
    deduped = [t for t in targets if not (t in seen or seen.add(t))]
    return deduped, unknown, flags


def cmd_connect(args: list[str], feature_factory: _FeatureFactory) -> int:
    if "help" in args or "--help" in args:
        print(_HELP_DOC)
        return 0
    targets, unknown, flags = _parse_targets_and_flags(args, _CONNECT_FLAGS,
                                                        aliases={"f": "force"})
    if unknown is not None:
        log_err(f"Unknown target or option: {unknown}")
        return 1
    if not targets:
        log_err("No target agent harness specified.")
        print(_HELP_DOC)
        return 1
    orch = feature_factory()
    print("Connecting agents-arwaky to agent harnesses...")
    print("------------------------------------------------------------------")
    rc = orch.connect(
        tuple(targets),
        force=flags["force"], dry_run=flags["dry_run"],
        mcp_only=flags["mcp_only"], skills_only=flags["skills_only"],
        env_only=flags["env_only"], router=flags["router"],
        copy_skills=flags["copy_skills"],
    )
    print("------------------------------------------------------------------")
    if rc:
        return rc
    print("\u2713 Connection complete. Agent harnesses are now synchronized with agents-arwaky.")
    return 0


def cmd_disconnect(args: list[str], feature_factory: _FeatureFactory) -> int:
    if "help" in args or "--help" in args:
        print(_HELP_DOC)
        return 0
    targets, unknown, flags = _parse_targets_and_flags(args, _DISCONNECT_FLAGS)
    if unknown is not None:
        log_err(f"Unknown target or option: {unknown}")
        return 1
    if not targets:
        log_err("No target agent harness specified.")
        print(_HELP_DOC)
        return 1
    orch = feature_factory()
    print("Disconnecting agents-arwaky from agent harnesses...")
    print("------------------------------------------------------------------")
    rc = orch.disconnect(tuple(targets), dry_run=flags["dry_run"])
    print("------------------------------------------------------------------")
    if rc:
        return rc
    print("\u2713 Disconnect complete. agents-arwaky entries removed from selected harnesses.")
    return 0


def main(argv: list[str], feature_factory: _FeatureFactory) -> int:
    if len(argv) < 2 or argv[1] in ("-h", "--help", "help"):
        print(_HELP_DOC)
        return 0
    args = argv[1:]
    if args[0] in ("disconnect", "unconnect"):
        return cmd_disconnect(args[1:], feature_factory)
    if args[0] == "connect":
        return cmd_connect(args[1:], feature_factory)
    if args[0] in ALIASES or args[0] in ("--all", "all"):
        # default action: connect (backward compat with connect-agent.sh calls)
        return cmd_connect(args, feature_factory)
    return cmd_disconnect(args, feature_factory)


__all__ = ["cmd_connect", "cmd_disconnect", "log_err", "main"]
