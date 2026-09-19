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
- In Progress: none.
- Blocked: none.
- Next Action: UPD-04 restructure to the 2-capability business-action model with per-tool updater adapters (docs only so far, no code touched); then UPD-01 sweep (update a real pin).

## Backlog

| ID | FRD Ref | Work Item | Priority | State | Actual Condition | Owner | Dependencies | Updated |
|----|---------|-----------|:---------|-------|------------------|-------|--------------|---------|
| UPD-01 | FR-001 | Per-tool update capability (submodule bump / runner update) | P0 | QA | 12 capabilities present at `5556fd5`; import OK; `aa check` PASSED. End-to-end pin-bump sweep outstanding. Superseded in shape by UPD-04 — sweep runs after the restructure. | @raka | UPD-04 | 2026-09-19 |
| UPD-02 | FR-002 | Registry-dispatch update orchestrator | P0 | Deferred | `agent_updater_orchestrator.py` routes by id at `5556fd5`. The per-tool-id dispatch model is superseded: capabilities are now per business action (bumper, recorder), and the orchestrator's registry keys on the manifest `id` selecting that tool's own leaf updater adapter. | @raka | None | 2026-09-19 |
| UPD-03 | FR-001, FR-002 | FRD + BACKLOG pair authoring for updater | P0 | Done | FRD rewritten to the 2-capability business-action model (bumper + recorder; **per-tool** leaf adapters `utility_<tool>_updater.py`, one per manifest id; no adapter sharing with installer; no dependency on `modules/installer/` or `modules/runner/`). This BACKLOG updated to match. Verified at commit `81e3736`: re-run `aa docs check modules/updater` → exit 0 with no `[FAIL]`; re-run `python -m compileall -q modules/updater` → COMPILE_OK. | @raka | None | 2026-09-19 |
| UPD-04 | FR-001, FR-002 | Restructure src/ to the 2-capability model | P0 | Ready | Not started — docs-only decision so far, no code touched. Scope: move each tool's update mechanics out of its `capabilities_<tool>_updater.py` into a per-tool leaf adapter `utility_<tool>_updater.py` (one per manifest id — e.g. `utility_mnemosyne_updater.py`, `utility_context7_updater.py`, `utility_lint_updater.py`), sharing primitives from `modules/shared` rather than duplicating submodule-bump/chmod/atomic-swap logic; then collapse the capability layer to exactly two business-action modules `capabilities_updater_bumper.py` + `capabilities_updater_recorder.py`; add the `IToolUpdaterAdapter` contract (per-tool, not per-runner family); rewire `root_updater_container.py` and the orchestrator's `_ADAPTERS` registry to key on the manifest `id`; rename `IToolUpdater` surface to `IToolBumper` / `IToolRecorder` per FRD API Contract. No generic runner-family adapter is created and no adapter class is shared with the installer. Verify: exactly 2 `capabilities_*.py` files; one `utility_<tool>_updater.py` per manifest id; adapters import nothing from capabilities/agent/root/contract layers; no `modules.installer` or `modules.runner` import anywhere under `modules/updater/`; compileall + `aa check` green. | @raka | UPD-03 | 2026-09-19 |

## Scenario Evidence (rows)

| Scenario | Kind | Test file | Test name | Last verified |
|----------|------|-----------|-----------|---------------|
| Updating an installed tool to a newer manifest pin moves the binary/submodule and reports old→new. | Gap | — | — | `5556fd5` (no automated test yet) |
| Updating a tool whose pin is already satisfied is an idempotent success. | Gap | — | — | `5556fd5` (no automated test yet) |
| Updating an unknown tool id fails with a typed error. | Gap | — | — | `5556fd5` (no automated test yet) |
| A manifest tool with no registered per-tool updater adapter fails with a typed error naming the id. | Gap | — | — | never (model introduced by UPD-04) |
| Dry-run updating reports the planned adapter call and leaves the filesystem untouched. | Gap | — | — | never (model introduced by UPD-04) |
| After update, if the binary path changed, the launcher under XDG bin points to the new location. | Gap | — | — | never (model introduced by UPD-04) |

## Blockers

None.

## Dependencies

Root WS-07 (merge) gates the submodule-pointer workflow on main.
UPD-01 sweep depends on UPD-04 (restructure) landing first, otherwise it tests
the superseded per-tool model. UPD-04 has no cross-module dependency: the
updater owns its own per-tool adapters and shares nothing with the installer.

## Release Readiness

| Area | Status | Notes |
|------|--------|-------|
| Tests | QA | import + `aa check` green at `5556fd5`; pin-bump sweep outstanding, gated on UPD-04 |
| Type gate | Done | `aa check` at `5556fd5` |
| Docs | Done | UPD-03 pair closed; FRD + this BACKLOG consistent on the per-tool-adapter model |

## Deferred

None.

## Change Log

| Date | Change | By |
|------|--------|----|
| 2026-09-18 | FRD/BACKLOG pair created during WS-04 doc sweep at `5556fd5`. | @raka |
| 2026-09-19 | FRD rewritten to 2-capability business-action model (bumper + recorder); UPD-02 deprecated, UPD-04 opened for the src/ restructure; scenario rows added for the new failure modes. Docs only — no code touched. | @raka |
| 2026-09-19 | Corrected adapter granularity: leaf adapters are **per-tool** (`utility_<tool>_updater.py`, keyed on manifest `id`), not per-package-manager family, and NOT shared with the installer (each module owns its own leaf utilities). FRD System Overview, API Contract (`IToolUpdaterAdapter`, `_ADAPTERS` keyed on id), NFRs (added Adapter-granularity metric, replaced Adapter-sharing metric with No-cross-module-coupling), Test Scenarios, Assumptions and Glossary updated; UPD-02/UPD-03/UPD-04 rows, the no-adapter scenario row, Dependencies and Release Readiness aligned. Still docs only — no code touched. | @raka |