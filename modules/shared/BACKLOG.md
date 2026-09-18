# Feature Backlog: shared

FRD: [FRD.md](FRD.md)
Architecture: [ARCHITECTURE.md](../../ARCHITECTURE.md)
State: root § State Definitions
Health: root § State Definitions
Last Updated: 2026-09-18

## Current Condition

- Done: flat kernel at `5556fd5` — 24 modules at `modules/shared/src/` root
  (taxonomies + utilities), zero sub-folders; no `contract_*` lifecycle files
  (decentralized to feature modules at `33ee506`/`58fc552`); import OK across
  16 feature packages at `5556fd5`; `aa check` PASSED at `5556fd5`.
- In Progress: SHR-03 — FRD/BACKLOG pair authoring (this file).
- Blocked: none.
- Next Action: SHR-03 — close this pair; then SHR-01 sweep (XDG + manifest
  read paths under `tests/`).

## Backlog

| ID | FRD Ref | Work Item | Priority | State | Actual Condition | Owner | Dependencies | Updated |
|----|---------|-----------|:---------|-------|------------------|-------|--------------|---------|
| SHR-01 | FR-001, FR-002, FR-003 | Path/manifest/XDG utility contracts stable and tested | P0 | QA | 24 flat modules at `5556fd5`; import OK; `aa check` PASSED. Unit coverage in `tests/` (`test_envfile`, `test_manifest`, `test_xdg`) outstanding as a migrated suite (root WS-06). | @raka | None | 2026-09-18 |
| SHR-02 | FR-001 | `repo_root()` anchor discovery + `AGENTS_ARWAKY_ROOT` hint | P0 | Done | `utility_paths.py` at `5556fd5`; honored by every module's root resolution. | @raka | None | 2026-09-18 |
| SHR-03 | FR-001–FR-003 | FRD + BACKLOG pair authoring for shared | P0 | In Progress | Files written in this sweep. | @raka | None | 2026-09-18 |

## Scenario Evidence

| Scenario | Kind | Test file | Test name | Last verified |
|----------|------|-----------|-----------|---------------|
| `load_tools()` parses manifest | Proxy | `tests/test_manifest.py` | manifest reader assertions | `5556fd5` |
| XDG helpers honor env override | Proxy | `tests/test_xdg.py` | xdg path assertions | `5556fd5` |
| `repo_root()` in a worktree | Gap | — | — | `5556fd5` (no automated test yet) |

## Blockers

None.

## Dependencies

SHR-01's migrated suite is gated by root WS-06 (test migration) — deferred until
after the P0 merge.

## Release Readiness

| Area | Status | Notes |
|------|--------|-------|
| Tests | QA | `tests/` has manifest/xdg/envfile coverage at `5556fd5`; full migrated suite outstanding (WS-06) |
| Type gate | Done | `aa check` at `5556fd5` |
| Docs | In Progress | SHR-03 (this pair) |

## Deferred

None.

## Change Log

| Date | Change | By |
|------|--------|----|
| 2026-09-18 | FRD/BACKLOG pair created during WS-04 doc sweep at `5556fd5`. | @raka |
