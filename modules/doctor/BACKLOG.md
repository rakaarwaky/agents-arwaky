# Feature Backlog: doctor

FRD: [FRD.md](FRD.md)
Architecture: [ARCHITECTURE.md](../../ARCHITECTURE.md)
State / Health: values from root [BACKLOG.md](../../BACKLOG.md) — do not redefine here.
Last Updated: 2026-09-23

## Current Condition

- Done: pair redesigned to the 1-row protocol `execute` + aggregate
  `diagnose`/`readiness`/`report`; code renamed to match (protocol,
  aggregate, orchestrator, runners, surface, root CLI call site);
  `python3 -m compileall -q modules/doctor modules/shared` → clean;
  live `aa doctor` / `aa status` sweeps on this host exit 0 (working tree
  atop `f87a775`).
- In Progress: none.
- Blocked: none.
- Next Action: DOC-03/DOC-04 closed; port the missing-toolchain scenario
  (Gap) to an automated test when the `modules/tests/` port lands (WS-06).

## Backlog

| ID | FRD Ref | Work Item | Priority | State | Actual Condition | Owner | Dependencies | Updated |
|----|---------|-----------|----------|-------|------------------|-------|--------------|---------|
| DOC-01 | FR-DOCTOR-001, FR-DOCTOR-002 | Env + tools diagnostic runners | P1 | Done | Gate: `python3 -m modules.root_cli_entry doctor` → exit 0 (all-PASS) + `... status --json` → 13 rows, stable keys on this host at `f87a775` (working tree). | @raka | None | 2026-09-23 |
| DOC-02 | FR-DOCTOR-001 | Bounded, read-only probes | P1 | Done | Gate: `git status --porcelain` unchanged after `python3 -m modules.root_cli_entry doctor` at `f87a775` (working tree). | @raka | None | 2026-09-23 |
| DOC-03 | FR-DOCTOR-001, FR-DOCTOR-002 | FRD + BACKLOG pair authoring / redesign for doctor | P1 | Done | Gate: `python3 -m modules.root_cli_entry check docs modules/doctor` → 0 findings at `f87a775` (working tree). | @raka | None | 2026-09-23 |
| DOC-04 | FR-DOCTOR-001, FR-DOCTOR-002 | Protocol `execute` + aggregate `diagnose`/`readiness`/`report` rename | P1 | Done | Gate: `python3 -m compileall -q modules/doctor modules/shared` → clean; aggregate smoke (diagnose/readiness/report) → 0 at `f87a775` (working tree). | @raka | DOC-03 | 2026-09-23 |

## Scenario Evidence

| Scenario | Kind | Test file | Test name | Last verified |
|----------|------|-----------|-----------|---------------|
| `aa doctor` on a healthy host prints all-PASS and exits 0. | Proxy | manual | `python -m modules.root_cli_entry doctor` on this host | `f87a775` (working tree) |
| `aa doctor` with a missing toolchain marks that row FAIL while the process still exits 0. | Gap | — | — | not yet |
| `aa status` lists every manifest tool with a readiness state and exits 0. | Proxy | manual | `python -m modules.root_cli_entry status` on this host | `f87a775` (working tree) |
| `aa status --json` emits parseable JSON rows with stable keys for every tool. | Proxy | manual | `python -m modules.root_cli_entry status --json` → `json.loads` + keys `id,category,binary,status` | `f87a775` (working tree) |

Kind values: Automated, Proxy, Manual, Gap.

## Blockers

None.

## Dependencies

None.

## Release Readiness

| Area | Status | Notes |
|------|--------|-------|
| Tests | Done | `compileall modules/doctor modules/shared` → clean; live doctor/status sweeps exit 0 on this host |
| Scenario evidence | Done | 4 of 4 scenarios mapped (3 Proxy, 1 Gap) |
| Docs | Done | [FRD.md](FRD.md) is specification-only; pair redesigned per approved plan |

## Deferred

None.

## Change Log

| Date | Change | By |
|------|--------|----|
| 2026-09-18 | FRD/BACKLOG pair created during WS-04 doc sweep at `5556fd5`. | @raka |
| 2026-09-23 | Redesigned pair per approved plan: Protocol API = 1 row `execute`; aggregate = `diagnose`/`readiness`/`report`; 4 scenarios ↔ 4 evidence rows; code renamed (protocol, aggregate, orchestrator, runners, surface, root CLI `.diagnose`); gates re-run at `f87a775` (working tree). | @raka |
