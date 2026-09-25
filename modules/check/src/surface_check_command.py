"""Check surface — CLI adapter for aa check (AES102 `command` suffix).

Scope runs delegate to the ICheckAggregate; the docs path/json/subtree audit
runs directly against the shared engine (smart surfaces may import Utility
layer files). This module stays free of agent/capability imports (AES205).

Standard scopes (HOW-TO / operator contract):
  aa check                    — every runner (docs + skill)
  aa check docs [path] [...]  — document invariants only (path/json/subtree)
  aa check skill              — skill-pack loadability only (skills/<category>/<skill>/SKILL.md)
"""
from __future__ import annotations

from pathlib import Path

from modules.shared.src.contract_check_aggregate import ICheckAggregate
from modules.shared.src.taxonomy_check_vo import (
    CHECK_SCOPES,
    CheckExitCode,
    CheckOnly,
)
from modules.shared.src.taxonomy_common_vo import DocFinding
from modules.shared.src.utility_logging_setup import banner, err, info, ok

_USAGE = """Usage: aa check [all|docs|skill] [path] [--include-subtrees] [--json]

  all (default)       Run every registered runner (docs + skill)
  docs                Document invariants only (PRD/ROADMAP/FRD/README/BACKLOG/AGENTS)
  skill               Skill-pack loadability only (skills/<category>/<skill>/SKILL.md)
  path                Audit only documents under this directory (docs scope only)
  --include-subtrees  Also audit vendor/ and internal/ subtrees (docs only)
  --json              Machine-readable findings (docs only)

Warnings are errors: every finding gates, with no advisory tier.

Examples:
  aa check
  aa check docs .
  aa check docs modules/check --json
  aa check skill"""


class CheckAction(ICheckAggregate):
    """CLI action surface for the check feature (surface layer, AES405 aggregate implementor)."""

    def __init__(self, orch: ICheckAggregate) -> None:
        self._orch = orch

    def check(self, only: CheckOnly | None = None) -> CheckExitCode:
        """Delegate check to the orchestrator, optionally scoped by *only*."""
        return self._orch.check(only=only)

    def check_docs(self) -> CheckExitCode:
        """Delegate docs check to the orchestrator."""
        return self._orch.check_docs()

    def check_skill(self) -> CheckExitCode:
        """Delegate skill check to the orchestrator."""
        return self._orch.check_skill()

    def summary(self, findings: list[DocFinding]) -> str:
        """Delegate summary generation to the orchestrator."""
        return self._orch.summary(findings)


def _docs_audit(
    target: str | None, *, include_subtrees: bool, json_mode: bool
) -> int:
    """Path/json/subtree document audit: ``aa check docs [path] [...]``.

    Strict is the default: every finding, warning included, is an error.
    """
    from modules.shared.src.utility_doc_hygiene import audit_hygiene
    from modules.shared.src.utility_doc_pack import (
        as_strict,
        audit_docs,
        errors_only,
        iter_doc_files,
    )
    from modules.shared.src.utility_logging_setup import err, info, ok
    from modules.shared.src.utility_paths_resolver import repo_root

    root = Path(target).resolve() if target else repo_root()
    if not root.is_dir():
        err(f"Not a directory: {root}")
        return 1
    if not json_mode:
        info(f"Auditing documents under {root} ...")
    scanned = len(iter_doc_files(root, include_subtrees=include_subtrees))
    findings = sorted(
        set(as_strict(
            audit_docs(root, include_subtrees=include_subtrees)
            + audit_hygiene(root, include_subtrees=include_subtrees)
        )),
        key=lambda f: (f.path, f.code, f.message),
    )
    problems = errors_only(findings)
    if json_mode:
        import json as _json
        out = {
            "scanned": scanned,
            "errors": [{"code": f.code, "path": f.path, "message": f.message} for f in problems],
            "warnings": [],
            "ok": not problems,
        }
        print(_json.dumps(out, indent=2, ensure_ascii=False))
        return 1 if problems else 0
    for finding in problems:
        err(f"{finding.code} {finding.path}: {finding.message}")
    print()
    if problems:
        err(f"{len(problems)} error(s) across {scanned} document(s) — "
            "a claim is in the wrong file, a pointer is broken, or a status assertion has no "
            "re-runnable evidence")
        return 1
    ok(f"{scanned} document(s) scanned: no errors")
    return 0


def cmd_check(args: list[str], orch: ICheckAggregate) -> int:
    """aa check [all|docs|skill] [path] [--include-subtrees] [--json]."""
    argv = list(args or [])
    if any(a in ("-h", "--help", "help") for a in argv):
        print(_USAGE)
        return 0
    include_subtrees = "--include-subtrees" in argv or "--include-submodules" in argv
    json_mode = "--json" in argv
    positional = [a for a in argv if not a.startswith("-")]
    if len(positional) > 2:
        print(_USAGE)
        return 1
    scope = (positional[0] if positional else "all").lower()
    if scope not in CHECK_SCOPES:
        print(f"Unknown check scope: {positional[0]!r}", flush=True)
        print(_USAGE)
        return 1
    docs_scope = scope in ("docs", "doc")
    target = positional[1] if len(positional) == 2 else None
    if target is not None and not docs_scope:
        print(_USAGE)
        return 1
    if not docs_scope and (json_mode or include_subtrees):
        print(_USAGE)
        return 1
    if docs_scope and (target is not None or json_mode or include_subtrees):
        return _docs_audit(
            target, include_subtrees=include_subtrees, json_mode=json_mode
        )
    only: CheckOnly | None = None if scope == "all" else CheckOnly(scope)
    banner()
    info("Running Python-based repository verification...")
    print()
    code = int(orch.check(only=only))
    print()
    if code:
        err(f"Verification FAILED with {code} errors.")
    else:
        ok("All verifications PASSED.")
    return code

__all__ = ['CheckAction', 'cmd_check']
