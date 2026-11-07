"""Skills orchestrator (AES agent layer).

Implements ``ISkillsAggregate``: a single ``execute`` entry point that
the surface, root CLI, and other features call with a typed
``SkillsRequest``. The agent is the only layer allowed to sequence
capabilities — in particular the rule that a mutation rebuilds the
catalog *after* it applies belongs here, never in a capability (no
inter-capability calls) and never in the surface (no business
sequencing in the UI layer).

The agent depends only on contract protocols and taxonomy; the
composition root injects every capability implementation.

The ``traces`` op is owned by the independent traces app; this package never
imports the sibling tree and never dispatches ``SkillsOp.TRACES``.
"""

from __future__ import annotations

import json
from collections.abc import Callable, Sequence
from pathlib import Path
from typing import cast

from shared.src.skills_design.contract_skills_aggregate import ISkillsAggregate
from shared.src.skills_design.contract_skills_protocol import (
    ISkillsArchiverProtocol,
    ISkillsCatalogProtocol,
    ISkillsCreatorProtocol,
    ISkillsDiscoverProtocol,
    ISkillsLinterProtocol,
    ISkillsListerProtocol,
    ISkillsMoverProtocol,
    ISkillsReaderProtocol,
)
from shared.src.skills_design.taxonomy_skills_constant import ARCHIVE_DIRNAME
from shared.src.skills_design.taxonomy_skills_error import (
    SkillsError,
    SkillsRootError,
    SkillsUsageError,
)
from shared.src.skills_design.taxonomy_skills_request import (
    SkillQuery,
    SkillsOp,
    SkillsRequest,
    SkillsRoot,
)
from shared.src.skills_design.taxonomy_skills_response import (
    SkillsExitCode,
    SkillsResult,
)
from shared.src.skills_design.taxonomy_skills_vo import (
    SkillContent,
    SkillRecord,
)

from skills_design.src.capabilities_skills_adopter import SkillsAdopter
from skills_design.src.capabilities_skills_backup import SkillsBackup
from skills_design.src.capabilities_skills_ledger import SkillsLedger
from skills_design.src.capabilities_skills_locker import SkillsLocker
from skills_design.src.capabilities_skills_piner import SkillsPiner
from skills_design.src.capabilities_skills_prune import SkillsPrune
from skills_design.src.capabilities_skills_purge import SkillsPurge
from skills_design.src.capabilities_skills_restore import SkillsRestore
from skills_design.src.capabilities_skills_rollback import SkillsRollback
from skills_design.src.capabilities_skills_runner import SkillsRunner
from skills_design.src.capabilities_skills_telemetry import SkillsTelemetry


