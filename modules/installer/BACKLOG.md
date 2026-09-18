# Feature Backlog: installer

FRD: [FRD.md](FRD.md)
Architecture: [ARCHITECTURE.md](../../ARCHITECTURE.md)
State: root § State Definitions
Health: root § State Definitions
Last Updated: 2026-09-18

## Current Condition

- Done: 14 per-tool `capabilities_*_installer.py` + registry-dispatch
  `agent_installer_orchestrator.py` + `IToolInstaller` contract at `5556fd5`;
  `python -c "import modules.installer.src"` OK at `5556fd5`; `aa check` PASSED
  at `5556fd5`. Excludes: live `.env` handling (root WS-05).
- In Progress: INS-03 — FRD/BACKLOG pair authoring (this file).
- Blocked: none.
- Next Action: INS-03 — close out this pair; then INS-01 verification sweep on a
  clean XDG host.

## Backlog

| ID | FRD Ref | Work Item | Priority | State | Actual Condition | Owner | Dependencies | Updated |
|----|---------|-----------|:---------|-------|------------------|-------|--------------|---------|
| INS-01 | FR-001 | Per-tool install capability for every manifest tool | P0 | QA | 14 capability modules present at `5556fd5`; import OK; `aa check` PASSED. Needs a clean-host install sweep to assert `aa tool install <id>` end-to-end. | @raka | None | 2026-09-18 |
| INS-02 | FR-002 | Registry-dispatch orchestrator (one capability per tool id) | P0 | Done | `agent_installer_orchestrator.py` routes by id; no per-tool `if` branches; verified by import + `aa check` at `5556fd5`. | @raka | None | 2026-09-18 |
| INS-03 | FR-001, FR-002 | FRD + BACKLOG pair authoring for installer | P0 | In Progress | Files written at `5556fd5` (this sweep). | @raka | None | 2026-09-18 |

## Scenario Evidence (rows)

| Scenario | Kind | Test file | Test name | Last verified |
|----------|------|-----------|-----------|---------------|
| Installing a known tool id on a clean host yields a working binary on PATH. | Proxy | manual | `aa tool install <id>` then `which <binary>` | `5556fd5` |
| Installing an unknown tool id fails with a typed error, not a crash. | Gap | — | — | `5556fd5` (no automated test yet) |
| Re-installing a satisfied tool id is idempotent. | Gap | — | — | `5556fd5` (no automated test yet) |

## Blockers

None.

## Dependencies

Root WS-05 (live `.env` location) gates any install that reads daemon secrets.

## Release Readiness

| Area | Status | Notes |
|------|--------|-------|
| Tests | QA | import + `aa check` green at `5556fd5`; clean-host install sweep outstanding |
| Type gate | Done | `aa check` includes compileall + JSON validation at `5556fd5` |
| Docs | In Progress | INS-03 (this pair) |

## Deferred

None.

## Change Log

| Date | Change | By |
|------|--------|----|
| 2026-09-18 | FRD/BACKLOG pair created during WS-04 doc sweep at `5556fd5`. | @raka |
