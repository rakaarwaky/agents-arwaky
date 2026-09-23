# Feature Backlog: doctor

FRD: [FRD.md](FRD.md)
Architecture: [ARCHITECTURE.md](../../ARCHITECTURE.md)
State: root § State Definitions
Health: root § State Definitions
Last Updated: 2026-09-18

## Current Condition

- Done: `DoctorOrchestrator` + 2 diagnostic runners (`env`, `tools`) + `IDiagnosticRunner` contract at `5556fd5`; import OK; `aa check` PASSED at `5556fd5`.
- In Progress: doctor-03 — FRD/BACKLOG pair authoring (this file).
- Blocked: none.
- Next Action: close this pair; then DOC-01 sweep (`aa doctor` on this host).

## Backlog

| ID | FRD Ref | Work Item | Priority | State | Actual Condition | Owner | Dependencies | Updated |
|----|---------|-----------|:---------|-------|------------------|-------|--------------|---------|
| DOC-01 | FR-DOCTOR-001, FR-DOCTOR-002 | Env + tools diagnostic runners | P1 | QA | 2 runners present at `5556fd5`; import OK; `aa check` PASSED. Live `aa doctor` sweep outstanding. | @raka | None | 2026-09-18 |
| DOC-02 | FR-DOCTOR-001 | Bounded, read-only probes | P1 | Done | per-probe timeout + no-mutation semantics at `5556fd5`. | @raka | None | 2026-09-18 |
| DOC-03 | FR-DOCTOR-001, FR-DOCTOR-002 | FRD + BACKLOG pair authoring for doctor | P1 | In Progress | Files written in this sweep. | @raka | None | 2026-09-18 |

## Scenario Evidence (rows)

| Scenario | Kind | Test file | Test name | Last verified |
|----------|------|-----------|-----------|---------------|
| `aa doctor` on a healthy host prints all-PASS and exits 0. | Proxy | manual | `python -m modules.root_cli_entry doctor` on this host | `5556fd5` |
| `aa doctor` with a missing toolchain marks that row FAIL (exit 0; row-level only). | Gap | — | — | `5556fd5` (no automated test yet) |
| The run is read-only: no package is installed and no file is written. | Gap | — | — | `5556fd5` (no automated test yet) |

## Blockers

None.

## Dependencies

None.

## Release Readiness

| Area | Status | Notes |
|------|--------|-------|
| Tests | QA | import + `aa check` at `{C}`; live sweep outstanding |
| Type gate | Done | `aa check` at `{C}` |
| Docs | In Progress | DOC-03 (this pair) |

## Deferred

None.

## Change Log

| Date | Change | By |
|------|--------|----|
| 2026-09-18 | FRD/BACKLOG pair created during WS-04 doc sweep at `5556fd5`. | @raka |
