# ROADMAP — agents-arwaky

State / Health: vocabulary below. Last Updated: 2026-10-26

## Current Condition

- Done: legacy `tools/` migration and per-feature AES architecture are in
  place; identified lifecycle, config, manifest, harness, and backup
  regressions are covered by feature suites and documented in per-feature
  backlogs.
- In Progress: none at workspace level.
- Blocked: none.
- Next: none.

## State Definitions

| State | Meaning |
|-------|---------|
| Idea | Not examined; no spec. |
| Refinement | Being specced. |
| Ready | Specified; not started. |
| In Progress | Active now. |
| Blocked | Name the blocker in Actual Condition. |
| In Review | PR open. |
| QA | Awaiting verification pass. |
| Done | Command + commit evidence. |
| Released | Shipped. |
| Deferred | Out of scope; reason in Actual Condition. |

| Health | Meaning |
|--------|---------|
| On Track | No threat to the gate. |
| At Risk | Gaps may miss the gate. |
| Blocked | Cannot proceed. |
| Ready for QA | Open rows clear; sweep left. |
| Ready for Release | Evidence recorded. |
| Released | Shipped. |

### Status Policy

- Verified, not self-reported: re-run the cited command; name a commit hash
  (never "today"). A `Done` / `Released` row owes a code-span command plus
  that hash in Actual Condition.
