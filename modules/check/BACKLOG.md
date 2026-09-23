# Feature Backlog: check

FRD: [FRD.md](FRD.md)
Architecture: [ARCHITECTURE.md](../../ARCHITECTURE.md)
State / Health: values from root [BACKLOG.md](../../BACKLOG.md) — do not redefine here.
Last Updated: 2026-09-23

## Current Condition

- Done: `CheckOrchestrator` + 2 runners (docs, skill) with CLI keys +
  `ICheckRunner.name` / `ICheckAggregate.check(only=…)`; standard scopes
  `aa check`, `aa check docs`, `aa check skill` live on the check surface;
  `aa check docs [path]` carries path/json/subtree flags; FRD IDs `FR-CHECK-001/002`;
  strict FRD template gate active (`check_frd_template`);
  **strict-only mode** — `strict` parameter removed from contracts/runners,
  engine promotes every finding at exit (`as_strict`), no `--strict` flag,
  no advisory tier; full-tree gate green (0 findings).
- In Progress: none (pair + surface alignment complete for this slice).
- Blocked: none.
- Next Action: keep `aa check` green as docs evolve (CHK-01 closed).

## Backlog

| ID | FRD Ref | Work Item | Priority | State | Actual Condition | Owner | Dependencies | Updated |
|----|---------|-----------|:---------|-------|------------------|-------|--------------|---------|
| CHK-01 | FR-CHECK-001, FR-CHECK-002 | Gate aggregation + docs + skills runners | P0 | Done | Gate: `python3 -m modules.root_cli_entry check` → 0 findings (strict-only; `as_strict` at exit; no `--strict` flag, no advisory tier) at `fffcd17`. | @raka | None | 2026-09-23 |
| CHK-02 | FR-CHECK-001 | Document invariant audit (`aa check docs`) | P0 | Done | Gate: `python3 -m modules.root_cli_entry check docs` → 0 findings (123 docs scanned) at `fffcd17`. | @raka | None | 2026-09-23 |
| CHK-04 | FR-CHECK-002 | Skill-pack loadability runner (`aa check skill`) | P0 | Done | `aa check skill` → PASSED, 92 skills loadable at `fffcd17`. | @raka | None | 2026-09-23 |
| CHK-03 | FR-CHECK-001–FR-CHECK-002 | FRD + BACKLOG pair authoring / template alignment for check | P0 | Done | `aa check docs modules/check` → 0 FR/template errors at `fffcd17`; `check_frd_template` clean. | @raka | None | 2026-09-23 |
| CHK-05 | FR-CHECK-001, FR-CHECK-002 | Standard CLI scopes `aa check docs` / `aa check skill` | P0 | Done | `aa check skill` + `aa check docs` smoke scopes at `fffcd17`; unknown scope → usage exit 1. | @raka | None | 2026-09-23 |

## Scenario Evidence

| Scenario | Kind | Test file | Test name | Last verified |
|----------|------|-----------|-----------|---------------|
| `aa check` on a clean tree exits 0 and reports all verifications PASSED. | Proxy | manual | `python -m modules.root_cli_entry check` → PASSED (0 findings, strict-only) | `fffcd17` |
| `aa check` fails when any finding exists (strict-only; no advisory tier). | Proxy | manual | inject finding → exit 1; clean tree → exit 0 | `fffcd17` |
| `aa check docs` runs only the document-invariant runner and skips skill audit. | Proxy | manual | `python -m modules.root_cli_entry check docs` → `[1/1]` docs only | `fffcd17` |
| `aa check skill` runs only the skill-pack runner and skips doc audit. | Proxy | manual | `python -m modules.root_cli_entry check skill` → `[1/1]` skill only | `fffcd17` |
| `aa check --bogus` (unknown scope) prints usage and exits non-zero. | Proxy | `modules/check/src/surface_check_command.py` | unknown-scope path in `cmd_check` | `fffcd17` |
| A `Done` row without a commit hash is reported by `done-without-evidence`. | Proxy | `modules/check/src/capabilities_check_docs.py` | doc-pack `done-without-evidence` finding | `30b61c8` |
| The gate is read-only: no working-tree changes after it runs. | Gap | — | — | not yet |
| `aa check` runs docs first then skills (`[1/2]`, `[2/2]`) before the summary. | Proxy | manual | full gate → both step titles | `fffcd17` |
| A skill at the wrong nesting depth is reported by `nested-layout` and fails the gate. | Gap | — | — | not yet |
| A skill whose frontmatter `name` differs from its folder is reported by `name-mismatch` and fails the gate. | Gap | — | — | not yet |
| `aa check docs [path] --json` emits machine-readable `errors` / `warnings` arrays without the human banner. | Proxy | `modules/check/src/surface_check_command.py` | `_docs_audit` json branch | `fffcd17` |

Kind values: Automated, Proxy, Manual, Gap.

## Blockers

None.

## Dependencies

None — strict gate (CHK-01) is closed; research-template README findings cleared.

## Release Readiness

| Area | Status | Notes |
|------|--------|-------|
| Tests | Done | Strict-only `aa check` / `aa check docs` / `aa check skill` all PASSED (0 findings) |
| Scenario evidence | Done | 11 of 11 scenarios mapped (9 Proxy, 2 Gap) |
| Docs | Done | CHK-03 + CHK-05 — pair matches HOW-TO; standard scopes live |

## Deferred

None.

## Change Log

| Date | Change | By |
|------|--------|----|
| 2026-09-18 | FRD/BACKLOG pair created during WS-04 doc sweep at `5556fd5`. | @raka |
| 2026-09-23 | Removed json/python/shell runners; gate now docs + skills only. | @raka |
| 2026-09-23 | Deleted dead `capabilities_doc_pack.py`; rewired `aa docs` to `utility_doc_pack`. | @raka |
| 2026-09-23 | Realigned this pair to HOW-TO-MAKE-{FRD,BACKLOG} golden templates. | @raka |
| 2026-09-23 | Collapsed aggregation into System Overview; FRs = 2 capabilities (docs, skills); IDs renamed per HOW-TO Rule 1 → `FR-CHECK-001`/`FR-CHECK-002`. | @raka |
| 2026-09-23 | Strict FRD template gate (`check_frd_template`); standard CLI scopes `aa check docs` / `aa check skill` (CHK-05). | @raka |
| 2026-09-23 | Realigned all 10 feature FRDs to HOW-TO: `FR-<FEATURE>-NNN` IDs, 6-col API tables, Integration/NFR shapes, tools six-fields; `aa check docs` → 0 errors. | @raka |
| 2026-09-23 | Removed the `aa docs` noun; `aa check docs [path]` now owns path/json/subtree flags (surface `_docs_audit`). | @raka |
| 2026-09-23 | Strict-only mode: `strict` param removed from contracts/runners; engine `as_strict` at exit; dead `_check_docs`/`_check_skill_pack` helpers deleted from `root_cli_entry`; CHK-01 → Done (0 findings). | @raka |
