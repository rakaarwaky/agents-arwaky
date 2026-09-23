# Feature Backlog: daemon

FRD: [FRD.md](FRD.md)
Architecture: [ARCHITECTURE.md](../../ARCHITECTURE.md)
State / Health: values from root [ROADMAP.md](../../ROADMAP.md) — do not redefine here.
Last Updated: 2026-09-23

## Current Condition

- Done: FRD/BACKLOG redesigned per the approved plan — single-execute
  protocol, 9-method aggregate (`list_known` + lifecycle + unit ops),
  4 FRs, 8 scenarios; `check docs modules/daemon` → 0 findings and
  `compileall` clean at `f87a775`; deploy assets already shipped at
  `5556fd5`.
- In Progress: none (redesign slice complete).
- Blocked: none for docs/code; live Podman sweep still needs a container
  host and root WS-05 (secret location).
- Next Action: DMN-01 live sweep (start/status/auth on a Podman host);
  keep `check docs modules/daemon` green as the pair evolves.

## Backlog

| ID | FRD Ref | Work Item | Priority | State | Actual Condition | Owner | Dependencies | Updated |
|----|---------|-----------|:---------|-------|------------------|-------|--------------|---------|
| DMN-01 | FR-DAEMON-001, FR-DAEMON-002 | Daemon lifecycle + auth-key | P1 | QA | Protocol + capability paths in place; import OK. Live Podman sweep outstanding (needs container host + WS-05). | @raka | WS-05 | 2026-09-23 |
| DMN-02 | FR-DAEMON-004 | Deploy assets (systemd units, Containerfile) | P1 | Done | `modules/daemon/deploy/` ships `anytype-daemon.service`, `omniroute.service`, `Containerfile` at `5556fd5`. | @raka | None | 2026-09-18 |
| DMN-03 | FR-DAEMON-001, FR-DAEMON-002, FR-DAEMON-003, FR-DAEMON-004 | FRD + BACKLOG pair authoring for daemon | P1 | Done | `check docs modules/daemon` → 0 findings (2 documents) at `f87a775`. | @raka | None | 2026-09-23 |
| DMN-04 | FR-DAEMON-001, FR-DAEMON-003, FR-DAEMON-004 | Single-execute protocol + 9-method aggregate redesign | P0 | Done | `python3 -m compileall -q modules/daemon modules/service modules/shared` → 0 at `f87a775`; `IDaemonProtocol.execute` replaces 5 leaf protocols; aggregate exposes `list_known`/`start`/`stop`/`restart`/`status`/`logs`/`install_unit`/`remove_unit`/`unit_status`. | @raka | None | 2026-09-23 |

## Scenario Evidence

| Scenario | Kind | Test file | Test name | Last verified |
|----------|------|-----------|-----------|---------------|
| Starting an Anytype daemon that is already running reports it is already running and exits 0 without a second launch. | Manual | — | `aa anytype start` twice on a live Podman host | `5556fd5` |
| Starting a daemon on a host without Podman falls back to native execution or reports a clear non-zero error with no traceback. | Gap | — | not yet asserted on a Podman-less host | — |
| `auth-key` writes the generated key to XDG config only; the repo tree stays clean after the run. | Proxy | manual | `git status --porcelain` clean after `aa anytype auth-key` | `5556fd5` |
| `auth-key` while the daemon is stopped reports the pre-condition and exits non-zero instead of crashing. | Manual | — | `aa anytype auth-key` with container stopped | `5556fd5` |
| `list_known` returns both managed daemon ids (omniroute and anytype) independent of run state. | Proxy | manual | `DaemonOrchestrator.list_known()` → both ids | `f87a775` |
| Enumerating daemons on a host where neither daemon is running still reports both ids. | Proxy | manual | `list_known()` with daemons stopped → both ids | `f87a775` |
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
| Tests | QA | `compileall` + `check docs modules/daemon` → 0 findings at `f87a775`; live sweep outstanding |
| Scenario evidence | QA | 8 of 8 scenarios mapped (3 Proxy, 2 Manual, 3 Gap) |
| Docs | Done | FRD rewritten to the approved redesign plan; pair matches HOW-TO (DMN-03) |

## Deferred

None.

## Change Log

| Date | Change | By |
|------|--------|----|
| 2026-09-18 | FRD/BACKLOG pair created during WS-04 doc sweep at `5556fd5`. | @raka |
| 2026-09-23 | FRD redesigned per approved plan: 4 FRs (adds FR-DAEMON-003 enum + FR-DAEMON-004 unit ops), Protocol API = single `execute`, aggregate expands to 9 methods, 8 scenarios; evidence reset to 8 rows; DMN-04 redesign row → Done at `f87a775`. | @raka |
