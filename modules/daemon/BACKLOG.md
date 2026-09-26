# Feature Backlog: daemon

FRD: [FRD.md](FRD.md)
Architecture: [ARCHITECTURE.md](../../ARCHITECTURE.md)
State / Health: values from root [ROADMAP.md](../../ROADMAP.md) — do not redefine here.
Last Updated: 2026-09-26

## Current Condition

- Done: `IDaemonProtocol` is a rich ABC — one named method per daemon
  operation (`start` / `stop` / `restart` / `status` / `logs` /
  `install_unit` / `remove_unit` / `unit_status`), each with its own typed
  return; no `execute(op, …)` dispatch bag. `IDaemonAggregate` keeps the
  single `execute(request) → response` entry point, and
  `DaemonOrchestrator` adds `known()` beside it. 4 FRs, 8 scenarios.
  Gate: `lint-arwaky-cli scan modules/daemon` → 0 violations;
  `python3 -m pytest modules/daemon -q` → 69 passed at `6df9f21`; deploy
  assets already shipped at `5556fd5`.
- In Progress: none (redesign slice complete).
- Blocked: none for docs/code; live Podman sweep still needs a container
  host and root WS-05 (secret location).
- Next Action: DMN-01 live sweep (start/status/auth on a Podman host);
  keep `check docs modules/daemon` green as the pair evolves.

## Backlog

| ID | FRD Ref | Work Item | Priority | State | Actual Condition | Owner | Dependencies | Updated |
|----|---------|-----------|:---------|-------|------------------|-------|--------------|---------|
| DMN-01 | FR-DAEMON-001, FR-DAEMON-002 | Daemon lifecycle + auth-key | P1 | QA | Protocol + capability paths in place; `python3 -m pytest modules/daemon -q` → 69 passed at `6df9f21`. Live Podman sweep outstanding (needs container host + WS-05). | @raka | WS-05 | 2026-09-26 |
| DMN-02 | FR-DAEMON-004 | Deploy assets (systemd units, Containerfile) | P1 | Done | `modules/daemon/deploy/` ships `anytype-daemon.service`, `9router.service`, `Containerfile` at `5556fd5`. | @raka | None | 2026-09-18 |
| DMN-03 | FR-DAEMON-001, FR-DAEMON-002, FR-DAEMON-003, FR-DAEMON-004 | FRD + BACKLOG pair authoring for daemon | P1 | Done | `check docs modules/daemon` → 0 findings (2 documents) at `f87a775`. | @raka | None | 2026-09-23 |
| DMN-04 | FR-DAEMON-001, FR-DAEMON-003, FR-DAEMON-004 | Rich per-operation `IDaemonProtocol` + single-`execute` aggregate | P0 | Done | `python3 -m compileall -q modules/daemon modules/shared` → 0 and `lint-arwaky-cli scan modules/daemon` → 0 violations at `6df9f21`; `IDaemonProtocol` declares one named method per operation (start/stop/restart/status/logs/install_unit/remove_unit/unit_status) instead of a single `execute`; `IDaemonAggregate.execute` remains the one entry point. | @raka | None | 2026-09-26 |

## Scenario Evidence

| Scenario | Kind | Test file | Test name | Last verified |
|----------|------|-----------|-----------|---------------|
| Starting an Anytype daemon that is already running reports it is already running and exits 0 without a second launch. | Manual | — | `aa anytype start` twice on a live Podman host | `5556fd5` |
| Starting a daemon on a host without Podman falls back to native execution or reports a clear non-zero error with no traceback. | Gap | — | not yet asserted on a Podman-less host | — |
| `auth-key` writes the generated key to XDG config only; the repo tree stays clean after the run. | Proxy | manual | `git status --porcelain` clean after `aa anytype auth-key` | `5556fd5` |
| `auth-key` while the daemon is stopped reports the pre-condition and exits non-zero instead of crashing. | Manual | — | `aa anytype auth-key` with container stopped | `5556fd5` |
| `list_known` returns both managed daemon ids (9router and anytype) independent of run state. | Proxy | manual | `DaemonOrchestrator.known()` → both ids | `6df9f21` |
| Enumerating daemons on a host where neither daemon is running still reports both ids. | Proxy | manual | `known()` with daemons stopped → both ids | `6df9f21` |
| `install_unit` for a daemon enables its user unit and a following `unit_status` reports it active. | Gap | — | not run on the user host (unit enable side effects) | — |
| `remove_unit` deletes a daemon's user unit so a following `unit_status` reports it not installed. | Gap | — | not run on the user host (unit remove side effects) | — |

Kind values: Automated, Proxy, Manual, Gap.

## Blockers

Live sweep (DMN-01) is blocked on a Podman host and root WS-05 (secret
location decision).

## Dependencies

WS-05 (live `.env`/XDG config decision) gates secret-backed auth flows.

## Release Readiness

| Area | Status | Notes |
|------|--------|-------|
| Tests | QA | `python3 -m pytest modules/daemon -q` → 69 passed and `lint-arwaky-cli scan modules/daemon` → 0 violations at `6df9f21`; live Podman sweep outstanding |
| Scenario evidence | QA | 8 of 8 scenarios mapped (3 Proxy, 2 Manual, 3 Gap) |
| Docs | Done | FRD rewritten to the approved redesign plan; pair matches HOW-TO (DMN-03) |

## Deferred

None.

## Change Log

| Date | Change | By |
|------|--------|----|
| 2026-09-18 | FRD/BACKLOG pair created during WS-04 doc sweep at `5556fd5`. | @raka |
| 2026-09-26 | Updated Current Condition, DMN-01/DMN-04 rows, scenario evidence, Release Readiness and Change Log to reflect `IDaemonProtocol` rich per-operation shape (start/stop/restart/status/logs/install_unit/remove_unit/unit_status), single-`execute` aggregate, 69 tests at `6df9f21`, 0 violations. | @raka |
| 2026-09-23 | FRD redesigned per approved plan: 4 FRs (adds FR-DAEMON-003 enum + FR-DAEMON-004 unit ops), Protocol API = single `execute`, aggregate expands to 9 methods, 8 scenarios; evidence reset to 8 rows; DMN-04 redesign row → Done at `f87a775`. | @raka |