# ─── Block 1: Class Definition & Constructor ──────────────
class SkillsAgent(ISkillsAggregate):
    """Dispatches every skills op and owns the mutation→catalog pipeline."""

    def __init__(
        self,
        lister: ISkillsListerProtocol,
        reader: ISkillsReaderProtocol,
        *,
        linter: ISkillsLinterProtocol | None = None,
        catalog: ISkillsCatalogProtocol | None = None,
        discover: ISkillsDiscoverProtocol | None = None,
        mover: ISkillsMoverProtocol | None = None,
        archiver: ISkillsArchiverProtocol | None = None,
        creator: ISkillsCreatorProtocol | None = None,
        telemetry: SkillsTelemetry | None = None,
        runner: SkillsRunner | None = None,
        piner: SkillsPiner | None = None,
        locker: SkillsLocker | None = None,
        adopter: SkillsAdopter | None = None,
        restore: SkillsRestore | None = None,
        prune: SkillsPrune | None = None,
        purge: SkillsPurge | None = None,
        backup: SkillsBackup | None = None,
        rollback: SkillsRollback | None = None,
        ledger: SkillsLedger | None = None,
        default_root: Path | None = None,
    ) -> None:
        self._lister = lister
        self._reader = reader
        self._linter = linter
        self._catalog = catalog
        self._discover = discover
        self._mover = mover
        self._archiver = archiver
        self._creator = creator

        wired_telemetry = telemetry if telemetry is not None else SkillsTelemetry()
        wired_backup = backup if backup is not None else SkillsBackup()
        self._telemetry = wired_telemetry
        self._runner = runner if runner is not None else SkillsRunner()
        self._piner = piner if piner is not None else SkillsPiner()
        self._locker = locker if locker is not None else SkillsLocker()
        self._adopter = adopter if adopter is not None else SkillsAdopter()
        self._restore = (
            restore
            if restore is not None
            else SkillsRestore(reanchor=wired_telemetry.reanchor_clock)
        )
        self._prune = prune if prune is not None else SkillsPrune()
        self._purge = purge if purge is not None else SkillsPurge()
        self._backup = wired_backup
        self._rollback = (
            rollback if rollback is not None else SkillsRollback(wired_backup)
        )
        self._ledger = ledger if ledger is not None else SkillsLedger()
        self._default_root = default_root

    # ─── Block 2: Aggregate Method Implementation ────────────
    def execute(self, request: SkillsRequest) -> SkillsResult:
        """Route *request* to the matching capability; return the response."""
        try:
            op = SkillsOp(request.op)
        except ValueError:
            return SkillsResult(
                ok=False,
                op=SkillsOp.LIST,
                exit_code=SkillsExitCode.USAGE_ERROR,
                message=f"Unknown skills op: {request.op}",
            )

        try:
            handler = self._handler_for(op)
        except KeyError:
            return SkillsResult(
                ok=False,
                op=op,
                exit_code=SkillsExitCode.USAGE_ERROR,
                message=f"Unknown skills op: {op}",
            )

        try:
            return handler(request, op)
        except SkillsError as failure:
            return SkillsResult(
                ok=False,
                op=op,
                exit_code=failure.exit_code,
                message=str(failure),
            )

    # ─── Block 3: Per-Op Handlers ─────────────────────────────
    def _handler_for(
        self, op: SkillsOp
    ) -> Callable[[SkillsRequest, SkillsOp], SkillsResult]:
        """The typed handler for one op; ``KeyError`` for an unknown one."""
        name = f"_execute_{op.value.replace('-', '_')}"
        handler = getattr(self, name, None)
        if not callable(handler):
            raise KeyError(name)
        return cast(Callable[[SkillsRequest, SkillsOp], SkillsResult], handler)

    def _execute_list(self, request: SkillsRequest, op: SkillsOp) -> SkillsResult:
        """List every skill in the pack."""
        lister = self._require(self._lister, "lister")
        records = tuple(lister.list_skills(request.root))
        return SkillsResult(
            ok=True,
            op=op,
            records=records,
            message="" if records else "No skills found",
        )

    def _execute_read(self, request: SkillsRequest, op: SkillsOp) -> SkillsResult:
        """Return one skill's raw SKILL.md content."""
        content = self._reader.show_skill(request.query, request.root)
        if content is None:
            return SkillsResult(
                ok=False,
                op=op,
                exit_code=SkillsExitCode.ISSUES_FOUND,
                message=f"Skill not found: {request.query}",
            )
        return SkillsResult(ok=True, op=op, content=content)

    def _execute_lint(self, request: SkillsRequest, op: SkillsOp) -> SkillsResult:
        """Run the full lint scan (13-rule checks + weed report) over the root."""
        linter = self._require(self._linter, "linter")
        category = request.flags.get("category") or None
        report = linter.lint(self._root(request), category=category)

        exit_code = (
            SkillsExitCode.CLEAN
            if report.unfiltered_issue_count == 0
            else SkillsExitCode.ISSUES_FOUND
        )
        return SkillsResult(
            ok=exit_code == SkillsExitCode.CLEAN,
            op=op,
            exit_code=exit_code,
            lint_report=report,
            root=report.skills_root,
        )

    def _execute_catalog(self, request: SkillsRequest, op: SkillsOp) -> SkillsResult:
        """Rebuild the catalog and/or read it back, per the ``build``/``read`` flags.

        The ``check`` flag (drift gate, exit 3) stays available at the
        capability/agent level but is no longer routed from the CLI.
        """
        catalog = self._require(self._catalog, "catalog")
        root = self._root(request)

        if request.flags.get("check") == "1":
            check = catalog.check(root)
            exit_code = (
                SkillsExitCode.CLEAN
                if check.in_sync
                else SkillsExitCode.CATALOG_DRIFT
            )
            return SkillsResult(
                ok=check.in_sync,
                op=op,
                exit_code=exit_code,
                check=check,
                message=check.message,
                root=root,
            )

        # CLI surface: the parser tri-state resolves to an explicit flag
        # value; no flag at all → both (build then print).
        # Facade: a bare catalog request (no build/read keys) → build only.
        build = (
            request.flags.get("build", "1") == "1"
            if "build" in request.flags or "read" in request.flags
            else True
        )
        read = request.flags.get("read", "0") == "1"

        if build:
            report = catalog.rebuild(root)
        else:
            report = None

        if read:
            text = catalog.read(root)
            if not text:
                return SkillsResult(
                    ok=False,
                    op=op,
                    exit_code=SkillsExitCode.ISSUES_FOUND,
                    message="catalog.json not found — run with --build first",
                    root=root,
                )
            return SkillsResult(
                ok=True,
                op=op,
                catalog=report,
                catalog_text=text,
                root=root,
            )

        return SkillsResult(ok=True, op=op, catalog=report, root=root)

    def _execute_discover(
        self, request: SkillsRequest, op: SkillsOp
    ) -> SkillsResult:
        """Score the catalog against the query, with the drift fallback."""
        discover = self._require(self._discover, "discover")
        limit = int(request.flags.get("limit", "20"))
        root = self._root(request)
        result = discover.discover(str(request.query), root, limit)

        return SkillsResult(
            ok=True,
            op=op,
            matches=result.matches,
            warning=result.warning or None,
            message=result.warning_detail,
            root=root,
        )

    def _execute_move(self, request: SkillsRequest, op: SkillsOp) -> SkillsResult:
        """Move a skill folder to another category — preview by default."""
        mover = self._require(self._mover, "mover")
        root = self._root(request)
        plan = mover.plan_move(
            str(request.query), request.flags.get("target", ""), root
        )

        if plan.already_in_category or not request.apply:
            return SkillsResult(ok=True, op=op, plan=plan, root=root)

        outcome = mover.apply_move(plan)
        catalog = self._require(self._catalog, "catalog").rebuild(root)
        return SkillsResult(
            ok=True, op=op, plan=plan, outcome=outcome, catalog=catalog, root=root
        )

    def _execute_archive(self, request: SkillsRequest, op: SkillsOp) -> SkillsResult:
        """Archive a skill into ``_archive/`` — preview by default."""
        archiver = self._require(self._archiver, "archiver")
        root = self._root(request)
        plan = archiver.plan_archive(str(request.query), root)

        if not request.apply:
            return SkillsResult(ok=True, op=op, plan=plan, root=root)

        outcome = archiver.apply_archive(plan)
        catalog = self._require(self._catalog, "catalog").rebuild(root)
        return SkillsResult(
            ok=True, op=op, plan=plan, outcome=outcome, catalog=catalog, root=root
        )

    def _execute_create(self, request: SkillsRequest, op: SkillsOp) -> SkillsResult:
        """Create a skill or a category in the pack — preview by default.

        ``flags["kind"]`` selects the verb: ``"skill"`` (default) or
        ``"category"``. The agent routes to the matching creator method
        and, on an applied write, rebuilds the catalog.
        """
        creator = self._require(self._creator, "creator")
        root = self._root(request)
        kind = request.flags.get("kind", "skill")

        if kind == "category":
            name = str(request.query)
            description = request.description or ""
            force = request.flags.get("force") == "1"
            plan = creator.create_category(
                name=name,
                description=description,
                root=root,
                force=force,
                apply=request.apply,
            )
            if not request.apply:
                return SkillsResult(ok=True, op=op, new_category=plan, root=root)
            catalog = self._require(self._catalog, "catalog").rebuild(root)
            return SkillsResult(
                ok=True,
                op=op,
                new_category=plan,
                catalog=catalog,
                root=root,
            )

        # kind == "skill" (default)
        skill = str(request.query)
        category = request.flags.get("category", "")
        if not category:
            raise SkillsUsageError(
                "Missing --category: pass --category <cat> for the new skill folder"
            )

        description = request.description
        when_to_use = request.flags.get("when_to_use", "")
        argument_hint = request.flags.get("argument_hint", "")
        body = request.flags.get("body", "")

        plan = creator.create_skill(
            skill=skill,
            category=category,
            description=description,
            when_to_use=when_to_use,
            argument_hint=argument_hint,
            body=body,
            root=root,
            apply=request.apply,
        )

        if plan.already_exists or not request.apply:
            return SkillsResult(ok=True, op=op, create_plan=plan, root=root)

        catalog = self._require(self._catalog, "catalog").rebuild(root)
        return SkillsResult(
            ok=True,
            op=op,
            create_plan=plan,
            catalog=catalog,
            root=root,
        )

    # ─── Block 3b: Lifecycle handlers ──────────────────────────────
    # All lifecycle ops route here through the single execute seam.

    def _execute_status(self, request: SkillsRequest, op: SkillsOp) -> SkillsResult:
        """STATUS: telemetry report rows as records."""
        telemetry = self._require(self._telemetry, "telemetry")
        root = self._root(request)
        try:
            rows = telemetry.curated_report(root)
        except OSError as failure:
            return SkillsResult(ok=False, op=op, exit_code=SkillsExitCode.ISSUES_FOUND, message=str(failure))
        return SkillsResult(ok=True, op=op, records=rows, message=f"{len(rows)} skill(s) tracked")

    def _execute_usage(self, request: SkillsRequest, op: SkillsOp) -> SkillsResult:
        """USAGE: same telemetry report as status (surface decides rendering)."""
        telemetry = self._require(self._telemetry, "telemetry")
        root = self._root(request)
        try:
            rows = telemetry.curated_report(root)
        except OSError as failure:
            return SkillsResult(ok=False, op=op, exit_code=SkillsExitCode.ISSUES_FOUND, message=str(failure))
        return SkillsResult(ok=True, op=op, records=rows, message=f"{len(rows)} skill(s) tracked")

    def _execute_run(self, request: SkillsRequest, op: SkillsOp) -> SkillsResult:
        """RUN: apply automatic transitions per pass."""
        runner = self._require(self._runner, "runner")
        root = self._root(request)
        try:
            report = runner.apply_automatic_transitions(root)
        except OSError as failure:
            return SkillsResult(ok=False, op=op, exit_code=SkillsExitCode.ISSUES_FOUND, message=str(failure))
        return SkillsResult(ok=True, op=op, records=report.get("applied", ()), message=str(report))

    def _execute_pause(self, request: SkillsRequest, op: SkillsOp) -> SkillsResult:
        """PAUSE: set pause=True in config."""
        runner = self._require(self._runner, "runner")
        root = self._root(request)
        try:
            runner.pause(root)
        except OSError as failure:
            return SkillsResult(ok=False, op=op, exit_code=SkillsExitCode.ISSUES_FOUND, message=str(failure))
        return SkillsResult(ok=True, op=op, message="lifecycle paused")

    def _execute_resume(self, request: SkillsRequest, op: SkillsOp) -> SkillsResult:
        """RESUME: set pause=False in config."""
        runner = self._require(self._runner, "runner")
        root = self._root(request)
        try:
            runner.resume(root)
        except OSError as failure:
            return SkillsResult(ok=False, op=op, exit_code=SkillsExitCode.ISSUES_FOUND, message=str(failure))
        return SkillsResult(ok=True, op=op, message="lifecycle resumed")

    def _execute_pin(self, request: SkillsRequest, op: SkillsOp) -> SkillsResult:
        """PIN: set pinned=True on *skill* sidecar."""
        piner = self._require(self._piner, "piner")
        return self._mutate_skill(request, op, piner, "pin", "pinned", True)

    def _execute_unpin(self, request: SkillsRequest, op: SkillsOp) -> SkillsResult:
        """UNPIN: set pinned=False on *skill* sidecar."""
        piner = self._require(self._piner, "piner")
        return self._mutate_skill(request, op, piner, "unpin", "pinned", False)

    def _execute_lock(self, request: SkillsRequest, op: SkillsOp) -> SkillsResult:
        """LOCK: set locked=True on *skill* sidecar."""
        locker = self._require(self._locker, "locker")
        return self._mutate_skill(request, op, locker, "lock", "locked", True)

    def _execute_unlock(self, request: SkillsRequest, op: SkillsOp) -> SkillsResult:
        """UNLOCK: set locked=False on *skill* sidecar."""
        locker = self._require(self._locker, "locker")
        return self._mutate_skill(request, op, locker, "unlock", "locked", False)

    def _mutate_skill(
        self,
        request: SkillsRequest,
        op: SkillsOp,
        capability: object,
        method: str,
        field: str,
        value: bool,
        *,
        message: str | None = None,
    ) -> SkillsResult:
        """Resolve one skill, call *method* on *capability*, map errors."""
        if not request.query or str(request.query).strip() in ("", "None"):
            return SkillsResult(
                ok=False,
                op=op,
                exit_code=SkillsExitCode.ISSUES_FOUND,
                message="Skill name required",
            )
        skill_name = str(request.query).strip()
        root = Path(self._root(request))
        if self._find_skill_dir(skill_name, root) is None:
            return SkillsResult(
                ok=False,
                op=op,
                exit_code=SkillsExitCode.ISSUES_FOUND,
                message=f"Skill not found: {skill_name}",
            )
        try:
            getattr(capability, method)(skill_name, root)
        except (OSError, ValueError, SkillsError) as failure:
            return SkillsResult(
                ok=False,
                op=op,
                exit_code=SkillsExitCode.ISSUES_FOUND,
                message=str(failure),
            )
        if message is not None:
            return SkillsResult(ok=True, op=op, message=message.format(skill=skill_name))
        return SkillsResult(ok=True, op=op, message=f"{field}={value} for {skill_name}")

    def _execute_lifecycle_archive(self, request: SkillsRequest, op: SkillsOp) -> SkillsResult:
        """Archive: restore.archive(skill, root)."""
        restore = self._require(self._restore, "restore")
        root = self._root(request)
        if not request.query or str(request.query).strip() in ("", "None"):
            return SkillsResult(
                ok=False,
                op=op,
                exit_code=SkillsExitCode.ISSUES_FOUND,
                message="Skill name required",
            )
        skill_name = str(request.query).strip()
        try:
            result = restore.archive(skill_name, root)
        except (OSError, SkillsError) as failure:
            return SkillsResult(ok=False, op=op, exit_code=SkillsExitCode.ISSUES_FOUND, message=str(failure))
        return SkillsResult(ok=True, op=op, message=str(result))

    def _execute_restore(self, request: SkillsRequest, op: SkillsOp) -> SkillsResult:
        """RESTORE: restore.restore(skill, root)."""
        restore = self._require(self._restore, "restore")
        root = self._root(request)
        if not request.query or str(request.query).strip() in ("", "None"):
            return SkillsResult(
                ok=False,
                op=op,
                exit_code=SkillsExitCode.ISSUES_FOUND,
                message="Skill name required",
            )
        skill_name = str(request.query).strip()
        try:
            result = restore.restore(skill_name, root)
        except (OSError, SkillsError) as failure:
            return SkillsResult(ok=False, op=op, exit_code=SkillsExitCode.ISSUES_FOUND, message=str(failure))
        return SkillsResult(ok=True, op=op, message=str(result))

    def _execute_prune(self, request: SkillsRequest, op: SkillsOp) -> SkillsResult:
        """PRUNE: prune.prune(root, days, dry_run) — bulk-archive idle skills."""
        prune = self._require(self._prune, "prune")
        root = self._root(request)
        days = int(request.flags["days"]) if "days" in request.flags else None
        dry_run = bool(request.flags.get("dry_run", False) or request.flags.get("dry-run", False))
        try:
            report = prune.prune(root=root, days=days, dry_run=dry_run)
        except (OSError, ValueError) as failure:
            return SkillsResult(ok=False, op=op, exit_code=SkillsExitCode.ISSUES_FOUND, message=str(failure))
        return SkillsResult(ok=True, op=op, records=report.get("pruned", ()), message=str(report))

    def _execute_purge(self, request: SkillsRequest, op: SkillsOp) -> SkillsResult:
        """PURGE: purge.purge(skill, root, dry_run) — delete archived skills."""
        purge = self._require(self._purge, "purge")
        root = self._root(request)
        query = str(request.query).strip() if request.query else ""
        skill_name = query if query and query != "None" else None
        dry_run = bool(request.flags.get("dry_run", False) or request.flags.get("dry-run", False))
        try:
            result = purge.purge(skill=skill_name, root=root, dry_run=dry_run)
        except (OSError, ValueError) as failure:
            return SkillsResult(ok=False, op=op, exit_code=SkillsExitCode.ISSUES_FOUND, message=str(failure))
        return SkillsResult(ok=True, op=op, message=str(result))

    def _execute_adopt(self, request: SkillsRequest, op: SkillsOp) -> SkillsResult:
        """ADOPT: mark skill as agent-managed (created_by="agent")."""
        adopter = self._require(self._adopter, "adopter")
        return self._mutate_skill(
            request, op, adopter, "adopt", "created_by", True, message="adopted {skill}"
        )

    def _execute_backup(self, request: SkillsRequest, op: SkillsOp) -> SkillsResult:
        """BACKUP: backup.create_snapshot(root) -> snapshot path."""
        backup = self._require(self._backup, "backup")
        root = self._root(request)
        try:
            path = backup.create_snapshot(root)
        except OSError as failure:
            return SkillsResult(ok=False, op=op, exit_code=SkillsExitCode.ISSUES_FOUND, message=str(failure))
        return SkillsResult(ok=True, op=op, content=str(path), message=f"snapshot at {path}")

    def _execute_rollback(self, request: SkillsRequest, op: SkillsOp) -> SkillsResult:
        """ROLLBACK: rollback.rollback(root, id_) with id from query/flags."""
        rollback = self._require(self._rollback, "rollback")
        root = self._root(request)
        snapshot_id = request.query or request.flags.get("id", "")
        try:
            result = rollback.rollback(root, snapshot_id or None)
        except (OSError, SkillsError) as failure:
            return SkillsResult(ok=False, op=op, exit_code=SkillsExitCode.ISSUES_FOUND, message=str(failure))
        return SkillsResult(ok=True, op=op, message=str(result))

    def _execute_ledger(self, request: SkillsRequest, op: SkillsOp) -> SkillsResult:
        """LEDGER: ledger_read, or ledger_compact when flags['--compact']."""
        ledger = self._require(self._ledger, "ledger")
        root = self._root(request)
        if request.flags.get("compact") == "1":
            try:
                result = ledger.ledger_compact(root)
            except OSError as failure:
                return SkillsResult(ok=False, op=op, exit_code=SkillsExitCode.ISSUES_FOUND, message=str(failure))
            return SkillsResult(ok=True, op=op, message=str(result))
        try:
            rows = ledger.ledger_read(root)
        except OSError as failure:
            return SkillsResult(ok=False, op=op, exit_code=SkillsExitCode.ISSUES_FOUND, message=str(failure))
        return SkillsResult(ok=True, op=op, records=rows, message=f"{len(rows)} ledger entry(ies)")

    def _execute_list_unmanaged(self, request: SkillsRequest, op: SkillsOp) -> SkillsResult:
        """LIST_UNMANAGED: skills with no sidecar OR created_by != 'agent'."""
        self._require(self._telemetry, "telemetry")
        root = Path(self._root(request))
        if not root.is_dir():
            return SkillsResult(ok=True, op=op, records=(), message="0 unmanaged")
        unmanaged: list[dict] = []
        for cat_dir in root.iterdir():
            if not cat_dir.is_dir() or cat_dir.name.startswith((".", "_")):
                continue
            for skill_dir in cat_dir.iterdir():
                if not skill_dir.is_dir() or not (skill_dir / "SKILL.md").exists():
                    continue
                sidecar = skill_dir / ".usage.json"
                if not sidecar.is_file():
                    unmanaged.append({"name": skill_dir.name, "category": cat_dir.name, "created_by": "unmanaged"})
                else:
                    try:
                        rec = json.loads(sidecar.read_text(encoding="utf-8"))
                    except (OSError, ValueError, json.JSONDecodeError):
                        rec = {}
                    if rec.get("created_by") != "agent":
                        unmanaged.append({"name": skill_dir.name, "category": cat_dir.name, "created_by": rec.get("created_by", "unmanaged")})
        return SkillsResult(ok=True, op=op, records=unmanaged, message=f"{len(unmanaged)} unmanaged")

    def _execute_list_archived(self, request: SkillsRequest, op: SkillsOp) -> SkillsResult:
        """LIST_ARCHIVED: skills currently in _archive/."""
        self._require(self._restore, "restore")
        root = Path(self._root(request))
        arch_dir = root / ARCHIVE_DIRNAME
        if not arch_dir.is_dir():
            return SkillsResult(ok=True, op=op, records=(), message="0 archived")
        archived: list[dict] = []
        for cat_dir in arch_dir.iterdir():
            if not cat_dir.is_dir() or cat_dir.name.startswith("."):
                continue
            for skill_dir in cat_dir.iterdir():
                if not skill_dir.is_dir() or not (skill_dir / "SKILL.md").exists():
                    continue
                sidecar = skill_dir / ".usage.json"
                rec = {}
                if sidecar.is_file():
                    try:
                        rec = json.loads(sidecar.read_text(encoding="utf-8"))
                    except (OSError, ValueError, json.JSONDecodeError):
                        rec = {}
                archived.append({
                    "name": skill_dir.name,
                    "category": cat_dir.name,
                    "state": "archived",
                    "archived_at": rec.get("archived_at"),
                })
        return SkillsResult(ok=True, op=op, records=archived, message=f"{len(archived)} archived")

    def _find_skill_dir(self, skill: str, root: Path, in_archive: bool = False) -> Path | None:
        """Find a skill directory under *root* by name (any category)."""
        base = root / ARCHIVE_DIRNAME if in_archive else root
        if not base.is_dir():
            return None
        for child in base.iterdir():
            if not child.is_dir() or (not in_archive and child.name.startswith((".", "_"))):
                continue
            candidate = child / skill
            if candidate.is_dir() and (candidate / "SKILL.md").exists():
                return candidate
        return None

    def _root(self, request: SkillsRequest) -> SkillsRoot:
        """Resolve the request's root: explicit beats derived, never silent."""
        if request.root is not None:
            path = request.root
            if not path.is_dir():
                raise SkillsRootError(f"Skills root does not exist: {path}")
            return path
        if self._default_root is not None:
            return self._default_root
        raise SkillsUsageError("No skills root configured")

    @staticmethod
    def _require(capability: object, name: str) -> object:
        """Fail loudly when an op is used on an aggregate wired without it."""
        if capability is None:
            raise SkillsUsageError(f"Skills {name} capability is not configured")
        return capability

    def list_skills(self, root: SkillsRoot | None = None) -> Sequence[SkillRecord]:
        """Convenience pass-through to the lister (used by tests; the facade builds its own request)."""
        return self._lister.list_skills(root)

    def show_skill(
        self, name: str, root: SkillsRoot | None = None
    ) -> SkillContent | None:
        """Convenience pass-through to the reader (used by the facade)."""
        return self._reader.show_skill(SkillQuery(name), root)
