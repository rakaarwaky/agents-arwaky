# Feature Backlog: updater

FRD: [FRD.md](FRD.md)
Architecture: [ARCHITECTURE.md](../../ARCHITECTURE.md)
State: root § State Definitions
Health: root § State Definitions
Last Updated: 2026-09-19

## Current Condition

- Done: 12 per-tool `capabilities_<tool>_updater.py` +
  `agent_updater_orchestrator.py` + `IToolUpdater` contract at `5556fd5`;
  import OK; `aa check` PASSED at `5556fd5`.
- In Progress: UPD-03 — FRD/BACKLOG pair authoring (this file).
- Blocked: none.
- Next Action: UPD-03 — close this pair; then UPD-04 restructure to the
  2-capability business-action model (docs only so far, no code touched); then
  UPD-01 sweep (update a real pin).

## Backlog

| ID | FRD Ref | Work Item | Priority | State | Actual Condition | Owner | Dependencies | Updated |
|----|---------|-----------|:---------|-------|------------------|-------|--------------|---------|
| UPD-01 | FR-001 | Per-tool update capability (submodule bump / runner update) | P0 | QA | 12 capabilities present at `5556fd5`; import OK; `aa check` PASSED. End-to-end pin-bump sweep outstanding. Superseded in shape by UPD-04 — sweep runs after the restructure. | @raka | UPD-04 | 2026-09-19 |
| UPD-02 | FR-002 | Registry-dispatch update orchestrator | P0 | Deferred | `agent_updater_orchestrator.py` routes by id at `5556fd5`. The per-tool-id dispatch model is superseded: capabilities are now per business action (bumper, recorder), and the orchestrator's registry keys on the manifest `runner` field selecting a leaf adapter shared with installer. | @raka | None | 2026-09-19 |
| UPD-03 | FR-001, FR-002 | FRD + BACKLOG pair authoring for updater | P0 | In Progress | FRD rewritten to the 2-capability business-action model (bumper + recorder; per-runner adapters as leaf utilities shared with installer; no dependency on `modules/installer/` or `modules/runner/`). This BACKLOG updated to match. | @raka | None | 2026-09-19 |
| UPD-04 | FR-001, FR-002 | Restructure src/ to the 2-capability model | P0 | Ready | Not started — docs-only decision so far, no code touched. Scope: delete 12 `capabilities_<tool>_updater.py`; create `capabilities_updater_bumper.py` + `capabilities_updater_recorder.py`; split `utility_installer_base.py` god-file into 6 leaf adapters (`utility_cargo_adapter.py`, `utility_uv_adapter.py`, `utility_bun_adapter.py`, `utility_pnpm_adapter.py`, `utility_npm_adapter.py`, `utility_pip_venv_adapter.py`) shared with installer via `modules/shared/src/`; add `IRunnerAdapter.update` method to the existing contract; rename `IToolUpdater` surface to `IToolBumper` / `IToolRecorder` per FRD API Contract; rewire `root_updater_container.py` and the orchestrator's `_ADAPTERS` registry. Verify: exactly 2 `capabilities_*.py` files, adapters import nothing from capabilities/agent/root/contract layers, no `modules.installer` or `modules.runner` import anywhere under `modules/updater/`, compileall + `aa check` green. | @raka | UPD-03, INS-04 | 2026-09-19 |

## Scenario Evidence (rows)

| Scenario | Kind | Test file | Test name | Last verified |
|----------|------|-----------|-----------|---------------|
| Updating an installed tool to a newer manifest pin moves the binary/submodule and reports old→new. | Gap | — | — | `5556fd5` (no automated test yet) |
| Updating a tool whose pin is already satisfied is an idempotent success. | Gap | — | — | `5556fd5` (no automated test yet) |
| Updating an unknown tool id fails with a typed error. | Gap | — | — | `5556fd5` (no automated test yet) |
| A tool whose manifest runner has no registered adapter fails with a typed error naming the runner. | Gap | — | — | never (model introduced by UPD-04) |
| Dry-run updating reports the planned adapter call and leaves the filesystem untouched. | Gap | — | — | never (model introduced by UPD-04) |
| After update, if the binary path changed, the launcher under XDG bin points to the new location. | Gap | — | — | never (model introduced by UPD-04) |

## Blockers

None.

## Dependencies

Root WS-07 (merge) gates the submodule-pointer workflow on main.
UPD-01 sweep depends on UPD-04 (restructure) landing first, otherwise it tests
the superseded per-tool model. UPD-04 depends on INS-04 because the runner
adapters are shared between the two modules.

## Release Readiness

| Area | Status | Notes |
|------|--------|-------|
| Tests | QA | import + `aa check` green at `5556fd5`; pin-bump sweep outstanding, gated on UPD-04 |
| Type gate | Done | `aa check` at `5556fd5` |
| Docs | In Progress | UPD-03 (this pair) |

## Deferred

None.

## Change Log

| Date | Change | By |
|------|--------|----|
| 2026-09-18 | FRD/BACKLOG pair created during WS-04 doc sweep at `5556fd5`. | @raka |
| 2026-09-19 | FRD rewritten to 2-capability business-action model (bumper + recorder, per-runner leaf adapters shared with installer); UPD-02 deprecated, UPD-04 opened for the src/ restructure; scenario rows added for the new failure modes. Docs only — no code touched. | @raka |