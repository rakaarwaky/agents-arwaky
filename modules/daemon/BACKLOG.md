# Feature Backlog: daemon

FRD: [FRD.md](FRD.md)
Architecture: [ARCHITECTURE.md](../../ARCHITECTURE.md)
State / Health: values from root [ROADMAP.md](../../ROADMAP.md) — do not redefine here.
Last Updated: 2026-10-26

## Current Condition

- Done: `IDaemonProtocol` is a rich ABC with typed lifecycle, authorization,
  and unit methods; `IDaemonAggregate.execute(request)` routes shared
  operations, and `DaemonOrchestrator.known()` enumerates every supported
  id (`anytype`, `omniroute`, `9router`). The FRD now separates lifecycle,
  XDG authorization, enumeration, and unit requirements. Gate: `./.venv/bin/python -m pytest modules/daemon -q`
  → 71 passed and `./.venv/bin/ruff check modules/daemon --ignore E501` →
  clean at `767b18672a0c0abd92f7225f267478db8271c334`.
- In Progress: none.
- Blocked: none for implementation or automated verification.
- Next Action: none.

## Backlog

| ID | FRD Ref | Priority | State | Dependencies | Next Action | Updated | Actual Condition |
|---|---|---|---|---|---|---|---|
| DMN-01 | FR-DAEMON-001 | P1 | Done | WS-05 | none | 2026-10-26 | Lifecycle behavior is implemented in `modules/daemon/src/capabilities_anytype_daemon.py`; Podman-absent status is exercised by `test_status_is_safe_without_podman`; `./.venv/bin/python -m pytest modules/daemon -q` → 71 passed at `767b18672a0c0abd92f7225f267478db8271c334`. |
| DMN-02 | FR-DAEMON-002 | P1 | Done | None | none | 2026-10-26 | `cmd_auth_key` writes the secret through `agents_arwaky_config_dir()`; `modules/daemon/tests/unit_daemon.py::test_auth_key_writes_private_xdg_env_only` invokes the root `cmd_anytype` path and verifies mode `0600` plus no repo credential; `./.venv/bin/python -m pytest modules/daemon -q` → 71 passed at `767b18672a0c0abd92f7225f267478db8271c334`. |
| DMN-03 | FR-DAEMON-003 | P1 | Done | None | none | 2026-10-26 | `DaemonOrchestrator.known()` is verified for `anytype` and `omniroute` in `modules/daemon/tests/integration_daemon.py::test_full_feature_wiring`; `./.venv/bin/python -m pytest modules/daemon -q` → 71 passed at `767b18672a0c0abd92f7225f267478db8271c334`. |
| DMN-04 | FR-DAEMON-004 | P0 | Done | None | none | 2026-10-26 | Per-daemon systemd unit methods and aggregate routing are implemented in `modules/daemon/src/`; `modules/daemon/tests/integration_daemon.py` exercises install/remove/status routing; `./.venv/bin/python -m pytest modules/daemon -q` → 71 passed at `767b18672a0c0abd92f7225f267478db8271c334`. |
| FR-DAEMON-001 | FR-DAEMON-001 | P1 | Done | DMN-01 | none | 2026-10-26 | Lifecycle capability and aggregate paths are exercised by `modules/daemon/tests/integration_daemon.py`; `./.venv/bin/python -m pytest modules/daemon -q` → 71 passed at `767b18672a0c0abd92f7225f267478db8271c334`. |
| FR-DAEMON-002 | FR-DAEMON-002 | P1 | Done | DMN-02 | none | 2026-10-26 | XDG-only authorization persistence is implemented in `capabilities_anytype_daemon.py` and verified by `test_auth_key_writes_private_xdg_env_only`; `./.venv/bin/python -m pytest modules/daemon -q` → 71 passed at `767b18672a0c0abd92f7225f267478db8271c334`. |
| FR-DAEMON-003 | FR-DAEMON-003 | P1 | Done | DMN-03 | none | 2026-10-26 | Pure canonical id enumeration is implemented by `DaemonOrchestrator.known()` and verified by `test_full_feature_wiring`; `./.venv/bin/python -m pytest modules/daemon -q` → 71 passed at `767b18672a0c0abd92f7225f267478db8271c334`. |
| DMN-05 | FR-DAEMON-001, FR-DAEMON-003, FR-DAEMON-004 | P1 | Done | DMN-01 | none | 2026-10-30 | 9router is a host-native daemon sibling of OmniRoute: `modules/daemon/src/capabilities_9router_daemon.py`, `modules/daemon/deploy/9router.service`, and the `9router` routing entries in `agent_daemon_orchestrator.py`, `root_daemon_container.py`, and `surface_daemon_command.py`. Verified by `modules/daemon/tests/{contract,unit,integration,smoke,dogfood}_daemon.py` in this worktree (uncommitted). |
| FR-DAEMON-005 | FR-DAEMON-005 | P1 | In Progress | DMN-05 | none | 2026-10-30 | `aa 9router import-omniroute` migration verb: new capability module `modules/daemon/src/capabilities_9router_import_omniroute.py`, CLI verb dispatch in `surface_daemon_command.py`, unit tests with temp-DB fixtures in `unit_daemon.py::TestImportOmniroute`, SQLite UPSERT write transport (daemon stopped first, restarted after), OmniRoute strictly read-only. Live run pending against `/home/raka/.omniroute/storage.sqlite` and `/home/raka/.9router/db/data.sqlite`. |
| FR-DAEMON-004 | FR-DAEMON-004 | P0 | Done | DMN-04 | none | 2026-10-26 | Systemd user-unit operations use packaged deploy assets and the aggregate; `./.venv/bin/python -m pytest modules/daemon -q` → 71 passed at `767b18672a0c0abd92f7225f267478db8271c334`. |