- Same PR updates every backlog row the change invalidates.
- Prefixes: workspace `WS-` · feature `<SCOPE>-` (feature rows stay in that
  feature's BACKLOG; this file carries cross-cutting rows only).
- `Last Updated` / `Updated` move only with a change in the file.

## Feature Roll-up

### Cross-Cutting Backlog

Cross-cutting `WS-` rows only. Feature rows live in each feature's BACKLOG.
One table: every feature. Feature detail stays in each feature's BACKLOG.

| ID | Feature | Priority | State | Dependencies | Next Action | Updated | Actual Condition |
|---|---|---|---|---|---|---|---|
| modules/tools | Tool lifecycle (install / update / uninstall / run / resolve) | P0 | Done | TOL-06 | none | 2026-10-26 | `./.venv/bin/python -m pytest modules/tools -q` → 84 passed at `767b18672a0c0abd92f7225f267478db8271c334` |
| modules/mcp | MCP manifest → client config / list / probe | P0 | Done | MCP-05 | none | 2026-10-26 | `./.venv/bin/python -m pytest modules/mcp -q` → 26 passed at `767b18672a0c0abd92f7225f267478db8271c334` |
| modules/config | Comment-safe config load / save / merge / env | P1 | Done | CFG-04 | none | 2026-10-26 | `./.venv/bin/python -m pytest modules/config -q` → 77 passed at `767b18672a0c0abd92f7225f267478db8271c334` |
| modules/daemon | Daemon lifecycle + Anytype auth / units | P1 | Done | DMN-04 | none | 2026-10-26 | `./.venv/bin/python -m pytest modules/daemon -q` → 71 passed at `767b18672a0c0abd92f7225f267478db8271c334` |
| modules/doctor | Host + tool readiness diagnosis | P1 | Done | DOC-03 | none | 2026-10-26 | `./.venv/bin/python -m pytest modules/doctor -q` → 29 passed at `767b18672a0c0abd92f7225f267478db8271c334` |
| modules/harness | Connect / disconnect / skill provisioning | P1 | Done | HRS-07 | none | 2026-10-26 | `./.venv/bin/python -m pytest modules/harness -q` → 45 passed at `767b18672a0c0abd92f7225f267478db8271c334` |
| modules/service | systemd unit drive / status / logs | P1 | Done | SVC-04 | none | 2026-10-26 | `./.venv/bin/python -m pytest modules/service -q` → 31 passed at `767b18672a0c0abd92f7225f267478db8271c334` |
| modules/skills | Skill pack discovery and authoring | P1 | Done | SKL-11 | none | 2026-10-26 | `./.venv/bin/python -m pytest modules/skills -q` → 168 passed at `767b18672a0c0abd92f7225f267478db8271c334` |
| modules/backup | Local archive / restore / list / status | P2 | Done | BKP-06 | none | 2026-10-26 | `./.venv/bin/python -m pytest modules/backup -q` → 35 passed at `767b18672a0c0abd92f7225f267478db8271c334` |
| modules/shared | Kernel (XDG, venv, launcher, engines) | P0 | Done | SHARED-02 | none | 2026-10-26 | `./.venv/bin/python -m pytest modules/shared -q` → 116 passed at `767b18672a0c0abd92f7225f267478db8271c334` |

### Branches in Flight

| Branch | Backlog IDs | State |
|--------|-------------|-------|
| `arena/640ff78a-agents-arwaky` | WS-05, WS-06, feature verification and evidence updates | In Progress |

| ID | FRD Ref | Work Item | Priority | State | Actual Condition | Owner | Dependencies | Updated |
|----|---------|-----------|----------|-------|-------------------|-------|--------------|---------|
| WS-01 | — | Migrate legacy `tools/` into AES 7-layer `modules/` (P0-P4) | P0 | Done | Gate: `python3 -m compileall modules/` → clean at `b9c8c62`; excludes live `.env` and legacy `tools/tests/`. | @raka | None | 2026-09-23 |
| WS-02 | — | Runner split per-tool (registry dispatch + RunnerBase + per-tool capabilities) | P0 | Done | Gate: `lint-arwaky scan modules` → 0 violations at `b9c8c62`; runner lives under `modules/tools`. | @raka | WS-01 | 2026-09-23 |
| WS-03 | — | Consolidate surface commands into per-feature packages | P0 | Done | Gate: `find modules -name 'surface_*'` → all under `modules/<feature>/src/` at `b9c8c62`; no `modules/cli`. | @raka | WS-01 | 2026-09-23 |
| WS-04 | — | FRD + BACKLOG pair for each module | P0 | Done | Pairs written + strict-only sweep; 0 findings at `fffcd17` (working tree). | @raka | WS-01 | 2026-09-23 |
| WS-05 | — | Select the private XDG config home for live Anytype credentials | P1 | Done | `./.venv/bin/python -m pytest modules/daemon/tests/unit_daemon.py::test_auth_key_writes_private_xdg_env_only -q` → 1 passed; `./.venv/bin/python -m pytest modules/daemon -q` → 71 passed at `767b18672a0c0abd92f7225f267478db8271c334`; writes only under `agents_arwaky_config_dir()/anytype.env`. | @raka | None | 2026-10-26 |
| WS-06 | — | Audit/migrate the legacy tools test suite if source files are tracked | P1 | Done | `git ls-tree -r --name-only HEAD -- tests tools/tests` → no tracked paths to migrate; feature tests already live under `modules/<feature>/tests/`; `./.venv/bin/python -m pytest modules -q` → 684 passed at `767b18672a0c0abd92f7225f267478db8271c334`. | @raka | WS-01 | 2026-10-26 |
| WS-07 | — | Merge `refactor/aes-tools` into main, deleting legacy `tools/` there | P0 | Done | Gate: `git log --oneline -1` → merge on main at `b9c8c62`; legacy `tools/` gone; AES + ruff green. | @raka | WS-04, WS-08 | 2026-09-23 |
| WS-08 | — | Fix CI entry-point drift (`modules.cli` → `root_cli_entry`) | P0 | Done | Gate: `grep root_cli_entry .github/workflows/ci.yml` → 2 hits at `b9c8c62`; CI green. | @raka | WS-03 | 2026-09-23 |

## Risk Register

- Risk: HRS-02 has no task description or FR/scenario mapping and remains
  Deferred; mitigation: keep it out of the active roll-up until the owner
  supplies an acceptance scope.
- Risk: live systemd/Podman operations are not run by the automated suite
  because they alter host services; mitigation: keep these host-side checks
  explicitly identified in the relevant feature backlogs.
