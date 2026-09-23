# Feature Backlog: check

FRD: [FRD.md](FRD.md)
Architecture: [ARCHITECTURE.md](../../ARCHITECTURE.md)
State: root § State Definitions
Health: root § State Definitions
Last Updated: 2026-09-18

## Current Condition

- Done: `CheckOrchestrator` + 2 check runners (docs, skills) + `ICheckRunner`/
  `ICheckAggregate` contracts; json/python/shell runners removed (delegated to
  CI + lint-arwaky); `aa check` → All verifications PASSED.
- In Progress: CHK-03 — FRD/BACKLOG pair authoring (this file).
- Blocked: none.
- Next Action: CHK-03 — close this pair; then CHK-01 strict sweep
  (`aa check --strict` currently has open warnings in `skills/` templates, out
  of P0 scope).

## Backlog

| ID | FRD Ref | Work Item | Priority | State | Actual Condition | Owner | Dependencies | Updated |
|----|---------|-----------|:---------|-------|------------------|-------|--------------|---------|
| CHK-01 | FR-001, FR-002 | Gate aggregation + doc-invariant audit | P0 | QA | `aa check` PASSED at `5556fd5` (non-strict). `--strict` sweep outstanding (skills-template warnings out of scope). | @raka | None | 2026-09-18 |
| CHK-02 | FR-002 | `aa docs check` invariant set wired into the gate | P0 | Done | docs runner present at `5556fd5`; `aa docs check .` → 107 docs scanned, 0 errors, 91 warnings at `5556fd5`. | @raka | None | 2026-09-18 |
| CHK-03 | FR-001–FR-002 | FRD + BACKLOG pair authoring for check | P0 | In Progress | Files written in this sweep. | @raka | None | 2026-09-18 |

## Scenario Evidence (rows)

| Scenario | Kind | Test file | Test name | Last verified |
|----------|------|-----------|-----------|---------------|
| `aa check` on a clean tree exits 0 and reports all verifications PASSED. | Proxy | manual | `python -m modules.root_cli_entry check` -> PASSED | `5556fd5` |
| `aa check` under `strict` fails when a warning-level finding exists. | Gap | — | — | `5556fd5` (no automated test yet) |
| A `Done` row without a commit hash is reported by `done-without-evidence`. | Proxy | `modules/check/src/capabilities_check_docs.py` | doc-pack `done-without-evidence` finding | `5556fd5` |
| The gate is read-only: no working-tree changes after it runs. | Gap | — | — | `5556fd5` (no automated test yet) |

## Blockers

None.

## Dependencies

Strict gate (CHK-01) depends on clearing `skills/research/.../templates` README
warnings — out of P0 scope, tracked at root if in scope later.

## Release Readiness

| Area | Status | Notes |
|------|--------|-------|
| Tests | QA | non-strict `aa check` PASSED at `5556fd5`; strict sweep outstanding |
| Type gate | Done | `aa check` at `5556fd5` |
| Docs | In Progress | CHK-03 (this pair) |

## Deferred

None.

## Change Log

| Date | Change | By |
|------|--------|----|
| 2026-09-18 | FRD/BACKLOG pair created during WS-04 doc sweep at `5556fd5`. | @raka |
| 2026-09-23 | Removed json/python/shell runners; gate now docs + skills only. | @raka |
