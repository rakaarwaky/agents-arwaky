# Feature Backlog: cli

FRD: [FRD.md](FRD.md)
Architecture: [ARCHITECTURE.md](../../ARCHITECTURE.md)
State: root § State Definitions
Health: root § State Definitions
Last Updated: 2026-09-18

## Current Condition

- Done: entry point `modules/root_cli_entry.py` + 13 surface modules under
  `modules/cli/src/` at `5556fd5`; surface consolidation (root WS-03) complete —
  zero surface files outside `modules/cli/src/`; `python -m modules.root_cli_entry
  tool run ponytail` → exit 0 at `5556fd5`. CI entry-point reference still
  stale (root WS-08).
- In Progress: CLI-03 — FRD/BACKLOG pair authoring (this file).
- Blocked: none.
- Next Action: CLI-03 — close this pair; then root WS-08 (fix `ci.yml` to
  `python3 -m modules.root_cli_entry check`).

## Backlog

| ID | FRD Ref | Work Item | Priority | State | Actual Condition | Owner | Dependencies | Updated |
|----|---------|-----------|:---------|-------|------------------|-------|--------------|---------|
| CLI-01 | FR-001 | Verb dispatch entry point (`root_cli_entry.py`) | P0 | Done | `python -m modules.root_cli_entry tool run ponytail` → exit 0 at `5556fd5`; `aa check` PASSED at `5556fd5`. | @raka | None | 2026-09-18 |
| CLI-02 | FR-002 | Surface modules confined to `modules/cli/src/` | P0 | Done | `find modules -name 'surface_*.py'` → all 13 under `modules/cli/src/` at `5556fd5` (WS-03). | @raka | None | 2026-09-18 |
| CLI-03 | FR-001, FR-002 | FRD + BACKLOG pair authoring for cli | P0 | In Progress | Files written in this sweep. | @raka | None | 2026-09-18 |

## Scenario Evidence

| Scenario | Kind | Test file | Test name | Last verified |
|----------|------|-----------|-----------|---------------|
| `tool run` on an installed tool exits 0 | Proxy | manual | `python -m modules.root_cli_entry tool run ponytail` → 0 | `5556fd5` |
| No surface file outside `modules/cli/src/` | Proxy | manual | `find modules -name 'surface_*.py'` → all under cli | `5556fd5` |
| Unknown verb prints usage, no traceback | Gap | — | — | `5556fd5` (no automated test yet) |

## Blockers

None.

## Dependencies

Root WS-08 (CI entry-point fix) is a downstream of this feature's CLI-01.

## Release Readiness

| Area | Status | Notes |
|------|--------|-------|
| Tests | QA | `tool run` + surface-locality verified at `5556fd5`; verb-coverage sweep outstanding |
| Type gate | Done | `aa check` at `5556fd5` |
| Docs | In Progress | CLI-03 (this pair) |

## Deferred

None.

## Change Log

| Date | Change | By |
|------|--------|----|
| 2026-09-18 | Entry point flattened to `modules/root_cli_entry.py` (`fdf5faf`); FRD/BACKLOG pair created during WS-04 sweep at `5556fd5`. | @raka |
