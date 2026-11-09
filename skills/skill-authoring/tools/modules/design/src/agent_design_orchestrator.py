"""Design agent (AES agent layer).

Implements ``ISkillsDesignAggregate`` over the design-side capabilities:
creator, adopter, linter, runner. Owns the ops: create, adopt, lint, run,
pause, resume. The agent is the only layer allowed to sequence capabilities.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import cast

from shared.src.common.taxonomy_common_error import (
    SkillsError,
    SkillsRootError,
    SkillsUsageError,
)
from shared.src.design.contract_design_aggregate import ISkillsDesignAggregate
from shared.src.design.contract_skills_protocol import (
    ISkillsAdopterProtocol,
    ISkillsCatalogProtocol,
    ISkillsCreatorProtocol,
    ISkillsLinterProtocol,
    ISkillsRunnerProtocol,
)
from shared.src.design.taxonomy_skills_request import (
    SkillsOp,
    SkillsRequest,
    SkillsRoot,
)
from shared.src.design.taxonomy_skills_response import (
    SkillsExitCode,
    SkillsResult,
)

__all__ = [
    "ISkillsDesignAggregate",
    "SkillsDesignAgent",
]


class SkillsDesignAgent(ISkillsDesignAggregate):
    """Design-side agent: create / adopt / lint / run / pause / resume."""

    def __init__(
        self,
        creator: ISkillsCreatorProtocol | None = None,
        adopter: ISkillsAdopterProtocol | None = None,
        linter: ISkillsLinterProtocol | None = None,
        runner: ISkillsRunnerProtocol | None = None,
        catalog: ISkillsCatalogProtocol | None = None,
        default_root: SkillsRoot | None = None,
    ) -> None:
        self._creator = creator
        self._adopter = adopter
        self._linter = linter
        self._runner = runner
        self._catalog = catalog
        self._default_root = default_root

    # ─── Block 1: Module Declaration ───
    def _require(self, capability: object, name: str) -> object:
        if capability is None:
            raise SkillsRootError(f"design capability not wired: {name}")
        return capability

    def _root(self, request: SkillsRequest) -> SkillsRoot | None:
        if request.root:
            return request.root
        if self._default_root is not None:
            return self._default_root
        return None

    def _mutate_skill(
        self,
        request: SkillsRequest,
        op: SkillsOp,
        capability: object,
        verb: str,
        field: str,
        value: object,
    ) -> SkillsResult:
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
            result = getattr(capability, verb)(skill_name, root)
        except (OSError, SkillsError) as failure:
            return SkillsResult(
                ok=False,
                op=op,
                exit_code=SkillsExitCode.ISSUES_FOUND,
                message=str(failure),
            )
        return SkillsResult(ok=True, op=op, message=str(result))

    # ─── Block 2: Module Contract ───
    def execute(self, request: SkillsRequest) -> SkillsResult:
        """Route *request* to the matching design capability."""
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

    def _handler_for(
        self, op: SkillsOp
    ) -> Callable[[SkillsRequest, SkillsOp], SkillsResult]:
        name = f"_execute_{op.value.replace('-', '_')}"
        handler = getattr(self, name, None)
        if not callable(handler):
            raise KeyError(name)
        return cast(Callable[[SkillsRequest, SkillsOp], SkillsResult], handler)

    # ─── Block 3: Module Helpers ───
    def _execute_lint(self, request: SkillsRequest, op: SkillsOp) -> SkillsResult:
        """Run the full lint scan (13-rule checks + weed report)."""
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

    def _execute_create(self, request: SkillsRequest, op: SkillsOp) -> SkillsResult:
        """Create a skill or a category — preview by default."""
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
            catalog = self._require(self._catalog, "catalog")
            catalog_result = catalog.rebuild(root)
            return SkillsResult(
                ok=True, op=op, new_category=plan, catalog=catalog_result, root=root
            )

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

        catalog = self._require(self._catalog, "catalog")
        catalog_result = catalog.rebuild(root)
        return SkillsResult(
            ok=True, op=op, create_plan=plan, catalog=catalog_result, root=root
        )

    def _execute_adopt(self, request: SkillsRequest, op: SkillsOp) -> SkillsResult:
        """ADOPT: mark skill as agent-managed (created_by="agent")."""
        adopter = self._require(self._adopter, "adopter")
        return self._mutate_skill(request, op, adopter, "adopt", "created_by", "agent")

    def _execute_run(self, request: SkillsRequest, op: SkillsOp) -> SkillsResult:
        """RUN: apply automatic transitions per pass."""
        runner = self._require(self._runner, "runner")
        root = self._root(request)
        try:
            report = runner.apply_automatic_transitions(root)
        except OSError as failure:
            return SkillsResult(
                ok=False,
                op=op,
                exit_code=SkillsExitCode.ISSUES_FOUND,
                message=str(failure),
            )
        return SkillsResult(ok=True, op=op, records=report.get("applied", ()), message=str(report))

    def _execute_pause(self, request: SkillsRequest, op: SkillsOp) -> SkillsResult:
        """PAUSE: set pause=True in config."""
        runner = self._require(self._runner, "runner")
        root = self._root(request)
        try:
            runner.pause(root)
        except OSError as failure:
            return SkillsResult(
                ok=False,
                op=op,
                exit_code=SkillsExitCode.ISSUES_FOUND,
                message=str(failure),
            )
        return SkillsResult(ok=True, op=op, message="lifecycle paused")

    def _execute_resume(self, request: SkillsRequest, op: SkillsOp) -> SkillsResult:
        """RESUME: set pause=False in config."""
        runner = self._require(self._runner, "runner")
        root = self._root(request)
        try:
            runner.resume(root)
        except OSError as failure:
            return SkillsResult(
                ok=False,
                op=op,
                exit_code=SkillsExitCode.ISSUES_FOUND,
                message=str(failure),
            )
        return SkillsResult(ok=True, op=op, message="lifecycle resumed")

    def show_skill(self, name: str, root: SkillsRoot | None = None):
        """Pass-through kept for facade compatibility (design has no reader)."""
        return SkillsResult(
            ok=False,
            op=SkillsOp.LIST,
            exit_code=SkillsExitCode.USAGE_ERROR,
            message="show_skill is not supported by the design agent",
        )
