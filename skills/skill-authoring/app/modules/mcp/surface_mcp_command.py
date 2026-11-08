"""Skills-design MCP adapter (AES surface layer).

MCP adapter exposing every ``sdc`` skill command as an MCP tool with
1:1 CLI equivalence. Each MCP tool delegates to the composed
``ISkillsAggregate.execute`` path — the same path the CLI uses — and
therefore triggers the same telemetry view recording on success.

The public entry point is ``SkillsMcpAdapter``.
"""
from __future__ import annotations

from shared.src.design.contract_skills_aggregate import ISkillsAggregate
from shared.src.design.taxonomy_skills_request import (
    SkillQuery,
    SkillsOp,
    SkillsRequest,
)
from shared.src.design.taxonomy_skills_response import SkillsResult

__all__ = ["SkillsMcpAdapter"]


class SkillsMcpAdapter:
    """MCP adapter: maps sdc verbs to MCP tools, 1:1 with the CLI.

    Every tool delegates to the composed aggregate — the same execution
    path the CLI surface uses — so telemetry view recording happens
    identically through both entry points.
    """

    def __init__(self, aggregate: ISkillsAggregate) -> None:
        self._aggregate = aggregate

    # ── Tool registry ───────────────────────────────────────────────

    def list_tools(self) -> list[dict]:
        """Return MCP tool descriptors, one per sdc verb (24 tools)."""
        return [
            {"name": "sdc_list", "description": "List all skills in the pack"},
            {"name": "sdc_read", "description": "Print a skill's SKILL.md"},
            {"name": "sdc_lint", "description": "Lint scan all skills"},
            {"name": "sdc_catalog", "description": "Build and/or print catalog.json"},
            {"name": "sdc_discover", "description": "Search the catalog"},
            {"name": "sdc_move", "description": "Move a skill to a category"},
            {"name": "sdc_archive", "description": "Archive a skill"},
            {"name": "sdc_create", "description": "Create a skill or category"},
            {"name": "sdc_status", "description": "Show per-skill lifecycle states"},
            {"name": "sdc_usage", "description": "Show usage telemetry rows"},
            {"name": "sdc_run", "description": "Run automated state transitions"},
            {"name": "sdc_pause", "description": "Pause automatic transitions"},
            {"name": "sdc_resume", "description": "Resume automatic transitions"},
            {"name": "sdc_pin", "description": "Pin a skill"},
            {"name": "sdc_unpin", "description": "Unpin a skill"},
            {"name": "sdc_lock", "description": "Lock a skill"},
            {"name": "sdc_unlock", "description": "Unlock a skill"},
            {"name": "sdc_restore", "description": "Restore an archived skill"},
            {"name": "sdc_prune", "description": "Bulk archive idle skills"},
            {"name": "sdc_purge", "description": "Permanently remove archived skills"},
            {"name": "sdc_adopt", "description": "Mark skill as agent-managed"},
            {"name": "sdc_backup", "description": "Create a snapshot of the skills pack"},
            {"name": "sdc_rollback", "description": "Restore from snapshot"},
            {"name": "sdc_ledger", "description": "View or compact audit ledger"},
        ]

    def execute_tool(self, name: str, arguments: dict) -> dict:
        """Dispatch an MCP tool call to the aggregate and return an MCP result."""
        tool_name = name.removeprefix("sdc_")
        result = self._dispatch(tool_name, arguments)
        return {
            "ok": result.ok,
            "content": [{"type": "text", "text": result.message or str(result)}],
        }

    # ── Internals ──────────────────────────────────────────────────

    def _op_from_tool(self, tool: str) -> SkillsOp:
        mapping = {
            "list": SkillsOp.LIST,
            "read": SkillsOp.READ,
            "lint": SkillsOp.LINT,
            "catalog": SkillsOp.CATALOG,
            "discover": SkillsOp.DISCOVER,
            "move": SkillsOp.MOVE,
            "archive": SkillsOp.ARCHIVE,
            "create": SkillsOp.CREATE,
            "status": SkillsOp.STATUS,
            "usage": SkillsOp.USAGE,
            "run": SkillsOp.RUN,
            "pause": SkillsOp.PAUSE,
            "resume": SkillsOp.RESUME,
            "pin": SkillsOp.PIN,
            "unpin": SkillsOp.UNPIN,
            "lock": SkillsOp.LOCK,
            "unlock": SkillsOp.UNLOCK,
            "restore": SkillsOp.RESTORE,
            "prune": SkillsOp.PRUNE,
            "purge": SkillsOp.PURGE,
            "adopt": SkillsOp.ADOPT,
            "backup": SkillsOp.BACKUP,
            "rollback": SkillsOp.ROLLBACK,
            "ledger": SkillsOp.LEDGER,
        }
        try:
            return mapping[tool]
        except KeyError:
            return SkillsOp.LIST

    def _dispatch(self, tool: str, args: dict) -> SkillsResult:
        op = self._op_from_tool(tool)
        query = SkillQuery(args.get("query", args.get("skill", "")))
        flags = self._flags(tool, args)
        apply_ = bool(args.get("apply", False))
        request = SkillsRequest(op=op, query=query, flags=flags, apply=apply_)
        return self._aggregate.execute(request)

    @staticmethod
    def _flags(tool: str, args: dict) -> dict:
        flags: dict = {}
        if tool == "lint" and args.get("category"):
            flags["category"] = args["category"]
        if tool == "catalog":
            flags["build"] = "1"
            flags["read"] = "1"
        if tool == "discover":
            flags["limit"] = str(args.get("limit", 20))
        if tool == "move" and args.get("target"):
            flags["target"] = args["target"]
        if tool == "create":
            for key in ("kind", "category", "description", "when_to_use", "argument_hint", "body"):
                if args.get(key):
                    flags[key] = args[key]
            if args.get("force"):
                flags["force"] = "1"
        if tool == "prune":
            for key in ("days", "dry_run"):
                if args.get(key) is not None:
                    flags[key] = str(args[key])
        if tool == "purge":
            for key in ("days", "dry_run"):
                if args.get(key) is not None:
                    flags[key] = str(args[key])
        if tool == "rollback" and args.get("id"):
            flags["id"] = args["id"]
        if tool == "ledger" and args.get("compact"):
            flags["compact"] = "1"
        return flags


__all__ = ["SkillsMcpAdapter"]
