#!/usr/bin/env python3
"""agents-arwaky Harness Connector / Disconnector — surface command (P4-A2).

Thin dispatch layer: parses CLI args, resolves harness targets through the
adapter registry, and delegates to per-harness capability modules.

Supports:
    aa disconnect --antigravity|--hermes|--opencode|--qwencode|--all
    aa disconnect --lean-ctx
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


# --- legacy lean-ctx cleanup (special command, not a harness adapter) ---------
def disconnect_legacy_lean_ctx(dry_run: bool):
    log_header("Cleaning up legacy lean-ctx remnants...")
    # 1. Hermes config.yaml mcp_servers.lean-ctx
    h = hermes_home()
    remove_mcp_servers(h / "config.yaml", dry_run)

    # 2. HERMES.md lean-ctx comment blocks (main + profiles)
    hermes_mds = [h / "HERMES.md"]
    if (h / "profiles").is_dir():
        hermes_mds.extend((h / "profiles").glob("*/HERMES.md"))
    for hmd in hermes_mds:
        if not hmd.is_file():
            continue
        if dry_run:
            log_sub(f"[DRY-RUN] Would strip lean-ctx blocks from {hmd}")
            continue
        try:
            s = hmd.read_text(encoding="utf-8")
            before = s
            s = re.sub(r"(?s)<!--\s*lean-ctx-rules\s*-->.*?<!--\s*/lean-ctx-rules\s*-->\n?", "", s)
            s = re.sub(r"(?s)<!--\s*lean-ctx-compression\s*-->.*?<!--\s*/lean-ctx-compression\s*-->\n?", "", s)
            s = re.sub(r"(?s)<!--\s*lean-ctx-solution\s*-->.*?<!--\s*/lean-ctx-solution\s*-->\n?", "", s)
            s = re.sub(r"(?s)<!--\s*lean-ctx\s*-->.*?<!--\s*/lean-ctx\s*-->\n?", "", s)
            s = re.sub(r"(?s)#\s*Lean-CTX.*?(?=\n# |\Z)", "", s, flags=re.IGNORECASE)
            if s != before:
                hmd.write_text(s, encoding="utf-8")
                log_ok(f"Stripped lean-ctx blocks from {hmd}")
        except OSError:
            log_warn(f"Could not process {hmd}")

    # 3. Skill dirs named lean-ctx
    skill_bases = [h / "skills"]
    if (h / "profiles").is_dir():
        skill_bases.extend((h / "profiles").glob("*/skills"))
    for base in skill_bases:
        if base.is_dir():
            d = base / "lean-ctx"
            if d.exists():
                if dry_run:
                    log_sub(f"[DRY-RUN] Would remove skill dir {d}")
                else:
                    shutil.rmtree(d, ignore_errors=True)
                    log_ok(f"Removed skill dir {d}")

    # 4. Zed settings.json
    zed = HOME / ".config" / "zed" / "settings.json"
    remove_mcp_servers(zed, dry_run)

    # 5. All ~/.config/*/mcp_servers.json templates
    for tpl in (HOME / ".config").glob("*/mcp_servers.json"):
        if tpl.is_file():
            removed = remove_mcp_servers(tpl, dry_run)
            if removed or dry_run:
                log_ok(f"Removed agents-arwaky servers from {tpl}")

    # 5b. Qwen settings.json.bak
    qwen_bak = HOME / ".qwen" / "settings.json.bak"
    if qwen_bak.is_file():
        removed = remove_mcp_servers(qwen_bak, dry_run)
        if removed or dry_run:
            log_ok(f"Removed agents-arwaky servers from {qwen_bak}")

    # 6. Binary remnants in internal-bin
    ibin = data_home() / "agents-arwaky" / "internal-bin"
    for b in ("lean-ctx", "_lc", "_lc_compress"):
        f = ibin / b
        if f.exists():
            if dry_run:
                log_sub(f"[DRY-RUN] Would remove binary {f}")
            else:
                f.unlink(missing_ok=True)
                log_ok(f"Removed binary {f}")

    log_ok("Legacy lean-ctx cleanup complete.")


# --- dispatcher --------------------------------------------------------------
def _parse_targets(args):
    """Return (targets, extras) where targets are resolved registry IDs."""
    targets = []
    i = 0
    while i < len(args):
        a = args[i]
        if a in ALIASES:
            targets.append(ALIASES[a])
        elif a in ("--all", "all"):
            targets = list(ALL_HARNESS_IDS)
        elif a in ("--help", "-h", "help"):
            return None, "help"
        else:
            return None, a
        i += 1
    return targets, None


def cmd_disconnect(args):
    dry_run = False
    lean_ctx_only = False
    clean_args = []
    for a in args:
        if a == "--dry-run":
            dry_run = True
        elif a in ("--lean-ctx", "lean-ctx", "lean_ctx"):
            lean_ctx_only = True
        else:
            clean_args.append(a)

    if lean_ctx_only:
        disconnect_legacy_lean_ctx(dry_run)
        return 0

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
