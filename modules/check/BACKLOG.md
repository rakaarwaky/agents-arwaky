# Feature Backlog: check

FRD: [FRD.md](FRD.md)
Architecture: [ARCHITECTURE.md](../../ARCHITECTURE.md)
State / Health: values from root [BACKLOG.md](../../BACKLOG.md) — do not redefine here.
Last Updated: 2026-09-23

## Current Condition

- Done: `CheckOrchestrator` + 2 runners (docs `[1/2]`, skills `[2/2]`) +
  `ICheckRunner` / `ICheckAggregate`; `capabilities_doc_pack.py` deleted
  (facade was dead — `DocPackRunner` never in runners; `aa docs` imports
  `utility_doc_pack` directly); `aa check` → All verifications PASSED at
  `30b61c8`.
- In Progress: CHK-03 — FRD/BACKLOG pair alignment to the latest
  HOW-TO-MAKE-* templates (this file).
- Blocked: none.
- Next Action: CHK-01 strict sweep — `aa check --strict` still has advisory
  warnings under `skills/` templates (out of P0 scope).

## Backlog

| ID | FRD Ref | Work Item | Priority | State | Actual Condition | Owner | Dependencies | Updated |
|----|---------|-----------|:---------|-------|------------------|-------|--------------|---------|
| CHK-01 | FR-001, FR-002, FR-003 | Gate aggregation + docs + skills runners | P0 | QA | `aa check` PASSED at `30b61c8` (non-strict). `--strict` sweep outstanding (skills-template warnings out of scope). | @raka | None | 2026-09-23 |
| CHK-02 | FR-002 | `aa docs check` invariant set wired into the gate | P0 | Done | docs runner present at `5556fd5`; `aa docs check .` → 0 errors at `30b61c8`. | @raka | None | 2026-09-23 |
| CHK-04 | FR-003 | Skill-pack loadability runner (`[2/2]`) | P0 | Done | `SkillsCheckRunner` + `audit_pack` in gate; `aa check` prints `[2/2] … 92 skills … loadable` at `30b61c8`. | @raka | None | 2026-09-23 |
| CHK-03 | FR-001–FR-003 | FRD + BACKLOG pair authoring / template alignment for check | P0 | In Progress | Pair rewritten against HOW-TO-MAKE-{FRD,BACKLOG}; sections + columns gated clean at `30b61c8`. | @raka | None | 2026-09-23 |

## Scenario Evidence

| Scenario | Kind | Test file | Test name | Last verified |
|----------|------|-----------|-----------|---------------|
| `aa check` on a clean tree exits 0 and reports all verifications PASSED. | Proxy | manual | `python -m modules.root_cli_entry check` → PASSED | `30b61c8` |
| `aa check` under `strict` fails when a warning-level finding exists. | Gap | — | — | `30b61c8` (no automated test yet) |
| A `Done` row without a commit hash is reported by `done-without-evidence`. | Proxy | `modules/check/src/capabilities_check_docs.py` | doc-pack `done-without-evidence` finding | `30b61c8` |
| The gate is read-only: no working-tree changes after it runs. | Gap | — | — | `30b61c8` (no automated test yet) |
| `aa check` runs docs as `[1/2]` then skills as `[2/2]` before the summary. | Proxy | manual | `python -m modules.root_cli_entry check` → both steps printed | `30b61c8` |
| A skill at the wrong nesting depth is reported by `nested-layout` and fails the gate. | Gap | — | — | `30b61c8` (no automated test yet) |
| A skill whose frontmatter `name` differs from its folder is reported by `name-mismatch` and fails the gate. | Gap | — | — | `30b61c8` (no automated test yet) |
| `aa docs check --json` emits machine-readable `errors` / `warnings` arrays without the human banner. | Gap | — | — | `30b61c8` (no automated test yet) |

Kind values: Automated, Proxy, Manual, Gap.

## Blockers

None.

## Dependencies

Strict gate (CHK-01) depends on clearing `skills/research/.../templates`
README warnings — out of P0 scope, tracked at root if in scope later.

## Release Readiness

| Area | Status | Notes |
|------|--------|-------|
| Tests | QA | non-strict `aa check` PASSED at `30b61c8`; strict sweep outstanding |
| Scenario evidence | Done | 8 of 8 scenarios mapped (3 Proxy, 5 Gap) |
| Docs | In Progress | CHK-03 (this pair) |

## Deferred

None.

## Change Log

| Date | Change | By |
|------|--------|----|
| 2026-09-18 | FRD/BACKLOG pair created during WS-04 doc sweep at `5556fd5`. | @raka |
| 2026-09-23 | Removed json/python/shell runners; gate now docs + skills only. | @raka |
| 2026-09-23 | Deleted dead `capabilities_doc_pack.py`; rewired `aa docs` to `utility_doc_pack`. | @raka |
| 2026-09-23 | Realigned this pair to HOW-TO-MAKE-{FRD,BACKLOG} golden templates. | @raka |
