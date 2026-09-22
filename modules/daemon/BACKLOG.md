# Feature Backlog: daemon

FRD: [FRD.md](FRD.md)
Architecture: [ARCHITECTURE.md](../../ARCHITECTURE.md)
State: root § State Definitions
Health: root § State Definitions
Last Updated: 2026-09-18

## Current Condition

- Done: `IDaemonManager` contract + 2 daemon capabilities +
  `agent_daemon_orchestrator.py` + deploy assets (systemd units, Containerfile)
  at `5556fd5`; import OK; `aa check` PASSED at `5556fd5`.
- In Progress: DMN-03 — FRD/BACKLOG pair authoring (this file).
- Blocked: none.
- Next Action: DMN-03 — close this pair; then DMN-01 live sweep (needs a host
  with Podman + root WS-05 env decision for secrets).

## Backlog

| ID | FRD Ref | Work Item | Priority | State | Actual Condition | Owner | Dependencies | Updated |
|----|---------|-----------|:---------|-------|------------------|-------|--------------|---------|
| DMN-01 | FR-001, FR-002 | Daemon lifecycle + auth-key | P1 | QA | 2 capabilities + contract at `5556fd5`; import OK. Live Podman sweep outstanding (needs host + WS-05). | @raka | WS-05 | 2026-09-18 |
| DMN-02 | FR-001 | Deploy assets (systemd units, Containerfile) | P1 | Done | `modules/daemon/deploy/` ships `anytype-daemon.service`, `omniroute.service`, `Containerfile` at `5556fd5`. | @raka | None | 2026-09-18 |
| DMN-03 | FR-001, FR-002 | FRD + BACKLOG pair authoring for daemon | P1 | In Progress | Files written in this sweep. | @raka | None | 2026-09-18 |

## Scenario Evidence (rows)

| Scenario | Kind | Test file | Test name | Last verified |
|----------|------|-----------|-----------|---------------|
| `aa anytype start` on a host with Podman brings the container up; `status` reports running. | Manual | — | `aa anytype start` + `aa anytype status` (live Podman host) | `5556fd5` |
| `aa anytype status` when the daemon is absent reports unknown, exit 0. | Manual | — | `aa anytype status` on a clean host | `5556fd5` |
| `auth-key` writes the key to XDG config and never to the repo tree. | Proxy | manual | `git status --porcelain` clean after `aa anytype auth-key` | `5556fd5` |

## Blockers

Live sweep (DMN-01) is blocked on a Podman host and root WS-05 (secret location).

## Dependencies

WS-05 (live `.env`/XDG config decision) gates secret-backed flows.

## Release Readiness

| Area | Status | Notes |
|------|--------|-------|
| Tests | QA | import + `aa check` at `5556fd5`; live sweep outstanding |
| Type gate | Done | `aa check` at `5556fd5` |
| Docs | In Progress | DMN-03 (this pair) |

## Deferred

None.

## Change Log

| Date | Change | By |
|------|--------|----|
| 2026-09-18 | FRD/BACKLOG pair created during WS-04 doc sweep at `5556fd5`. | @raka |