## Scenario Evidence

| Scenario | Kind | Test file | Test name | Last verified |
|----------|------|-----------|-----------|---------------|
| Starting an Anytype daemon that is already running reports it is already running and exits 0 without a second launch. | Manual | — | live Podman host start-twice check | not run in this environment |
| A host without Podman reports safe status without a traceback. | Automated | `modules/daemon/tests/integration_daemon.py` | `test_status_is_safe_without_podman` | `767b186` |
| `auth-key` writes the generated key to private XDG config only; the repo tree stays clean. | Automated | `modules/daemon/tests/unit_daemon.py` | `test_auth_key_writes_private_xdg_env_only` | `767b186` |
| `auth-key` while the daemon is stopped reports the pre-condition and exits non-zero. | Manual | — | live Anytype host check | not run in this environment |
| `known()` returns every managed daemon id (anytype, omniroute, 9router) regardless of run state. | Automated | `modules/daemon/tests/integration_daemon.py` | `test_full_feature_wiring` | worktree, uncommitted |
| Enumerating daemons with neither daemon running still reports both ids. | Automated | `modules/daemon/tests/integration_daemon.py` | `test_full_feature_wiring` | `767b186` |
| `install_unit` enables a daemon user unit and a following status reports it active. | Gap | — | host-side systemd enablement not run | not run |
| `remove_unit` deletes a daemon user unit so a following status reports it absent. | Gap | — | host-side systemd removal not run | not run |
| 9router unit ops route to the 9router manager and never reach OmniRoute. | Automated | `modules/daemon/tests/integration_daemon.py` | `test_orchestrator_remove_unit_9router` | worktree, uncommitted |
| Both gateway systemd unit templates ship in `deploy/`. | Automated | `modules/daemon/tests/contract_daemon.py` | `test_default_unit_templates_exist_for_both_gateways` | worktree, uncommitted |

Kind values: Automated, Proxy, Manual, Gap.

## Blockers

None for code or automated tests.

## Dependencies

WS-05 chooses the private XDG config home for secrets. The service feature
uses the daemon aggregate for unit operations instead of duplicating them.

## Release Readiness

| Area | Status | Notes |
|------|--------|-------|
| Tests | Done | `./.venv/bin/python -m pytest modules/daemon -q` → 71 passed; Ruff clean at `767b18672a0c0abd92f7225f267478db8271c334` |
| Scenario evidence | QA | XDG authorization, enumeration, and Podman-absent status are automated; host systemd side-effect checks remain explicitly unrun |
| Docs | Done | FRD defines FR-DAEMON-001 through FR-DAEMON-004 and references this backlog |

## Deferred

- Live systemd enable/remove checks require a host where user-unit changes are explicitly authorized; the automated suite avoids host-side effects.

## Change Log

| Date | Change | By |
|------|--------|----|
| 2026-09-18 | FRD/BACKLOG pair created during WS-04 doc sweep at `5556fd5`. | @raka |
| 2026-09-26 | Rich per-operation protocol and aggregate described; 69 tests at `6df9f21`. | @raka |
| 2026-10-26 | Split the FRD into four requirements; added FRD-ref backlog rows and commit-backed evidence; 71 daemon tests pass at `767b186`. | @raka |
