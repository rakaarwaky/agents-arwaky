# Feature Backlog: doctor

FRD: [FRD.md](FRD.md)
Architecture: [ARCHITECTURE.md](../../ARCHITECTURE.md)
State / Health: values from root [ROADMAP.md](../../ROADMAP.md) — do not redefine here.
Last Updated: 2026-09-26

## Current Condition

- Done: `IDoctorProtocol` stays a one-method capability ABC (`run(flags)`
  under the `json` / `mode` flags VO) — one diagnostic pass, one exit code.
  `IDoctorAggregate` keeps the single `execute(request) → response` entry
  point; `DoctorOrchestrator` fans the request out to the env and tools
  runners. Gate: `lint-arwaky-cli scan modules/doctor` → 0 violations;
  `python3 -m pytest modules/doctor -q` → 29 passed at `6df9f21`; live
  `aa doctor` / `aa status` sweeps on this host exit 0.
- In Progress: none.
- Blocked: none.
- Next Action: DOC-03/DOC-04 closed; port the missing-toolchain scenario
  (Gap) to an automated test when the `modules/tests/` port lands (WS-06).

## Backlog

| ID | Priority | State | Dependencies | Next Action | Updated |
|---|---|---|---|---|---|
| DOC-01 | P1 | Done | None | none | 2026-09-26 |
| DOC-02 | P1 | Done | None | none | 2026-09-26 |
| DOC-03 | P1 | Done | None | none | 2026-09-26 |
| DOC-04 | P1 | Done | DOC-03 | none | 2026-09-26 |

## Scenario Evidence

| Scenario | Kind | Test file | Test name | Last verified |
|----------|------|-----------|-----------|---------------|
| `aa doctor` on a healthy host prints all-PASS and exits 0. | Proxy | manual | `python -m modules.root_cli_entry doctor` on this host | `6df9f21` |
| `aa doctor` with a missing toolchain marks that row FAIL while the process still exits 0. | Gap | — | — | not yet |
| `aa status` lists every manifest tool with a readiness state and exits 0. | Proxy | manual | `python -m modules.root_cli_entry status` on this host | `6df9f21` |
| `aa status --json` emits parseable JSON rows with stable keys for every tool. | Proxy | manual | `python -m modules.root_cli_entry status --json` → `json.loads` + keys `id,category,binary,status` | `6df9f21` |

Kind values: Automated, Proxy, Manual, Gap.

## Blockers

None.

## Dependencies

None.

## Release Readiness

| Area | Status | Notes |
|------|--------|-------|
| Tests | Done | `python3 -m pytest modules/doctor -q` → 29 passed and `lint-arwaky-cli scan modules/doctor` → 0 violations at `6df9f21`; live doctor/status sweeps exit 0 on this host |
| Scenario evidence | Done | 4 of 4 scenarios mapped (3 Proxy, 1 Gap) |
| Docs | Done | [FRD.md](FRD.md) is specification-only; pair redesigned per approved plan |

## Deferred

None.

## Change Log

| Date | Change | By |
|------|--------|----|
| 2026-09-26 | Updated Current Condition, DOC-01/02/03/04 rows, scenario evidence, Release Readiness and Change Log to reflect the one-method `IDoctorProtocol.run` + single-`execute` aggregate, 29 tests at `6df9f21`, 0 violations. | @raka |
| 2026-09-18 | FRD/BACKLOG pair created during WS-04 doc sweep at `5556fd5`. | @raka |
| 2026-09-23 | Redesigned pair per approved plan: Protocol API = 1 row `run`; aggregate = single `execute`; 4 scenarios ↔ 4 evidence rows; code renamed (protocol, aggregate, orchestrator, runners, surface, root CLI `.diagnose`); gates re-run at `f87a775` (working tree). | @raka |
